/**
 * Cost Melt Dashboard - Routing Page
 * 
 * Routing complexity and model distribution.
 */

'use client';

import { useEffect, useState } from 'react';
import { getRouting } from '../../lib/api';
import type { RoutingDistribution } from '../../lib/types';
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
import { formatNumber } from '../../lib/utils';

const COLORS = ['#2563eb', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];

export default function RoutingPage() {
  const [routing, setRouting] = useState<RoutingDistribution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const data = await getRouting();
        setRouting(data);
      } catch (err) {
        console.error('Error fetching routing data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load routing data');
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

  const complexityData = routing ? [
    { name: 'Simple (0)', value: routing.complexity_distribution['0'] },
    { name: 'Medium (1)', value: routing.complexity_distribution['1'] },
    { name: 'Complex (2)', value: routing.complexity_distribution['2'] }
  ] : [];

  const modelData = routing ? Object.entries(routing.model_distribution).map(([model, count]) => ({
    name: model,
    value: count
  })) : [];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Routing Breakdown</h1>
        <p className="text-gray-600">Complexity distribution and model routing</p>
      </div>

      {/* Complexity Distribution Table */}
      <Card>
        <CardHeader>
          <CardTitle>Complexity Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable headers={['Complexity Level', 'Count', 'Description']}>
            <TableRow>
              <TableCell className="font-medium">Simple (0)</TableCell>
              <TableCell>{formatNumber(routing?.complexity_distribution['0'] || 0)}</TableCell>
              <TableCell className="text-gray-600">Basic Q&A, simple tasks</TableCell>
            </TableRow>
            <TableRow>
              <TableCell className="font-medium">Medium (1)</TableCell>
              <TableCell>{formatNumber(routing?.complexity_distribution['1'] || 0)}</TableCell>
              <TableCell className="text-gray-600">Multi-step reasoning, moderate context</TableCell>
            </TableRow>
            <TableRow>
              <TableCell className="font-medium">Complex (2)</TableCell>
              <TableCell>{formatNumber(routing?.complexity_distribution['2'] || 0)}</TableCell>
              <TableCell className="text-gray-600">Deep reasoning, extensive context</TableCell>
            </TableRow>
          </DataTable>
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Complexity Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={complexityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#2563eb" name="Requests" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Model Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={modelData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {modelData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
