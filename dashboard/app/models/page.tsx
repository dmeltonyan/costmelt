/**
 * Cost Melt Dashboard - Models Page
 * 
 * Model usage and cost comparison.
 */

'use client';

import { useEffect, useState } from 'react';
import { getModels } from '../../lib/api';
import type { ModelsResponse } from '../../lib/types';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/Card';
import Loader from '../../components/Loader';
import ErrorState from '../../components/ErrorState';
import DataTable, { TableRow, TableCell } from '../../components/DataTable';
import { formatCurrency, formatNumber, formatPercentage } from '../../lib/utils';

export default function ModelsPage() {
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const data = await getModels();
        setModels(data);
      } catch (err) {
        console.error('Error fetching models data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load models data');
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

  const entries = models?.entries || [];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Model Comparison</h1>
        <p className="text-gray-600">Cost analysis and savings by model</p>
      </div>

      {/* Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle>Model Cost Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            headers={['Model', 'Requests', 'Actual Cost', 'Baseline Cost', 'Savings %']}
          >
            {entries.map((entry, index) => (
              <TableRow key={index}>
                <TableCell className="font-medium">{entry.model}</TableCell>
                <TableCell>{formatNumber(entry.requests)}</TableCell>
                <TableCell>{formatCurrency(entry.actual_cost)}</TableCell>
                <TableCell>{formatCurrency(entry.baseline_cost)}</TableCell>
                <TableCell className={entry.savings_pct > 0 ? 'text-green-600 font-semibold' : ''}>
                  {formatPercentage(entry.savings_pct)}
                </TableCell>
              </TableRow>
            ))}
            {entries.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-gray-500">
                  No model data available
                </TableCell>
              </TableRow>
            )}
          </DataTable>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Total Models</div>
            <div className="text-2xl font-bold text-gray-900">{entries.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Total Requests</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatNumber(entries.reduce((sum, e) => sum + e.requests, 0))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="text-sm font-medium text-gray-600 mb-1">Total Actual Cost</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(entries.reduce((sum, e) => sum + e.actual_cost, 0))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

