/**
 * Cost Melt - Basic k6 Load Test
 * 
 * Simple load test targeting the /v1/route endpoint.
 * 
 * Usage:
 *   k6 run k6_basic.js
 * 
 * With environment variables:
 *   BENCHMARK_BASE_URL=http://localhost:8000 BENCHMARK_API_KEY=cm_live_... k6 run k6_basic.js
 * 
 * Custom VUs and duration:
 *   k6 run --vus 100 --duration 2m k6_basic.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const routeLatency = new Trend('route_latency');

// Configuration
const BASE_URL = __ENV.BENCHMARK_BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.BENCHMARK_API_KEY || '';

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 50 },     // Ramp up to 50 users
    { duration: '1m', target: 50 },     // Stay at 50 users
    { duration: '30s', target: 0 },     // Ramp down to 0 users
  ],
  
  thresholds: {
    // 95% of requests must complete below 1 second
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    // Error rate must be below 1%
    http_req_failed: ['rate<0.01'],
    // Custom error rate
    errors: ['rate<0.01'],
  },
};

// Sample prompts for testing
const prompts = [
  'Explain what a vector database is.',
  'What is the difference between SQL and NoSQL?',
  'Write a Python function to reverse a linked list.',
  'Explain how machine learning models are trained.',
  'What are the benefits of using microservices architecture?',
  'How does a load balancer distribute traffic?',
  'Explain the concept of recursion with examples.',
  'What is the difference between synchronous and asynchronous programming?',
  'Design a simple caching strategy for a REST API.',
  'Explain how Docker containers work.',
];

/**
 * Main test function - executed by each virtual user
 */
export default function () {
  // Select a random prompt
  const prompt = prompts[Math.floor(Math.random() * prompts.length)];
  
  // Prepare request payload
  const payload = JSON.stringify({
    prompt: prompt,
    user_id: 'k6-benchmark',
    metadata: {
      source: 'k6-benchmark',
      test_type: 'basic_load_test',
    },
  });
  
  // Prepare headers
  const headers = {
    'Content-Type': 'application/json',
  };
  
  // Add API key if provided
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }
  
  // Make request
  const startTime = Date.now();
  const response = http.post(
    `${BASE_URL}/v1/route`,
    payload,
    { headers: headers }
  );
  const endTime = Date.now();
  const latency = endTime - startTime;
  
  // Record custom metrics
  routeLatency.add(latency);
  
  // Check response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response has body': (r) => r.body.length > 0,
    'response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  // Check for specific error conditions
  if (response.status === 429) {
    errorRate.add(1);
    console.log('Rate limit exceeded');
  } else if (response.status === 401) {
    errorRate.add(1);
    console.log('Authentication failed');
  } else if (response.status >= 500) {
    errorRate.add(1);
    console.log(`Server error: ${response.status}`);
  } else if (!success) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
    
    // Try to parse response and log metrics if available
    try {
      const data = JSON.parse(response.body);
      if (data.latency_ms) {
        console.log(`Request latency: ${data.latency_ms}ms`);
      }
      if (data.cache_hit) {
        console.log('Cache hit!');
      }
    } catch (e) {
      // Ignore parse errors
    }
  }
  
  // Wait between requests (simulate user think time)
  sleep(Math.random() * 2 + 0.5); // 0.5-2.5 seconds
}

/**
 * Setup function - runs once before the test
 */
export function setup() {
  console.log(`Testing Cost Melt API at: ${BASE_URL}`);
  if (API_KEY) {
    console.log('Using API key authentication');
  } else {
    console.log('No API key provided - assuming local dev mode');
  }
  return {};
}

/**
 * Teardown function - runs once after the test
 */
export function teardown(data) {
  console.log('Load test completed');
}

