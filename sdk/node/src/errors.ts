/**
 * Cost Melt Node SDK - Custom Exceptions
 * 
 * Custom error classes for Cost Melt API errors.
 */

/**
 * Base error class for all Cost Melt errors
 */
export class APIError extends Error {
  code: number;
  
  constructor(message: string, code: number = 0) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    Error.captureStackTrace(this, this.constructor);
  }
  
  toString(): string {
    if (this.code) {
      return `[${this.code}] ${this.message}`;
    }
    return this.message;
  }
}

/**
 * Rate limit exceeded error
 */
export class RateLimitError extends APIError {
  retryAfter?: number;
  
  constructor(message: string, retryAfter?: number) {
    super(message, 429);
    this.retryAfter = retryAfter;
  }
}

/**
 * Server-side error (5xx)
 */
export class ServerError extends APIError {
  constructor(message: string, code: number = 500) {
    super(message, code);
  }
}

/**
 * Network/connection error
 */
export class NetworkError extends APIError {
  constructor(message: string) {
    super(message, 0);
  }
}

/**
 * Request validation error
 */
export class ValidationError extends APIError {
  constructor(message: string) {
    super(message, 400);
  }
}

/**
 * Request timeout error
 */
export class TimeoutError extends APIError {
  constructor(message: string = "Request timed out") {
    super(message, 504);
  }
}

