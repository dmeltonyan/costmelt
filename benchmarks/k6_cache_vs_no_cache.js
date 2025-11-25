/**
 * Cost Melt - Cache vs No Cache Performance Comparison
 * 
 * Compares performance with semantic cache hits vs cache misses.
 * 
 * Usage:
 *   k6 run k6_cache_vs_no_cache.js
 * 
 * With environment variables:
 *   BENCHMARK_BASE_URL=http://localhost:8000 BENCHMARK_API_KEY=cm_live_... k6 run k6_cache_vs_no_cache.js
 * 
 * This test runs two scenarios in parallel:
 *   - cached: Sends the same prompt repeatedly (high cache hit rate)
 *   - uncached: Sends random prompts (low cache hit rate)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics for cached vs uncached requests
const cachedLatency = new Trend('cached_latency');
const uncachedLatency = new Trend('uncached_latency');
const cachedErrorRate = new Rate('cached_errors');
const uncachedErrorRate = new Rate('uncached_errors');
const cacheHitRate = new Rate('cache_hits');

// Configuration
const BASE_URL = __ENV.BENCHMARK_BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.BENCHMARK_API_KEY || '';

// Fixed prompt for cache hits
const CACHED_PROMPT = 'Explain what a vector database is and how it differs from traditional databases.';

// Random prompts for cache misses
const RANDOM_PROMPTS = [
  'What is machine learning?',
  'Explain the concept of recursion.',
  'How does a hash table work?',
  'What is the difference between SQL and NoSQL?',
  'Design a rate limiting algorithm.',
  'Explain how Docker containers work.',
  'What are microservices?',
  'How does a load balancer distribute traffic?',
  'Explain synchronous vs asynchronous programming.',
  'What is REST API?',
  'How do you implement caching?',
  'Explain the transformer architecture.',
  'What is a distributed system?',
  'How does Redis work?',
  'Explain database indexing.',
];

// Test configuration with two scenarios
export const options = {
  scenarios: {
    // Scenario A: Repeated same prompt (cache hits)
    cached: {
      executor: 'constant-arrival-rate',
      rate: 20,                    // 20 requests per second
      timeUnit: '1s',
      duration: '1m',
      preAllocatedVUs: 10,
      maxVUs: 50,
      exec: 'cachedScenario',
    },
    
    // Scenario B: Random prompts (cache misses)
    uncached: {
      executor: 'constant-arrival-rate',
      rate: 20,                    // 20 requests per second
      timeUnit: '1s',
      duration: '1m',
      preAllocatedVUs: 10,
      maxVUs: 50,
      exec: 'uncachedScenario',
    },
  },
  
  thresholds: {
    // Cached requests should be faster
    cached_latency: ['p(95)<500', 'p(99)<1000'],
    // Uncached requests may be slower
    uncached_latency: ['p(95)<2000', 'p(99)<5000'],
    // Both should have low error rates
    cached_errors: ['rate<0.01'],
    uncached_errors: ['rate<0.01'],
    // Overall error rate
    http_req_failed: ['rate<0.01'],
  },
};

/**
 * Cached scenario: Send the same prompt repeatedly
 * This should result in high cache hit rates after the first request
 */
export function cachedScenario() {
  const payload = JSON.stringify({
    prompt: CACHED_PROMPT,
    user_id: 'k6-benchmark-cached',
    metadata: {
      source: 'k6-benchmark',
      test_type: 'cached_scenario',
    },
  });
  
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }
  
  const startTime = Date.now();
  const response = http.post(
    `${BASE_URL}/v1/route`,
    payload,
    { headers: headers }
  );
  const endTime = Date.now();
  const latency = endTime - startTime;
  
  cachedLatency.add(latency);
  
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response has body': (r) => r.body.length > 0,
  });
  
  // Check if response came from cache
  try {
    const data = JSON.parse(response.body);
    if (data.cache_hit === true) {
      cacheHitRate.add(1);
      console.log(`[CACHED] Cache hit! Latency: ${latency}ms`);
    } else {
      cacheHitRate.add(0);
      console.log(`[CACHED] Cache miss. Latency: ${latency}ms`);
    }
  } catch (e) {
    // Ignore parse errors
  }
  
  if (!success || response.status >= 400) {
    cachedErrorRate.add(1);
  } else {
    cachedErrorRate.add(0);
  }
  
  sleep(0.1); // Small delay between requests
}

/**
 * Uncached scenario: Send random prompts
 * This should result in low cache hit rates
 */
export function uncachedScenario() {
  // Select a random prompt and add a unique suffix to ensure cache miss
  const randomPrompt = RANDOM_PROMPTS[Math.floor(Math.random() * RANDOM_PROMPTS.length)];
  const uniqueSuffix = ` [test-${Math.random().toString(36).substring(7)}]`;
  const prompt = randomPrompt + uniqueSuffix;
  
  const payload = JSON.stringify({
    prompt: prompt,
    user_id: 'k6-benchmark-uncached',
    metadata: {
      source: 'k6-benchmark',
      test_type: 'uncached_scenario',
    },
  });
  
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }
  
  const startTime = Date.now();
  const response = http.post(
    `${BASE_URL}/v1/route`,
    payload,
    { headers: headers }
  );
  const endTime = Date.now();
  const latency = endTime - startTime;
  
  uncachedLatency.add(latency);
  
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response has body': (r) => r.body.length > 0,
  });
  
  // Check if response came from cache (should be false for random prompts)
  try {
    const data = JSON.parse(response.body);
    if (data.cache_hit === true) {
      console.log(`[UNCACHED] Unexpected cache hit! Latency: ${latency}ms`);
    } else {
      console.log(`[UNCACHED] Cache miss (expected). Latency: ${latency}ms`);
    }
  } catch (e) {
    // Ignore parse errors
  }
  
  if (!success || response.status >= 400) {
    uncachedErrorRate.add(1);
  } else {
    uncachedErrorRate.add(0);
  }
  
  sleep(0.1); // Small delay between requests
}

/**
 * Setup function
 */
export function setup() {
  console.log(`Testing Cost Melt API at: ${BASE_URL}`);
  console.log('Running cache comparison test:');
  console.log('  - Cached scenario: Same prompt (high cache hit rate)');
  console.log('  - Uncached scenario: Random prompts (low cache hit rate)');
  if (API_KEY) {
    console.log('Using API key authentication');
  }
  return {};
}

/**
 * Teardown function
 */
export function teardown(data) {
  console.log('Cache comparison test completed');
  console.log('Compare cached_latency vs uncached_latency metrics to see cache performance impact');
}

