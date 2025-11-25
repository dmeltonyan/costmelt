/**
 * Cost Melt Dashboard - Home Page
 * 
 * Main dashboard with overview metrics and charts.
 */

'use client';

import { useEffect, useState } from 'react';
import { getStats, getUsage, getRouting, getDaily, getSavings } from '../lib/api';
import type { Stats, UsageResponse, RoutingDistribution, DailyResponse, SavingsResponse } from '../lib/types';
import Card, { CardHeader, CardTitle, CardContent } from '../components/Card';
import ChartCard from '../components/ChartCard';
import Loader from '../components/Loader';
import ErrorState from '../components/ErrorState';
import Metric from '../components/Metric';
import {
  LineChart,
  Line,
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
import { formatCurrency, formatNumber, formatPercentage } from '../lib/utils';

const COLORS = ['#2563eb', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [routing, setRouting] = useState<RoutingDistribution | null>(null);
  const [daily, setDaily] = useState<DailyResponse | null>(null);
  const [savings, setSavings] = useState<SavingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [statsData, usageData, routingData, dailyData, savingsData] = await Promise.all([
          getStats(),
          getUsage(),
          getRouting(),
          getDaily(30),
          getSavings(30)
        ]);

        setStats(statsData);
        setUsage(usageData);
        setRouting(routingData);
        setDaily(dailyData);
        setSavings(savingsData);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
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

  // Prepare chart data
  const savingsChartData = savings?.savings_over_time || [];
  const modelPieData = usage?.models.map(m => ({
    name: m.model,
    value: m.count
  })) || [];
  const complexityBarData = routing ? [
    { name: 'Simple', value: routing.complexity_distribution['0'] },
    { name: 'Medium', value: routing.complexity_distribution['1'] },
    { name: 'Complex', value: routing.complexity_distribution['2'] }
  ] : [];
  const dailyUsageData = daily?.days || [];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard Overview</h1>
        <p className="text-gray-600">Cost optimization metrics and analytics</p>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Total Requests"
              value={formatNumber(stats?.total_requests || 0)}
              subtitle="All time requests"
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Total Tokens In"
              value={formatNumber(stats?.total_tokens_in || 0)}
              subtitle="Input tokens processed"
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Cost Saved"
              value={formatCurrency(stats?.total_savings || 0)}
              subtitle={`${formatPercentage(stats?.savings_pct || 0)} savings`}
              trend={{ value: stats?.savings_pct || 0, isPositive: true }}
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Cache Hit Rate"
              value={formatPercentage(stats?.cache_hit_rate || 0)}
              subtitle="Cache performance"
            />
          </CardContent>
        </Card>
      </div>

      {/* Row 2: Savings Chart + Model Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Savings Over Time">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={savingsChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Legend />
              <Line
                type="monotone"
                dataKey="saved"
                stroke="#10b981"
                strokeWidth={2}
                name="Savings"
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Model Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={modelPieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {modelPieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 3: Routing Complexity + Daily Usage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="Routing Complexity Distribution">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={complexityBarData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#2563eb" name="Requests" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Daily Usage Preview">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyUsageData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="requests"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="Requests"
              />
              <Line
                type="monotone"
                dataKey="actual_cost"
                stroke="#f59e0b"
                strokeWidth={2}
                name="Cost"
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
