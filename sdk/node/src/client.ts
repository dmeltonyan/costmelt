/**
 * Cost Melt Node SDK - Main Client
 * 
 * Production-ready TypeScript/JavaScript client for Cost Melt API.
 */

import axios, { AxiosInstance, AxiosError } from "axios";
import {
  RouteResponse,
  RouteOptions,
  ClientOptions,
  ErrorResponse,
} from "./types";
import {
  APIError,
  RateLimitError,
  ServerError,
  NetworkError,
  ValidationError,
  TimeoutError,
} from "./errors";
import { calculateBackoffDelay, sleep, isNetworkError } from "./utils";

/**
 * Official Node.js/TypeScript client for Cost Melt API.
 * 
 * Provides a simple interface for routing LLM requests through Cost Melt's
 * optimization pipeline with automatic retries and error handling.
 * 
 * @example
 * ```typescript
 * import { CostMeltClient } from "costmelt";
 * 
 * const client = new CostMeltClient();
 * const response = await client.route("Explain binary search.");
 * console.log(response.response);
 * ```
 */
export class CostMeltClient {
  private apiKey?: string;
  private baseUrl: string;
  private timeout: number;
  private maxRetries: number;
  private axiosInstance: AxiosInstance;

  /**
   * Initialize Cost Melt client.
   * 
   * @param options - Client configuration options
   * @param options.apiKey - API key for authentication (optional in dev mode)
   * @param options.baseUrl - Base URL for Cost Melt API (default: http://localhost:8000)
   * @param options.timeout - Request timeout in milliseconds (default: 30000)
   * @param options.maxRetries - Maximum number of retry attempts (default: 3)
   */
  constructor(options?: ClientOptions) {
    this.apiKey = options?.apiKey || process.env.COSTMELT_API_KEY;
    this.baseUrl = (options?.baseUrl || process.env.COSTMELT_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
    this.timeout = options?.timeout || 30000;
    this.maxRetries = options?.maxRetries || 3;

    // Create axios instance
    this.axiosInstance = axios.create({
      baseURL: this.baseUrl,
      timeout: this.timeout,
      headers: {
        "Content-Type": "application/json",
        "User-Agent": "costmelt-node-sdk/0.1.0",
      },
    });

    // Add API key to headers if provided
    if (this.apiKey) {
      this.axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${this.apiKey}`;
    }
  }

  /**
   * Route an LLM request through Cost Melt's optimization pipeline.
   * 
   * This method sends a prompt to Cost Melt, which automatically:
   * - Compresses the prompt to reduce tokens
   * - Checks semantic cache for similar prompts
   * - Routes to the optimal model based on complexity
   * - Batches requests when possible
   * - Calculates cost and savings
   * 
   * @param prompt - The user prompt to process (required)
   * @param options - Optional request parameters
   * @param options.user_id - User identifier for analytics
   * @param options.metadata - Additional metadata dictionary
   * @param options.max_output_tokens - Maximum output tokens (default: 400)
   * 
   * @returns RouteResponse with LLM response and metadata
   * 
   * @throws {ValidationError} If prompt is invalid
   * @throws {RateLimitError} If rate limit is exceeded
   * @throws {ServerError} If server returns 5xx error
   * @throws {NetworkError} If connection fails
   */
  async route(prompt: string, options?: RouteOptions): Promise<RouteResponse> {
    if (!prompt || !prompt.trim()) {
      throw new ValidationError("Prompt cannot be empty");
    }

    const payload = {
      prompt: prompt.trim(),
      ...(options?.user_id && { user_id: options.user_id }),
      ...(options?.metadata && { metadata: options.metadata }),
      ...(options?.max_output_tokens !== undefined && { max_output_tokens: options.max_output_tokens }),
    };

    return this._makeRequest<RouteResponse>("POST", "/v1/route", payload);
  }

  /**
   * Get global statistics from dashboard.
   * 
   * @returns Dictionary with total requests, tokens, costs, savings, cache hit rate
   */
  async getStats(): Promise<any> {
    return this._makeRequest("GET", "/dashboard/stats");
  }

  /**
   * Get usage breakdown by model.
   * 
   * @returns Dictionary with models list containing usage statistics
   */
  async getUsage(): Promise<any> {
    return this._makeRequest("GET", "/dashboard/usage");
  }

  /**
   * Get cache performance metrics.
   * 
   * @returns Dictionary with cache hits, misses, hit rate, recent hits
   */
  async getCacheStats(): Promise<any> {
    return this._makeRequest("GET", "/dashboard/cache");
  }

  /**
   * Get routing complexity and model distribution.
   * 
   * @returns Dictionary with complexity_distribution and model_distribution
   */
  async getRoutingStats(): Promise<any> {
    return this._makeRequest("GET", "/dashboard/routing");
  }

  /**
   * Get daily timeseries metrics.
   * 
   * @param days - Number of days to look back (default: 30)
   * @returns Dictionary with days list containing daily metrics
   */
  async getDailyStats(days: number = 30): Promise<any> {
    return this._makeRequest("GET", `/dashboard/daily?days=${days}`);
  }

  /**
   * Get model usage and cost comparison.
   * 
   * @returns Dictionary with entries list containing model statistics
   */
  async getModelsStats(): Promise<any> {
    return this._makeRequest("GET", "/dashboard/models");
  }

  /**
   * Get historical savings over time.
   * 
   * @param days - Number of days to look back (default: 30)
   * @returns Dictionary with savings_over_time list
   */
  async getSavingsStats(days: number = 30): Promise<any> {
    return this._makeRequest("GET", `/dashboard/savings?days=${days}`);
  }

  /**
   * Check API health status.
   * 
   * @returns Dictionary with status information
   */
  async healthCheck(): Promise<any> {
    return this._makeRequest("GET", "/health");
  }

  /**
   * Make HTTP request to Cost Melt API with retry logic.
   * 
   * @param method - HTTP method (GET, POST)
   * @param endpoint - API endpoint path
   * @param payload - Request payload (for POST requests)
   * @returns Response data
   * @throws Various APIError subclasses based on error type
   */
  private async _makeRequest<T>(
    method: "GET" | "POST",
    endpoint: string,
    payload?: any
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const response = await this.axiosInstance.request({
          method,
          url: endpoint,
          data: method === "POST" ? payload : undefined,
        });

        return response.data as T;
      } catch (error) {
        lastError = error as Error;

        if (axios.isAxiosError(error)) {
          const axiosError = error as AxiosError;
          const statusCode = axiosError.response?.status || 0;
          const errorData = axiosError.response?.data as ErrorResponse | undefined;

          // Handle successful response (shouldn't happen in catch, but just in case)
          if (statusCode === 200) {
            return axiosError.response?.data as T;
          }

          // Parse error message
          const errorMessage = errorData?.message || errorData?.error || axiosError.message;
          const errorCode = errorData?.code || statusCode;

          // Rate limit error (don't retry)
          if (statusCode === 429) {
            const retryAfter = errorData?.retry_after;
            throw new RateLimitError(errorMessage, retryAfter);
          }

          // Validation error (don't retry)
          if (statusCode === 400) {
            throw new ValidationError(errorMessage);
          }

          // Client errors 4xx (don't retry, except 429)
          if (statusCode >= 400 && statusCode < 500) {
            throw new APIError(errorMessage, errorCode);
          }

          // Server errors 5xx (retryable)
          if (statusCode >= 500) {
            if (attempt < this.maxRetries - 1) {
              const delay = calculateBackoffDelay(attempt);
              await sleep(delay);
              continue;
            }
            throw new ServerError(errorMessage, errorCode);
          }

          // Timeout error (retryable)
          if (statusCode === 504 || axiosError.code === "ETIMEDOUT") {
            if (attempt < this.maxRetries - 1) {
              const delay = calculateBackoffDelay(attempt);
              await sleep(delay);
              continue;
            }
            throw new TimeoutError(errorMessage);
          }
        }

        // Network errors (retryable)
        if (isNetworkError(error)) {
          if (attempt < this.maxRetries - 1) {
            const delay = calculateBackoffDelay(attempt);
            await sleep(delay);
            continue;
          }
          throw new NetworkError(`Network error: ${(error as Error).message}`);
        }

        // Other/unclassified errors — retry up to the configured limit,
        // same as the network/server-error branches above. (Previously
        // gated on isRetryableError(0), which is always false since 0
        // never matches any of that function's retryable status codes,
        // so this branch silently never retried and always failed on
        // the first attempt regardless of maxRetries.)
        if (attempt < this.maxRetries - 1) {
          const delay = calculateBackoffDelay(attempt);
          await sleep(delay);
          continue;
        }

        throw new NetworkError(`Request failed: ${(error as Error).message}`);
      }
    }

    // Should never reach here, but handle last error
    if (lastError) {
      throw new NetworkError(`Request failed after ${this.maxRetries} attempts: ${lastError.message}`);
    }

    throw new NetworkError("Request failed for unknown reason");
  }
}

