/**
 * Cost Melt Dashboard - Daily Page
 * 
 * Daily timeseries usage metrics.
 */

'use client';

import { useEffect, useState } from 'react';
import { getDaily } from '../../lib/api';
import type { DailyResponse } from '../../lib/types';
import ChartCard from '../../components/ChartCard';
import Loader from '../../components/Loader';
import ErrorState from '../../components/ErrorState';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { formatCurrency, formatNumber } from '../../lib/utils';

export default function DailyPage() {
  const [daily, setDaily] = useState<DailyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const data = await getDaily(days);
        setDaily(data);
      } catch (err) {
        console.error('Error fetching daily data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load daily data');
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

  const daysData = daily?.days || [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Daily Usage</h1>
          <p className="text-gray-600">Timeseries metrics over time</p>
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

      {/* Full Width Chart */}
      <ChartCard title="Daily Usage Metrics">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={daysData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="requests"
              stroke="#2563eb"
              strokeWidth={2}
              name="Requests"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="tokens_in"
              stroke="#10b981"
              strokeWidth={2}
              name="Tokens In"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="tokens_out"
              stroke="#8b5cf6"
              strokeWidth={2}
              name="Tokens Out"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="actual_cost"
              stroke="#f59e0b"
              strokeWidth={2}
              name="Actual Cost"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="baseline_cost"
              stroke="#ef4444"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="Baseline Cost"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="savings"
              stroke="#06b6d4"
              strokeWidth={2}
              name="Savings"
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-sm font-medium text-gray-600 mb-1">Total Requests</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatNumber(daysData.reduce((sum, d) => sum + d.requests, 0))}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-sm font-medium text-gray-600 mb-1">Total Tokens In</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatNumber(daysData.reduce((sum, d) => sum + d.tokens_in, 0))}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-sm font-medium text-gray-600 mb-1">Total Actual Cost</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatCurrency(daysData.reduce((sum, d) => sum + d.actual_cost, 0))}
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-sm font-medium text-gray-600 mb-1">Total Savings</div>
          <div className="text-2xl font-bold text-green-600">
            {formatCurrency(daysData.reduce((sum, d) => sum + d.savings, 0))}
          </div>
        </div>
      </div>
    </div>
  );
}

