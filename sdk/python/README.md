# Cost Melt Python SDK

Official Python client library for Cost Melt - LLM routing, caching, batching, and cost-optimization proxy.

## Installation

```bash
pip install costmelt
```

Or install from source:

```bash
git clone https://github.com/your-username/costmelt.git
cd costmelt/sdk/python
pip install -e .
```

## Quickstart

```python
from costmelt import CostMeltClient

# Initialize client
client = CostMeltClient(
    api_key="your-api-key",  # Optional in dev mode
    base_url="http://localhost:8000"  # Default
)

# Route a request
response = client.route("Explain binary search algorithm with time complexity.")

print(f"Response: {response['response']}")
print(f"Model: {response['model_used']}")
print(f"Cost: ${response['cost']['actual_cost']:.6f}")
print(f"Savings: {response['cost']['savings_pct']:.1f}%")
```

## Usage

### Basic Request

```python
from costmelt import CostMeltClient

client = CostMeltClient()

# Simple request
response = client.route("What is machine learning?")

# With user ID for analytics
response = client.route(
    prompt="Write a SQL query for top customers",
    user_id="user-123"
)

# With metadata
response = client.route(
    prompt="Explain REST APIs",
    user_id="user-123",
    metadata={"source": "docs", "priority": "high"},
    max_output_tokens=500
)
```

### Response Structure

```python
response = {
    "response": "Binary search is a search algorithm...",
    "model_used": "gpt-4o-mini",
    "complexity": 1,
    "cache_hit": False,
    "tokens_in": 82,
    "tokens_out": 146,
    "cost": {
        "actual_cost": 0.00027,
        "baseline_cost": 0.00180,
        "absolute_savings": 0.00153,
        "savings_pct": 85.0
    },
    "latency_ms": 120
}
```

### Error Handling

```python
from costmelt import CostMeltClient
from costmelt.errors import (
    RateLimitError,
    ValidationError,
    ServerError,
    APIConnectionError
)

client = CostMeltClient()

try:
    response = client.route("Your prompt here")
except ValidationError as e:
    print(f"Invalid request: {e}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
except ServerError as e:
    print(f"Server error: {e}")
except APIConnectionError as e:
    print(f"Connection error: {e}")
```

### Dashboard Endpoints

```python
# Get global statistics
stats = client.get_stats()
print(f"Total requests: {stats['total_requests']}")
print(f"Total savings: ${stats['total_savings']:.2f}")

# Get usage by model
usage = client.get_usage()
for model in usage['models']:
    print(f"{model['model']}: {model['count']} requests")

# Get cache performance
cache = client.get_cache_stats()
print(f"Cache hit rate: {cache['hit_rate']}%")

# Get daily metrics
daily = client.get_daily_stats(days=30)
for day in daily['days']:
    print(f"{day['date']}: {day['requests']} requests")

# Get model comparison
models = client.get_models_stats()
for entry in models['entries']:
    print(f"{entry['model']}: {entry['savings_pct']:.1f}% savings")

# Get savings over time
savings = client.get_savings_stats(days=30)
for item in savings['savings_over_time']:
    print(f"{item['date']}: ${item['saved']:.2f} saved")
```

### Environment Variables

Set `COSTMELT_API_KEY` environment variable to avoid passing it explicitly:

```bash
export COSTMELT_API_KEY="your-api-key"
```

```python
# Client will automatically use COSTMELT_API_KEY from environment
client = CostMeltClient()
```

### Retry Logic

The client automatically retries on:
- Network errors (connection failures)
- 5xx server errors
- 429 rate limit errors
- 504 timeout errors

Retries use exponential backoff with jitter (up to 3 attempts by default).

### Custom Configuration

```python
client = CostMeltClient(
    api_key="your-api-key",
    base_url="https://api.costmelt.com",
    timeout=60.0,  # Request timeout in seconds
    max_retries=5  # Maximum retry attempts
)
```

## API Reference

### CostMeltClient

#### `__init__(api_key=None, base_url="http://localhost:8000", timeout=30.0, max_retries=3)`

Initialize the client.

**Parameters:**
- `api_key` (str, optional): API key for authentication
- `base_url` (str): Base URL for Cost Melt API
- `timeout` (float): Request timeout in seconds
- `max_retries` (int): Maximum number of retry attempts

#### `route(prompt, user_id=None, metadata=None, max_output_tokens=400)`

Route an LLM request through Cost Melt.

**Parameters:**
- `prompt` (str): The user prompt to process (required)
- `user_id` (str, optional): User identifier for analytics
- `metadata` (dict, optional): Additional metadata
- `max_output_tokens` (int, optional): Maximum output tokens (default: 400)

**Returns:** `RouteResponse` dictionary

**Raises:**
- `ValidationError`: If prompt is invalid
- `RateLimitError`: If rate limit is exceeded
- `ServerError`: If server returns 5xx error
- `APIConnectionError`: If connection fails

## Publishing to PyPI

### Build Package

```bash
cd sdk/python
python -m build
```

### Publish to PyPI

```bash
# Using twine (recommended)
pip install twine
twine upload dist/*

# Or using poetry
poetry build
poetry publish --username __token__ --password <pypi_token>
```

## Development

### Setup Development Environment

```bash
cd sdk/python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Type Checking

```bash
mypy costmelt
```

### Code Formatting

```bash
black costmelt
```

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation:** [https://docs.costmelt.com](https://docs.costmelt.com)
- **GitHub Issues:** [https://github.com/your-username/costmelt/issues](https://github.com/your-username/costmelt/issues)
- **Email:** support@costmelt.com

