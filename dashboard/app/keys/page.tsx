/**
 * Cost Melt Dashboard - API Key Management Page
 *
 * Create, list, rotate, and revoke API keys. Requires the dashboard's
 * COSTMELT_ADMIN_API_KEY to be configured on the server (see
 * lib/backendProxy.ts) - a 503 from the backend means it isn't set up yet.
 */

'use client';

import { useEffect, useState } from 'react';
import { listKeys, createKey, revokeKey, rotateKey } from '../../lib/api';
import type { APIKeyInfo } from '../../lib/types';
import Card, { CardHeader, CardTitle, CardContent } from '../../components/Card';
import Loader from '../../components/Loader';
import ErrorState from '../../components/ErrorState';
import DataTable, { TableRow, TableCell } from '../../components/DataTable';

function formatDate(value: string | null): string {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

function RoleBadge({ role }: { role: string }) {
  const colors: Record<string, string> = {
    admin: 'bg-red-100 text-red-700',
    write: 'bg-amber-100 text-amber-700',
    read: 'bg-blue-100 text-blue-700',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[role] || 'bg-gray-100 text-gray-700'}`}>
      {role}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const active = status === 'active';
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
      {status}
    </span>
  );
}

/** Shown once after a create/rotate call - the API never returns the plaintext key again. */
function RevealedKeyBanner({ apiKey, onDismiss }: { apiKey: string; onDismiss: () => void }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(apiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be denied by the browser; the key is still selectable text.
    }
  }

  return (
    <Card className="border-amber-300 bg-amber-50">
      <CardContent className="p-6 space-y-3">
        <p className="font-semibold text-amber-900">
          Copy this key now — it will not be shown again.
        </p>
        <div className="flex items-center gap-2">
          <code className="flex-1 px-3 py-2 bg-white border border-amber-300 rounded-lg text-sm overflow-x-auto whitespace-nowrap">
            {apiKey}
          </code>
          <button
            onClick={copy}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors text-sm shrink-0"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        <button onClick={onDismiss} className="text-sm text-amber-800 underline">
          Done, dismiss this
        </button>
      </CardContent>
    </Card>
  );
}

export default function KeysPage() {
  const [keys, setKeys] = useState<APIKeyInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revealedKey, setRevealedKey] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const [projectId, setProjectId] = useState('');
  const [role, setRole] = useState<'admin' | 'write' | 'read'>('write');
  const [creating, setCreating] = useState(false);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const data = await listKeys();
      setKeys(data.keys);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!projectId.trim()) return;
    setCreating(true);
    setActionError(null);
    try {
      const result = await createKey({ project_id: projectId.trim(), role });
      setRevealedKey(result.api_key);
      setProjectId('');
      setRole('write');
      await refresh();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to create API key');
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(id: string) {
    if (!confirm('Revoke this key? Anything using it will stop working immediately.')) return;
    setBusyId(id);
    setActionError(null);
    try {
      await revokeKey(id);
      await refresh();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to revoke API key');
    } finally {
      setBusyId(null);
    }
  }

  async function handleRotate(id: string) {
    if (!confirm('Rotate this key? The old key stops working immediately and a new one is issued.')) return;
    setBusyId(id);
    setActionError(null);
    try {
      const result = await rotateKey(id);
      setRevealedKey(result.api_key);
      await refresh();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Failed to rotate API key');
    } finally {
      setBusyId(null);
    }
  }

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
        <ErrorState message={error} onRetry={refresh} />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">API Key Management</h1>
        <p className="text-gray-600">Create, rotate, and revoke keys used to authenticate against the Cost Melt gateway.</p>
      </div>

      {revealedKey && (
        <RevealedKeyBanner apiKey={revealedKey} onDismiss={() => setRevealedKey(null)} />
      )}

      {actionError && (
        <div className="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {actionError}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Create a New Key</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-1">Project ID</label>
              <input
                type="text"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                placeholder="e.g. my-app"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as 'admin' | 'write' | 'read')}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="read">read</option>
                <option value="write">write</option>
                <option value="admin">admin</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={creating}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {creating ? 'Creating…' : 'Create Key'}
            </button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Existing Keys ({keys.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable headers={['Prefix', 'Project', 'Role', 'Status', 'Created', 'Last Used', 'Actions']}>
            {keys.map((key) => (
              <TableRow key={key.id}>
                <TableCell className="font-mono">{key.prefix}…</TableCell>
                <TableCell>{key.project_id}</TableCell>
                <TableCell><RoleBadge role={key.role} /></TableCell>
                <TableCell><StatusBadge status={key.status} /></TableCell>
                <TableCell>{formatDate(key.created_at)}</TableCell>
                <TableCell>{formatDate(key.last_used_at)}</TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRotate(key.id)}
                      disabled={busyId === key.id || key.status !== 'active'}
                      className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Rotate
                    </button>
                    <button
                      onClick={() => handleRevoke(key.id)}
                      disabled={busyId === key.id || key.status !== 'active'}
                      className="text-sm text-red-600 hover:text-red-800 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Revoke
                    </button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {keys.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-gray-500">
                  No API keys yet. Create one above to get started.
                </TableCell>
              </TableRow>
            )}
          </DataTable>
        </CardContent>
      </Card>
    </div>
  );
}
