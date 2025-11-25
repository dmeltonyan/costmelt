/**
 * Cost Melt Node SDK - Type Definitions
 * 
 * TypeScript interfaces for requests and responses.
 */

/**
 * Cost breakdown for a request
 */
export interface CostSummary {
  actual_cost: number;
  baseline_cost: number;
  absolute_savings: number;
  savings_pct: number;
}

/**
 * Request options for route method
 */
export interface RouteOptions {
  user_id?: string;
  metadata?: Record<string, any>;
  max_output_tokens?: number;
}

/**
 * Response from /v1/route endpoint
 */
export interface RouteResponse {
  response: string;
  model_used: string;
  complexity: number;
  cache_hit: boolean;
  tokens_in: number;
  tokens_out: number;
  cost: CostSummary;
  latency_ms: number;
}

/**
 * Error response structure
 */
export interface ErrorResponse {
  error: string;
  code: number;
  message: string;
}

/**
 * Client configuration options
 */
export interface ClientOptions {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

