/**
 * Cost Melt Dashboard - Cache Page
 * 
 * Cache performance metrics and recent hits.
 */

'use client';

import { useEffect, useState } from 'react';
import { getCache } from '../../lib/api';
import type { CacheMetrics } from '../../lib/types';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/Card';
import ChartCard from '../../components/ChartCard';
import Loader from '../../components/Loader';
import ErrorState from '../../components/ErrorState';
import DataTable, { TableRow, TableCell } from '../../components/DataTable';
import Metric from '../../components/Metric';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { formatPercentage, formatNumber } from '../../lib/utils';

export default function CachePage() {
  const [cache, setCache] = useState<CacheMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const data = await getCache();
        setCache(data);
      } catch (err) {
        console.error('Error fetching cache data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load cache data');
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

  const hitMissData = [
    { name: 'Cache Hits', value: cache?.cache_hits || 0 },
    { name: 'Cache Misses', value: cache?.cache_misses || 0 }
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Cache Performance</h1>
        <p className="text-gray-600">Semantic cache metrics and recent hits</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Cache Hits"
              value={formatNumber(cache?.cache_hits || 0)}
              subtitle="Total cache hits"
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Cache Misses"
              value={formatNumber(cache?.cache_misses || 0)}
              subtitle="Total cache misses"
            />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <Metric
              label="Hit Rate"
              value={formatPercentage(cache?.hit_rate || 0)}
              subtitle="Cache performance"
            />
          </CardContent>
        </Card>
      </div>

      {/* Chart */}
      <ChartCard title="Cache Hits vs Misses">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={hitMissData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="value" fill="#10b981" name="Count" />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Recent Hits Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Cache Hits</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable headers={['Prompt', 'Response Length']}>
            {cache?.recent_hits.map((hit, index) => (
              <TableRow key={index}>
                <TableCell>{hit.prompt}</TableCell>
                <TableCell>{formatNumber(hit.response_length)} chars</TableCell>
              </TableRow>
            )) || (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-gray-500">
                  No recent cache hits
                </TableCell>
              </TableRow>
            )}
          </DataTable>
        </CardContent>
      </Card>
    </div>
  );
}
