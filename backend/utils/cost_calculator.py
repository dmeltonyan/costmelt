"""
Cost Melt - Production-Grade Cost Calculator Engine

Tracks token costs per model, computes request costs, estimates baseline costs,
and calculates savings for dashboards, billing, ROI reporting, and analytics.
"""

from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Model pricing per 1K tokens (input and output)
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": {
        "input_per_1k": 0.005,
        "output_per_1k": 0.015,
        "provider": "openai"
    },
    "gpt-4o-mini": {
        "input_per_1k": 0.00015,
        "output_per_1k": 0.00060,
        "provider": "openai"
    },
    
    # Anthropic
    "claude-3-haiku": {
        "input_per_1k": 0.00025,
        "output_per_1k": 0.00125,
        "provider": "anthropic"
    },
    "claude-3-5-sonnet": {
        "input_per_1k": 0.003,
        "output_per_1k": 0.015,
        "provider": "anthropic"
    },
    
    # Groq
    "llama3-70b-groq": {
        "input_per_1k": 0.00006,
        "output_per_1k": 0.00006,
        "provider": "groq"
    },
    "llama-3": {
        "input_per_1k": 0.00006,
        "output_per_1k": 0.00006,
        "provider": "groq"
    },
    
    # DeepSeek
    "deepseek-chat": {
        "input_per_1k": 0.00002,
        "output_per_1k": 0.00002,
        "provider": "deepseek"
    }
}

# Default baseline model for cost comparison
DEFAULT_BASELINE_MODEL = "gpt-4o"


class CostCalculator:
    """
    Production-grade cost calculator for LLM token costs.
    
    Features:
    - Per-model pricing lookup
    - Request cost computation
    - Baseline cost estimation
    - Savings calculation (absolute and percentage)
    - Aggregation helpers for analytics
    """
    
    def __init__(self, default_baseline_model: str = DEFAULT_BASELINE_MODEL):
        """
        Initialize cost calculator.
        
        Args:
            default_baseline_model: Default model to use for baseline cost comparison
        """
        self.default_baseline_model = default_baseline_model
        
        # Validate default baseline model
        if default_baseline_model not in MODEL_PRICING:
            logger.warning(
                f"Default baseline model '{default_baseline_model}' not in pricing table, "
                f"using '{DEFAULT_BASELINE_MODEL}'"
            )
            self.default_baseline_model = DEFAULT_BASELINE_MODEL
        
        logger.info(f"CostCalculator initialized with baseline model: {self.default_baseline_model}")
    
    def compute_request_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Compute the estimated dollar cost for a single request using the given model.
        
        Args:
            model: Model name (e.g., "gpt-4o", "gpt-4o-mini")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Total cost in USD (rounded to 8 decimal places)
        """
        # Look up model pricing
        pricing = MODEL_PRICING.get(model)
        
        if not pricing:
            logger.warning(f"Model '{model}' not found in pricing table, returning 0.0")
            return 0.0
        
        # Extract pricing rates
        input_rate = pricing["input_per_1k"]
        output_rate = pricing["output_per_1k"]
        
        # Calculate costs
        input_cost = (input_tokens / 1000.0) * input_rate
        output_cost = (output_tokens / 1000.0) * output_rate
        total_cost = input_cost + output_cost
        
        # Round to 8 decimal places
        return round(total_cost, 8)
    
    def compute_baseline_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        baseline_model: Optional[str] = None
    ) -> float:
        """
        Compute the hypothetical cost if this request were processed entirely
        by a baseline model (e.g., gpt-4o).
        
        This represents the "naïve cost" if the user had routed everything
        through the baseline model without optimization.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            baseline_model: Baseline model to use (defaults to instance default)
        
        Returns:
            Baseline cost in USD (rounded to 8 decimal places)
        """
        # Use default baseline if not specified
        if baseline_model is None:
            baseline_model = self.default_baseline_model
        
        # Validate baseline model
        if baseline_model not in MODEL_PRICING:
            logger.warning(
                f"Baseline model '{baseline_model}' not found in pricing table, "
                f"using '{DEFAULT_BASELINE_MODEL}'"
            )
            baseline_model = DEFAULT_BASELINE_MODEL
        
        # Compute cost using baseline model pricing
        return self.compute_request_cost(
            model=baseline_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
    
    def compute_savings(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        baseline_model: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Compute cost savings by comparing actual model cost to baseline cost.
        
        Args:
            model: Actual model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            baseline_model: Baseline model for comparison (defaults to instance default)
        
        Returns:
            Dict with:
            {
                "actual_cost": float,
                "baseline_cost": float,
                "absolute_savings": float,
                "savings_pct": float
            }
        """
        # Compute actual cost
        actual_cost = self.compute_request_cost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Compute baseline cost
        baseline_cost = self.compute_baseline_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            baseline_model=baseline_model
        )
        
        # Compute savings
        absolute_savings = max(baseline_cost - actual_cost, 0.0)
        
        if baseline_cost > 0:
            savings_pct = (absolute_savings / baseline_cost) * 100.0
        else:
            savings_pct = 0.0
        
        # Round values
        actual_cost = round(actual_cost, 6)
        baseline_cost = round(baseline_cost, 6)
        absolute_savings = round(absolute_savings, 6)
        savings_pct = round(savings_pct, 2)
        
        logger.debug(
            f"Cost savings computed: model={model}, input_tokens={input_tokens}, "
            f"output_tokens={output_tokens}, actual_cost=${actual_cost}, "
            f"baseline_cost=${baseline_cost}, savings=${absolute_savings} ({savings_pct}%)"
        )
        
        return {
            "actual_cost": actual_cost,
            "baseline_cost": baseline_cost,
            "absolute_savings": absolute_savings,
            "savings_pct": savings_pct
        }
    
    def aggregate_savings(self, records: List[Dict[str, int]]) -> Dict[str, float]:
        """
        Aggregate savings across multiple request records.
        
        Args:
            records: List of records, each with:
                {
                    "model": str,
                    "input_tokens": int,
                    "output_tokens": int
                }
        
        Returns:
            Dict with aggregated totals:
            {
                "total_actual_cost": float,
                "total_baseline_cost": float,
                "total_absolute_savings": float,
                "avg_savings_pct": float
            }
        """
        if not records:
            return {
                "total_actual_cost": 0.0,
                "total_baseline_cost": 0.0,
                "total_absolute_savings": 0.0,
                "avg_savings_pct": 0.0
            }
        
        total_actual = 0.0
        total_baseline = 0.0
        total_absolute_savings = 0.0
        savings_pcts = []
        
        # Process each record
        for record in records:
            model = record.get("model")
            input_tokens = record.get("input_tokens", 0)
            output_tokens = record.get("output_tokens", 0)
            
            if not model:
                logger.warning("Record missing 'model' field, skipping")
                continue
            
            # Compute savings for this record
            savings = self.compute_savings(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            total_actual += savings["actual_cost"]
            total_baseline += savings["baseline_cost"]
            total_absolute_savings += savings["absolute_savings"]
            savings_pcts.append(savings["savings_pct"])
        
        # Calculate average savings percentage
        avg_savings_pct = sum(savings_pcts) / len(savings_pcts) if savings_pcts else 0.0
        
        # Round values
        total_actual = round(total_actual, 6)
        total_baseline = round(total_baseline, 6)
        total_absolute_savings = round(total_absolute_savings, 6)
        avg_savings_pct = round(avg_savings_pct, 2)
        
        logger.info(
            f"Aggregated savings: {len(records)} records, "
            f"total_actual=${total_actual}, total_baseline=${total_baseline}, "
            f"total_savings=${total_absolute_savings}, avg_savings_pct={avg_savings_pct}%"
        )
        
        return {
            "total_actual_cost": total_actual,
            "total_baseline_cost": total_baseline,
            "total_absolute_savings": total_absolute_savings,
            "avg_savings_pct": avg_savings_pct
        }
    
    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """
        Get pricing information for a model.
        
        Args:
            model: Model name
        
        Returns:
            Dict with 'input_per_1k' and 'output_per_1k' prices
        """
        pricing = MODEL_PRICING.get(model)
        
        if not pricing:
            logger.warning(f"Model '{model}' not found in pricing table")
            return {
                "input_per_1k": 0.0,
                "output_per_1k": 0.0,
                "provider": "unknown"
            }
        
        return {
            "input_per_1k": pricing["input_per_1k"],
            "output_per_1k": pricing["output_per_1k"],
            "provider": pricing["provider"]
        }
    
    def list_models(self) -> List[str]:
        """
        List all available models in the pricing table.
        
        Returns:
            List of model names
        """
        return list(MODEL_PRICING.keys())
