# Cost Melt Node.js SDK

Official Node.js/TypeScript client library for Cost Melt - LLM routing, caching, batching, and cost-optimization proxy.

## Installation

```bash
npm install costmelt
```

Or install from source:

```bash
git clone https://github.com/your-username/costmelt.git
cd costmelt/sdk/node
npm install
npm run build
```

## Quickstart

```typescript
import { CostMeltClient } from "costmelt";

// Initialize client
const client = new CostMeltClient({
  apiKey: "your-api-key",  // Optional in dev mode
  baseUrl: "http://localhost:8000"  // Default
});

// Route a request
const response = await client.route("Explain binary search algorithm with time complexity.");

console.log(`Response: ${response.response}`);
console.log(`Model: ${response.model_used}`);
console.log(`Cost: $${response.cost.actual_cost.toFixed(6)}`);
console.log(`Savings: ${response.cost.savings_pct.toFixed(1)}%`);
```

## Usage

### Basic Request

```typescript
import { CostMeltClient } from "costmelt";

const client = new CostMeltClient();

// Simple request
const response = await client.route("What is machine learning?");

// With user ID for analytics
const response = await client.route("Write a SQL query for top customers", {
  user_id: "user-123"
});

// With metadata and custom token limit
const response = await client.route("Explain REST APIs", {
  user_id: "user-123",
  metadata: { source: "docs", priority: "high" },
  max_output_tokens: 500
});
```

### Response Structure

```typescript
interface RouteResponse {
  response: string;              // LLM-generated response text
  model_used: string;            // Model that processed the request
  complexity: number;            // Complexity classification (0, 1, or 2)
  cache_hit: boolean;            // Whether response came from cache
  tokens_in: number;             // Number of input tokens
  tokens_out: number;            // Number of output tokens
  cost: {
    actual_cost: number;         // Actual cost in USD
    baseline_cost: number;        // Baseline cost (GPT-4o) in USD
    absolute_savings: number;     // Dollar amount saved
    savings_pct: number;          // Percentage saved (0-100)
  };
  latency_ms: number;            // Request latency in milliseconds
}
```

### Error Handling

```typescript
import { CostMeltClient } from "costmelt";
import {
  RateLimitError,
  ValidationError,
  ServerError,
  NetworkError
} from "costmelt";

const client = new CostMeltClient();

try {
  const response = await client.route("Your prompt here");
} catch (error) {
  if (error instanceof ValidationError) {
    console.error(`Invalid request: ${error.message}`);
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after: ${error.retryAfter} seconds`);
  } else if (error instanceof ServerError) {
    console.error(`Server error: ${error.message}`);
  } else if (error instanceof NetworkError) {
    console.error(`Connection error: ${error.message}`);
  } else {
    console.error(`Unexpected error: ${error}`);
  }
}
```

### Dashboard Endpoints

```typescript
// Get global statistics
const stats = await client.getStats();
console.log(`Total requests: ${stats.total_requests}`);
console.log(`Total savings: $${stats.total_savings.toFixed(2)}`);

// Get usage by model
const usage = await client.getUsage();
for (const model of usage.models) {
  console.log(`${model.model}: ${model.count} requests`);
}

// Get cache performance
const cache = await client.getCacheStats();
console.log(`Cache hit rate: ${cache.hit_rate}%`);

// Get daily metrics
const daily = await client.getDailyStats(30);
for (const day of daily.days) {
  console.log(`${day.date}: ${day.requests} requests`);
}

// Get model comparison
const models = await client.getModelsStats();
for (const entry of models.entries) {
  console.log(`${entry.model}: ${entry.savings_pct.toFixed(1)}% savings`);
}

// Get savings over time
const savings = await client.getSavingsStats(30);
for (const item of savings.savings_over_time) {
  console.log(`${item.date}: $${item.saved.toFixed(2)} saved`);
}
```

### Environment Variables

Set `COSTMELT_API_KEY` and `COSTMELT_BASE_URL` environment variables:

```bash
export COSTMELT_API_KEY="your-api-key"
export COSTMELT_BASE_URL="http://localhost:8000"
```

```typescript
// Client will automatically use environment variables
const client = new CostMeltClient();
```

### Retry Logic

The client automatically retries on:
- Network errors (ENOTFOUND, ETIMEDOUT, ECONNREFUSED)
- 5xx server errors
- 429 rate limit errors
- 504 timeout errors

Retries use exponential backoff with jitter (up to 3 attempts by default).

### Custom Configuration

```typescript
const client = new CostMeltClient({
  apiKey: "your-api-key",
  baseUrl: "https://api.costmelt.com",
  timeout: 60000,      // Request timeout in milliseconds
  maxRetries: 5        // Maximum retry attempts
});
```

### TypeScript Support

The SDK is written in TypeScript and includes full type definitions:

```typescript
import { CostMeltClient, RouteResponse, RouteOptions } from "costmelt";

const client = new CostMeltClient();

const options: RouteOptions = {
  user_id: "user-123",
  max_output_tokens: 500
};

const response: RouteResponse = await client.route("Your prompt", options);
```

## API Reference

### CostMeltClient

#### `constructor(options?: ClientOptions)`

Initialize the client.

**Parameters:**
- `options.apiKey` (string, optional): API key for authentication
- `options.baseUrl` (string, optional): Base URL for Cost Melt API
- `options.timeout` (number, optional): Request timeout in milliseconds
- `options.maxRetries` (number, optional): Maximum number of retry attempts

#### `route(prompt: string, options?: RouteOptions): Promise<RouteResponse>`

Route an LLM request through Cost Melt.

**Parameters:**
- `prompt` (string): The user prompt to process (required)
- `options.user_id` (string, optional): User identifier for analytics
- `options.metadata` (object, optional): Additional metadata
- `options.max_output_tokens` (number, optional): Maximum output tokens (default: 400)

**Returns:** `Promise<RouteResponse>`

**Throws:**
- `ValidationError`: If prompt is invalid
- `RateLimitError`: If rate limit is exceeded
- `ServerError`: If server returns 5xx error
- `NetworkError`: If connection fails

## Publishing to npm

### Build Package

```bash
cd sdk/node
npm run build
```

### Publish to npm

```bash
# Login to npm
npm login

# Publish package
npm publish --access public
```

## Development

### Setup Development Environment

```bash
cd sdk/node
npm install
```

### Build TypeScript

```bash
npm run build
```

### Run Tests

```bash
npm test
```

### Lint Code

```bash
npm run lint
```

### Format Code

```bash
npm run format
```

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation:** [https://docs.costmelt.com](https://docs.costmelt.com)
- **GitHub Issues:** [https://github.com/your-username/costmelt/issues](https://github.com/your-username/costmelt/issues)
- **Email:** support@costmelt.com

