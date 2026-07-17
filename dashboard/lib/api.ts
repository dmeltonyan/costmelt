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
  SavingsResponse
} from './types';

/**
 * Fetch data from this app's own API proxy routes
 */
async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(endpoint, {
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
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

