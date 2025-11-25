"""
Cost Melt - Locust Load Testing Script

Simulates multiple concurrent users hitting the /v1/route endpoint
with various prompt types to test performance under load.

Usage:
    # Basic run with 50 users, spawn rate 10/sec
    locust -f locustfile.py --users 50 --spawn-rate 10 --host http://localhost:8000

    # With API key authentication
    BENCHMARK_API_KEY=cm_live_... locust -f locustfile.py --users 100 --spawn-rate 20

    # Headless mode (no web UI)
    locust -f locustfile.py --users 50 --spawn-rate 10 --host http://localhost:8000 --headless --run-time 5m

Environment Variables:
    BENCHMARK_BASE_URL: Base URL for Cost Melt API (default: http://localhost:8000)
    BENCHMARK_API_KEY: API key for authentication (optional, omit for local dev)
"""

import os
import random
from locust import HttpUser, task, between


# Sample prompts covering different complexity levels
SIMPLE_PROMPTS = [
    "What is machine learning?",
    "Explain the concept of recursion in simple terms.",
    "What is the difference between SQL and NoSQL databases?",
    "Summarize the benefits of using Docker containers.",
    "What is REST API?",
]

MEDIUM_PROMPTS = [
    "Write a SQL query to find all users who haven't logged in for 30 days.",
    "Explain how a hash table works and provide a Python implementation.",
    "Design a rate limiting algorithm using a token bucket approach.",
    "How would you implement a caching layer for a REST API?",
    "Write a function to merge two sorted arrays in O(n) time.",
    "Explain the difference between synchronous and asynchronous programming.",
    "How does a load balancer distribute traffic across multiple servers?",
]

COMPLEX_PROMPTS = [
    "Design a distributed caching system that handles cache invalidation across multiple nodes. Include details on consistency models and failure scenarios.",
    "Implement a RAG (Retrieval Augmented Generation) pipeline that retrieves relevant context from a vector database and generates responses using an LLM.",
    "Explain the transformer architecture in detail, including attention mechanisms, positional encoding, and how it processes sequences.",
    "Design a microservices architecture for an e-commerce platform with order processing, payment handling, and inventory management. Include inter-service communication patterns.",
    "Write a comprehensive algorithm to optimize LLM token usage by compressing prompts while preserving semantic meaning. Include examples.",
    "Explain how to implement a distributed rate limiting system using Redis that scales across multiple API gateway instances.",
    "Design a system to route LLM requests to the most cost-effective model based on prompt complexity, with fallback mechanisms and health checks.",
]

ALL_PROMPTS = SIMPLE_PROMPTS + MEDIUM_PROMPTS + COMPLEX_PROMPTS


class CostMeltUser(HttpUser):
    """
    Locust user class that simulates a user making requests to Cost Melt API.
    
    Behavior:
    - Randomly selects prompts from different complexity levels
    - Waits 0.5-2 seconds between requests
    - Includes API key authentication if provided
    """
    
    wait_time = between(0.5, 2.0)  # Wait between 0.5 and 2 seconds between requests
    
    def on_start(self):
        """Called when a user starts. Set up authentication if API key is provided."""
        self.api_key = os.getenv("BENCHMARK_API_KEY")
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    @task(weight=3)
    def route_simple_prompt(self):
        """Send a simple prompt (30% of requests)"""
        prompt = random.choice(SIMPLE_PROMPTS)
        self._make_route_request(prompt)
    
    @task(weight=5)
    def route_medium_prompt(self):
        """Send a medium complexity prompt (50% of requests)"""
        prompt = random.choice(MEDIUM_PROMPTS)
        self._make_route_request(prompt)
    
    @task(weight=2)
    def route_complex_prompt(self):
        """Send a complex prompt (20% of requests)"""
        prompt = random.choice(COMPLEX_PROMPTS)
        self._make_route_request(prompt)
    
    @task(weight=1)
    def route_random_prompt(self):
        """Send a completely random prompt (10% of requests)"""
        prompt = random.choice(ALL_PROMPTS)
        self._make_route_request(prompt)
    
    def _make_route_request(self, prompt: str):
        """
        Make a POST request to /v1/route endpoint.
        
        Args:
            prompt: The prompt text to send
        """
        payload = {
            "prompt": prompt,
            "user_id": "benchmark-user",
            "metadata": {
                "source": "locust-benchmark",
                "test_type": "load_test"
            }
        }
        
        with self.client.post(
            "/v1/route",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/v1/route"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Log some metrics if available
                    if "latency_ms" in data:
                        response.success()
                    else:
                        response.success()
                except Exception as e:
                    response.failure(f"Failed to parse response: {e}")
            elif response.status_code == 429:
                response.failure("Rate limit exceeded")
            elif response.status_code == 401:
                response.failure("Authentication failed")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")


# Set default host if BENCHMARK_BASE_URL is not set
if not os.getenv("BENCHMARK_BASE_URL"):
    import sys
    if "--host" not in sys.argv:
        # Locust will use this as default if --host is not provided
        pass

