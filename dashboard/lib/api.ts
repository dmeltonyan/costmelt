/**
 * Cost Melt Dashboard - API Client
 *
 * Fetches data through this Next.js app's own /api/* route handlers
 * (see the route.ts files under app/api/), which run server-side and attach the backend
 * API key from COSTMELT_DASHBOARD_API_KEY. The backend's /dashboard/*
 * endpoints require authentication, and that key must never reach the
 * browser — calling the backend directly from here (a client-evaluated
 * module) would mean either shipping the key in a NEXT_PUBLIC_ var or
 * getting 401s. Going through our own /api/* proxy avoids both.
 */

import {
  Stats,
  UsageResponse,
  CacheMetrics,
  RoutingDistribution,
  DailyResponse,
  ModelsResponse,
  SavingsResponse,
  ListAPIKeysResponse,
  CreateAPIKeyRequest,
  CreateAPIKeyResponse,
  RotateAPIKeyResponse
} from './types';

/**
 * Fetch data from this app's own API proxy routes
 */
async function fetchAPI<T>(endpoint: string, init?: RequestInit): Promise<T> {
  const response = await fetch(endpoint, {
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
    },
    ...init,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error || body?.detail || `API error: ${response.status} ${response.statusText}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

/**
 * Get top-level summary statistics
 */
export async function getStats(): Promise<Stats> {
  return fetchAPI<Stats>('/api/stats');
}

/**
 * Get usage breakdown by model
 */
export async function getUsage(): Promise<UsageResponse> {
  return fetchAPI<UsageResponse>('/api/usage');
}

/**
 * Get cache performance metrics
 */
export async function getCache(): Promise<CacheMetrics> {
  return fetchAPI<CacheMetrics>('/api/cache');
}

/**
 * Get routing complexity and model distribution
 */
export async function getRouting(): Promise<RoutingDistribution> {
  return fetchAPI<RoutingDistribution>('/api/routing');
}

/**
 * Get daily timeseries metrics
 */
export async function getDaily(days: number = 30): Promise<DailyResponse> {
  return fetchAPI<DailyResponse>(`/api/daily?days=${days}`);
}

/**
 * Get model usage and cost comparison
 */
export async function getModels(): Promise<ModelsResponse> {
  return fetchAPI<ModelsResponse>('/api/models');
}

/**
 * Get savings over time
 */
export async function getSavings(days: number = 30): Promise<SavingsResponse> {
  return fetchAPI<SavingsResponse>(`/api/savings?days=${days}`);
}

/**
 * List all API keys (admin only - see backend/security/rbac.py)
 */
export async function listKeys(): Promise<ListAPIKeysResponse> {
  return fetchAPI<ListAPIKeysResponse>('/api/keys');
}

/**
 * Create a new API key. The plaintext key is only ever returned here, once.
 */
export async function createKey(body: CreateAPIKeyRequest): Promise<CreateAPIKeyResponse> {
  return fetchAPI<CreateAPIKeyResponse>('/api/keys', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

/**
 * Revoke an API key. Revoked keys can no longer authenticate.
 */
export async function revokeKey(id: string): Promise<void> {
  return fetchAPI<void>(`/api/keys/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

/**
 * Rotate an API key: revokes the old one and returns a freshly minted replacement.
 */
export async function rotateKey(id: string): Promise<RotateAPIKeyResponse> {
  return fetchAPI<RotateAPIKeyResponse>(`/api/keys/${encodeURIComponent(id)}/rotate`, {
    method: 'POST',
  });
}

