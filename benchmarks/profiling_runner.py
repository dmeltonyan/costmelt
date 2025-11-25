"""
Cost Melt - Profiling Runner

Simple profiling harness to measure backend performance and identify hotspots.
Uses cProfile to analyze CPU usage during sequential requests.

Usage:
    python profiling_runner.py
    python profiling_runner.py --count 100
    python profiling_runner.py --count 200 --output profile.stats

Environment Variables:
    BENCHMARK_BASE_URL: Base URL for Cost Melt API (default: http://localhost:8000)
    BENCHMARK_API_KEY: API key for authentication (optional)
"""

import os
import sys
import time
import cProfile
import pstats
import argparse
import requests
from typing import List, Dict, Any
import json


# Sample prompts for profiling
PROMPTS = [
    "What is machine learning?",
    "Write a SQL query to find all users who haven't logged in for 30 days.",
    "Explain how a hash table works and provide a Python implementation.",
    "Design a distributed caching system that handles cache invalidation across multiple nodes.",
    "Explain the transformer architecture in detail, including attention mechanisms.",
]


def make_request(
    base_url: str,
    prompt: str,
    api_key: str = None,
    request_id: int = 0
) -> Dict[str, Any]:
    """
    Make a single request to /v1/route endpoint.
    
    Args:
        base_url: Base URL for Cost Melt API
        prompt: Prompt text to send
        api_key: Optional API key for authentication
        request_id: Request identifier for logging
    
    Returns:
        Dictionary with response data and timing information
    """
    url = f"{base_url}/v1/route"
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    payload = {
        "prompt": prompt,
        "user_id": "profiling-runner",
        "metadata": {
            "source": "profiling",
            "request_id": request_id
        }
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "latency_ms": latency,
                "status_code": response.status_code,
                "cache_hit": data.get("cache_hit", False),
                "model_used": data.get("model_used", "unknown"),
                "tokens_in": data.get("tokens_in", 0),
                "tokens_out": data.get("tokens_out", 0),
            }
        else:
            return {
                "success": False,
                "latency_ms": latency,
                "status_code": response.status_code,
                "error": response.text[:200]  # First 200 chars of error
            }
    except requests.exceptions.Timeout:
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        return {
            "success": False,
            "latency_ms": latency,
            "status_code": 0,
            "error": "Request timeout"
        }
    except Exception as e:
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        return {
            "success": False,
            "latency_ms": latency,
            "status_code": 0,
            "error": str(e)
        }


def run_requests(
    base_url: str,
    api_key: str,
    count: int
) -> List[Dict[str, Any]]:
    """
    Run N sequential requests and collect results.
    
    Args:
        base_url: Base URL for Cost Melt API
        api_key: Optional API key
        count: Number of requests to make
    
    Returns:
        List of request results
    """
    results = []
    
    print(f"Making {count} sequential requests to {base_url}/v1/route...")
    print("This may take a while depending on backend performance.\n")
    
    for i in range(count):
        # Cycle through prompts
        prompt = PROMPTS[i % len(PROMPTS)]
        
        print(f"Request {i+1}/{count}: {prompt[:50]}...", end=" ", flush=True)
        
        result = make_request(base_url, prompt, api_key, i)
        results.append(result)
        
        if result["success"]:
            print(f"✓ {result['latency_ms']:.0f}ms (cache: {result.get('cache_hit', False)})")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    return results


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze request results and compute statistics.
    
    Args:
        results: List of request results
    
    Returns:
        Dictionary with statistics
    """
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if not successful:
        return {
            "total_requests": len(results),
            "successful": 0,
            "failed": len(failed),
            "success_rate": 0.0,
            "error": "No successful requests"
        }
    
    latencies = [r["latency_ms"] for r in successful]
    latencies.sort()
    
    total_time = sum(latencies)
    avg_latency = total_time / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    
    # Percentiles
    p50 = latencies[int(len(latencies) * 0.50)]
    p90 = latencies[int(len(latencies) * 0.90)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]
    
    # Cache hit rate
    cache_hits = sum(1 for r in successful if r.get("cache_hit", False))
    cache_hit_rate = (cache_hits / len(successful)) * 100 if successful else 0
    
    # Model distribution
    models = {}
    for r in successful:
        model = r.get("model_used", "unknown")
        models[model] = models.get(model, 0) + 1
    
    return {
        "total_requests": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "success_rate": (len(successful) / len(results)) * 100,
        "total_time_ms": total_time,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "p50_latency_ms": p50,
        "p90_latency_ms": p90,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "cache_hit_rate": cache_hit_rate,
        "model_distribution": models,
    }


def print_statistics(stats: Dict[str, Any]):
    """
    Print statistics in a readable format.
    
    Args:
        stats: Statistics dictionary
    """
    print("\n" + "="*60)
    print("PROFILING RESULTS")
    print("="*60)
    print(f"\nRequest Statistics:")
    print(f"  Total requests:     {stats['total_requests']}")
    print(f"  Successful:         {stats['successful']}")
    print(f"  Failed:             {stats['failed']}")
    print(f"  Success rate:       {stats['success_rate']:.1f}%")
    
    if "error" in stats:
        print(f"\nError: {stats['error']}")
        return
    
    print(f"\nLatency Statistics (ms):")
    print(f"  Average:            {stats['avg_latency_ms']:.2f}")
    print(f"  Minimum:            {stats['min_latency_ms']:.2f}")
    print(f"  Maximum:            {stats['max_latency_ms']:.2f}")
    print(f"  p50 (median):       {stats['p50_latency_ms']:.2f}")
    print(f"  p90:                {stats['p90_latency_ms']:.2f}")
    print(f"  p95:                {stats['p95_latency_ms']:.2f}")
    print(f"  p99:                {stats['p99_latency_ms']:.2f}")
    
    print(f"\nCache Performance:")
    print(f"  Cache hit rate:     {stats['cache_hit_rate']:.1f}%")
    
    if stats['model_distribution']:
        print(f"\nModel Distribution:")
        for model, count in stats['model_distribution'].items():
            percentage = (count / stats['successful']) * 100
            print(f"  {model}: {count} ({percentage:.1f}%)")
    
    print("\n" + "="*60)


def run_profile(count: int = 50, output_file: str = None):
    """
    Run profiling session.
    
    Args:
        count: Number of requests to make
        output_file: Optional file to save cProfile stats
    """
    base_url = os.getenv("BENCHMARK_BASE_URL", "http://localhost:8000")
    api_key = os.getenv("BENCHMARK_API_KEY")
    
    print(f"Cost Melt Profiling Runner")
    print(f"Target: {base_url}")
    print(f"Requests: {count}")
    if api_key:
        print("Authentication: Enabled")
    else:
        print("Authentication: Disabled (local dev mode)")
    print()
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Run requests with profiling
    profiler.enable()
    results = run_requests(base_url, api_key, count)
    profiler.disable()
    
    # Analyze results
    stats = analyze_results(results)
    print_statistics(stats)
    
    # Print profiling stats
    print("\n" + "="*60)
    print("CPU PROFILING - TOP 20 FUNCTIONS BY TOTAL TIME")
    print("="*60)
    
    stream = sys.stdout
    if output_file:
        stream = open(output_file, 'w')
    
    profile_stats = pstats.Stats(profiler, stream=stream)
    profile_stats.sort_stats('cumulative')
    profile_stats.print_stats(20)  # Top 20 functions
    
    if output_file:
        stream.close()
        print(f"\nFull profile stats saved to: {output_file}")
        print("View with: python -m pstats profile.stats")
    
    print("\n" + "="*60)
    print("Profiling complete!")
    print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile Cost Melt backend performance")
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of requests to make (default: 50)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for cProfile stats (default: print to stdout)"
    )
    
    args = parser.parse_args()
    
    run_profile(count=args.count, output_file=args.output)

