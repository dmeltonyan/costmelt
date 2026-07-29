/**
 * Cost Melt Dashboard - Billing Page
 *
 * What you'd actually be billed: total spend, spend trend over time, and a
 * per-model cost breakdown. Distinct from Usage (token counts) and Savings
 * (savings-over-time) - this page answers "what is this costing me."
 */

'use client';

import { useEffect, useState } from 'react';
import { getStats, getDaily, getModels } from '../../lib/api';
import type { Stats, DailyResponse, ModelsResponse } from '../../lib/types';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/Card';
import ChartCard from '../../components/ChartCard';
import Loader from '../../components/Loader';
import ErrorState from '../../components/ErrorState';
import DataTable, { TableRow, TableCell } from '../../components/DataTable';
import Metric from '../../components/Metric';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { formatCurrency, formatPercentage } from '../../lib/utils';

export default function BillingPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [daily, setDaily] = useState<DailyResponse | null>(null);
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const [statsData, dailyData, modelsData] = await Promise.all([
          getStats(),
          getDaily(days),
          getModels(),
        ]);
        setStats(statsData);
        setDaily(dailyData);
        setModels(modelsData);
      } catch (err) {
        console.error('Error fetching billing data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load billing data');
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

  const dailyData = daily?.days || [];
  const modelEntries = [...(models?.entries || [])].sort((a, b) => b.actual_cost - a.actual_cost);
  const hasData = (stats?.total_requests || 0) > 0;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Billing & Usage</h1>
          <p className="text-gray-600">What Cost Melt&apos;s optimization is actually costing you, and what it would have cost without it</p>
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

      {!hasData && (
        <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
          No requests recorded yet. Route some traffic through the gateway and this page will fill in automatically.
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Current Spend"
              value={formatCurrency(stats?.total_actual_cost || 0)}
              subtitle="Total actual cost, all time"
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Without Optimization"
              value={formatCurrency(stats?.total_baseline_cost || 0)}
              subtitle="Baseline cost estimate"
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="You Saved"
              value={formatCurrency(stats?.total_savings || 0)}
              subtitle={`${formatPercentage(stats?.savings_pct || 0)} of baseline`}
              trend={{ value: stats?.savings_pct || 0, isPositive: true }}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Total Requests"
              value={stats?.total_requests || 0}
              subtitle="All time"
            />
          </CardContent>
        </Card>
      </div>

      {/* Spend over time */}
      <ChartCard title="Spend Over Time">
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={dailyData}>
            <defs>
              <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.7} />
                <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorBaseline" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value: number) => formatCurrency(value)} />
            <Legend />
            <Area
              type="monotone"
              dataKey="baseline_cost"
              stroke="#f59e0b"
              fill="url(#colorBaseline)"
              name="Without optimization"
            />
            <Area
              type="monotone"
              dataKey="actual_cost"
              stroke="#2563eb"
              fill="url(#colorActual)"
              name="Actual spend"
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Per-model cost breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Spend by Model</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable headers={['Model', 'Requests', 'Actual Cost', 'Baseline Cost', 'Savings']}>
            {modelEntries.map((entry, index) => (
              <TableRow key={index}>
                <TableCell className="font-medium">{entry.model}</TableCell>
                <TableCell>{entry.requests}</TableCell>
                <TableCell>{formatCurrency(entry.actual_cost)}</TableCell>
                <TableCell>{formatCurrency(entry.baseline_cost)}</TableCell>
                <TableCell className={entry.savings_pct > 0 ? 'text-green-600' : ''}>
                  {formatPercentage(entry.savings_pct)}
                </TableCell>
              </TableRow>
            ))}
            {modelEntries.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-gray-500">
                  No spend data available for this period
                </TableCell>
              </TableRow>
            )}
          </DataTable>
        </CardContent>
      </Card>
    </div>
  );
}
