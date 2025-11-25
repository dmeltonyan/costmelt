/**
 * Cost Melt Dashboard - API Client
 * 
 * Functions for fetching data from the backend dashboard API.
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

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Fetch data from backend API
 */
async function fetchAPI<T>(endpoint: string): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;
  
  const response = await fetch(url, {
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
  return fetchAPI<Stats>('/dashboard/stats');
}

/**
 * Get usage breakdown by model
 */
export async function getUsage(): Promise<UsageResponse> {
  return fetchAPI<UsageResponse>('/dashboard/usage');
}

/**
 * Get cache performance metrics
 */
export async function getCache(): Promise<CacheMetrics> {
  return fetchAPI<CacheMetrics>('/dashboard/cache');
}

/**
 * Get routing complexity and model distribution
 */
export async function getRouting(): Promise<RoutingDistribution> {
  return fetchAPI<RoutingDistribution>('/dashboard/routing');
}

/**
 * Get daily timeseries metrics
 */
export async function getDaily(days: number = 30): Promise<DailyResponse> {
  return fetchAPI<DailyResponse>(`/dashboard/daily?days=${days}`);
}

/**
 * Get model usage and cost comparison
 */
export async function getModels(): Promise<ModelsResponse> {
  return fetchAPI<ModelsResponse>('/dashboard/models');
}

/**
 * Get savings over time
 */
export async function getSavings(days: number = 30): Promise<SavingsResponse> {
  return fetchAPI<SavingsResponse>(`/dashboard/savings?days=${days}`);
}

