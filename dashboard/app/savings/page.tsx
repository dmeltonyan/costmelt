/**
 * Cost Melt Dashboard - Savings Page
 * 
 * Historical savings analysis.
 */

'use client';

import { useEffect, useState } from 'react';
import { getSavings } from '../../lib/api';
import type { SavingsResponse } from '../../lib/types';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/Card';
import ChartCard from '../../components/ChartCard';
import Loader from '../../components/Loader';
import ErrorState from '../../components/ErrorState';
import DataTable, { TableRow, TableCell } from '../../components/DataTable';
import Metric from '../../components/Metric';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { formatCurrency } from '../../lib/utils';

export default function SavingsPage() {
  const [savings, setSavings] = useState<SavingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const data = await getSavings(days);
        setSavings(data);
      } catch (err) {
        console.error('Error fetching savings data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load savings data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [days]);

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

  const savingsData = savings?.savings_over_time || [];
  const totalSavings = savingsData.reduce((sum, d) => sum + d.saved, 0);
  const avgDailySavings = totalSavings / (savingsData.length || 1);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Savings Analysis</h1>
          <p className="text-gray-600">Historical cost savings over time</p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Summary Totals */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Total Savings"
              value={formatCurrency(totalSavings)}
              subtitle="Over selected period"
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Average Daily Savings"
              value={formatCurrency(avgDailySavings)}
              subtitle="Per day average"
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Days Tracked"
              value={savingsData.length}
              subtitle="Data points"
            />
          </CardContent>
        </Card>
      </div>

      {/* Historical Savings Chart */}
      <ChartCard title="Historical Savings">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={savingsData}>
            <defs>
              <linearGradient id="colorSavings" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value: number) => formatCurrency(value)} />
            <Legend />
            <Area
              type="monotone"
              dataKey="saved"
              stroke="#10b981"
              fillOpacity={1}
              fill="url(#colorSavings)"
              name="Savings"
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Savings Table */}
      <Card>
        <CardHeader>
          <CardTitle>Daily Savings Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable headers={['Date', 'Savings']}>
            {savingsData.map((entry, index) => (
              <TableRow key={index}>
                <TableCell className="font-medium">{entry.date}</TableCell>
                <TableCell className="text-green-600 font-semibold">
                  {formatCurrency(entry.saved)}
                </TableCell>
              </TableRow>
            ))}
            {savingsData.length === 0 && (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-gray-500">
                  No savings data available
                </TableCell>
              </TableRow>
            )}
          </DataTable>
        </CardContent>
      </Card>
    </div>
  );
}

