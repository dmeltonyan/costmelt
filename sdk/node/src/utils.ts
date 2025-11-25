/**
 * Cost Melt Node SDK - Utility Functions
 * 
 * Helper functions for retries, backoff, and type checking.
 */

/**
 * Calculate exponential backoff delay
 */
export function calculateBackoffDelay(
  attempt: number,
  baseDelay: number = 1000,
  maxDelay: number = 60000
): number {
  const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
  // Add jitter (random factor between 0.5 and 1.5)
  const jitter = 0.5 + Math.random();
  return delay * jitter;
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Check if error is retryable
 */
export function isRetryableError(statusCode: number): boolean {
  // Retry on 5xx errors, 429 (rate limit), and 504 (timeout)
  return statusCode >= 500 || statusCode === 429 || statusCode === 504;
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: any): boolean {
  return (
    error.code === "ENOTFOUND" ||
    error.code === "ETIMEDOUT" ||
    error.code === "ECONNREFUSED" ||
    error.message?.includes("timeout") ||
    error.message?.includes("network")
  );
}

/**
 * Type guard for ErrorResponse
 */
export function isErrorResponse(obj: any): obj is { error: string; code: number; message: string } {
  return (
    typeof obj === "object" &&
    obj !== null &&
    typeof obj.error === "string" &&
    typeof obj.code === "number"
  );
}

