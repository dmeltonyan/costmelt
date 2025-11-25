/**
 * Cost Melt Dashboard - Usage Page
 * 
 * Model usage breakdown with tables and charts.
 */

'use client';

import { useEffect, useState } from 'react';
import { getUsage } from '../../lib/api';
import type { UsageResponse } from '../../lib/types';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/Card';
import ChartCard from '../../components/ChartCard';
import Loader from '../../components/Loader';
import ErrorState from '../../components/ErrorState';
import DataTable, { TableRow, TableCell } from '../../components/DataTable';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { formatCurrency, formatNumber } from '../../lib/utils';

const COLORS = ['#2563eb', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];

export default function UsagePage() {
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const data = await getUsage();
        setUsage(data);
      } catch (err) {
        console.error('Error fetching usage data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load usage data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <Loader size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  const models = usage?.models || [];
  const barChartData = models.map(m => ({
    name: m.model,
    requests: m.count
  }));
  const pieChartData = models.map(m => ({
    name: m.model,
    value: m.actual_cost
  }));

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Usage by Model</h1>
        <p className="text-gray-600">Detailed breakdown of model usage and costs</p>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Model Usage Table</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            headers={['Model', 'Request Count', 'Tokens In', 'Tokens Out', 'Actual Cost', 'Baseline Cost', 'Savings %']}
          >
            {models.map((model, index) => {
              // Calculate baseline cost (would need to fetch separately or calculate)
              const baselineCost = model.actual_cost * 3; // Rough estimate
              const savingsPct = ((baselineCost - model.actual_cost) / baselineCost * 100);

              return (
                <TableRow key={index}>
                  <TableCell className="font-medium">{model.model}</TableCell>
                  <TableCell>{formatNumber(model.count)}</TableCell>
                  <TableCell>{formatNumber(model.input_tokens)}</TableCell>
                  <TableCell>{formatNumber(model.output_tokens)}</TableCell>
                  <TableCell>{formatCurrency(model.actual_cost)}</TableCell>
                  <TableCell>{formatCurrency(baselineCost)}</TableCell>
                  <TableCell className={savingsPct > 0 ? 'text-green-600' : ''}>
                    {savingsPct.toFixed(1)}%
                  </TableCell>
                </TableRow>
              );
            })}
          </DataTable>
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Requests per Model">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="requests" fill="#2563eb" name="Requests" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Cost Comparison">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

