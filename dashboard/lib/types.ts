/**
 * Cost Melt Dashboard - Type Definitions
 */

export interface Stats {
  total_requests: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_actual_cost: number;
  total_baseline_cost: number;
  total_savings: number;
  savings_pct: number;
  cache_hit_rate: number;
}

export interface ModelUsage {
  model: string;
  count: number;
  input_tokens: number;
  output_tokens: number;
  actual_cost: number;
}

export interface UsageResponse {
  models: ModelUsage[];
}

export interface CacheMetrics {
  cache_hits: number;
  cache_misses: number;
  hit_rate: number;
  recent_hits: Array<{
    prompt: string;
    response_length: number;
  }>;
}

export interface RoutingDistribution {
  complexity_distribution: {
    "0": number;
    "1": number;
    "2": number;
  };
  model_distribution: Record<string, number>;
}

export interface DailyMetric {
  date: string;
  requests: number;
  tokens_in: number;
  tokens_out: number;
  actual_cost: number;
  baseline_cost: number;
  savings: number;
}

export interface DailyResponse {
  days: DailyMetric[];
}

export interface ModelEntry {
  model: string;
  requests: number;
  actual_cost: number;
  baseline_cost: number;
  savings_pct: number;
}

export interface ModelsResponse {
  entries: ModelEntry[];
}

export interface SavingsData {
  date: string;
  saved: number;
}

export interface SavingsResponse {
  savings_over_time: SavingsData[];
}

