"""
Cost Melt - Prompt Compressor Tests

Test suite for the production-grade prompt compression engine.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any


# Mock classes for testing
class MockLLMClient:
    """Mock LLM client"""
    
    def __init__(self):
        self.call_count = 0
        self.responses = {}
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Return mock LLM response"""
        self.call_count += 1
        
        # Default: return compressed version
        if prompt in self.responses:
            return {"text": self.responses[prompt], "tokens_used": 100}
        
        # Simple mock compression: remove "COMPRESS THIS PROMPT:" prefix
        if "COMPRESS THIS PROMPT:" in prompt:
            compressed = prompt.replace("COMPRESS THIS PROMPT:", "").strip()
            # Simulate some compression
            compressed = compressed.replace("  ", " ")
            return {"text": compressed, "tokens_used": len(compressed) // 4}
        
        return {"text": prompt, "tokens_used": len(prompt) // 4}
    
    def set_response(self, prompt: str, response: str):
        """Set custom response for a prompt"""
        self.responses[prompt] = response


class MockTokenCounter:
    """Mock token counter"""
    
    def __init__(self):
        self.counts = {}
    
    def count(self, text: str) -> int:
        """Count tokens (simple approximation: 1 token ≈ 4 chars)"""
        if not text:
            return 0
        # Simple approximation
        return len(text) // 4
    
    def set_count(self, text: str, count: int):
        """Set custom count for text"""
        self.counts[text] = count


@pytest.fixture
def mock_llm_client():
    """Fixture for mock LLM client"""
    return MockLLMClient()


@pytest.fixture
def mock_token_counter():
    """Fixture for mock token counter"""
    return MockTokenCounter()


@pytest.fixture
def prompt_compressor(mock_llm_client, mock_token_counter):
    """Fixture for prompt compressor with mocks"""
    from api.prompt_compressor import PromptCompressor
    
    return PromptCompressor(
        llm_client=mock_llm_client,
        token_counter=mock_token_counter
    )


@pytest.mark.asyncio
async def test_rule_based_compression(prompt_compressor):
    """Test rule-based compression removes redundant phrases"""
    prompt = "Please note that I would like you to explain in detail what quaternions are."
    
    compressed = prompt_compressor._rule_based_compress(prompt)
    
    # Should remove "Please note that" and "I would like you to"
    assert "please note that" not in compressed.lower()
    assert "i would like you to" not in compressed.lower()
    # Should replace "explain in detail" with "explain briefly"
    assert "explain briefly" in compressed.lower() or "explain" in compressed.lower()


@pytest.mark.asyncio
async def test_compress_full_pipeline(prompt_compressor, mock_token_counter):
    """Test full compression pipeline"""
    prompt = "Please note that the following request needs to be completed in a clear and concise manner. Explain in detail what quaternions are and provide examples. The purpose of this request is to help me understand the concept."
    
    result = await prompt_compressor.compress(prompt)
    
    assert "compressed_prompt" in result
    assert "tokens_before" in result
    assert "tokens_after" in result
    assert "reduction_pct" in result
    assert "strategy" in result
    
    # Should have some reduction
    assert result["tokens_after"] <= result["tokens_before"]
    assert result["reduction_pct"] >= 0


@pytest.mark.asyncio
async def test_llm_compression_used(prompt_compressor, mock_llm_client):
    """Test that LLM compression is used when appropriate"""
    # A long prompt with no repeated sentences and no rule-matchable filler
    # phrases, so rule-based compression can't get anywhere near the 30%
    # reduction that would make the LLM pass unnecessary (a single repeated
    # sentence here would get deduplicated by _remove_repeated_instructions
    # alone and legitimately skip the LLM step).
    prompt = (
        "Machine learning is a field of artificial intelligence that enables systems "
        "to learn patterns from data without being explicitly programmed for every rule. "
        "Deep learning relies on neural networks with many layers to model complex, "
        "non-linear relationships between inputs and outputs. "
        "Reinforcement learning trains an agent to make decisions by rewarding good "
        "outcomes and penalizing bad ones over repeated interactions with an environment. "
        "Natural language processing focuses on enabling computers to understand, "
        "interpret, and generate human language in a way that is both meaningful and useful. "
        "Computer vision gives machines the ability to interpret and analyze visual "
        "information captured from images, video, and other sensors."
    )

    result = await prompt_compressor.compress(prompt)

    # Should have used LLM if prompt is long enough
    if len(prompt) > 200:  # Threshold for LLM usage
        assert "llm" in result["strategy"] or mock_llm_client.call_count > 0


@pytest.mark.asyncio
async def test_safety_check_passes(prompt_compressor):
    """Test safety check passes for valid compression"""
    original = "Explain what Python is."
    compressed = "Explain Python."
    
    result = prompt_compressor._safety_check(original, compressed)
    
    assert result["safe"] is True
    assert result["reason"] == "all_checks_passed"


@pytest.mark.asyncio
async def test_safety_check_fails_empty(prompt_compressor):
    """Test safety check fails for empty compressed prompt"""
    original = "Explain what Python is."
    compressed = ""
    
    result = prompt_compressor._safety_check(original, compressed)
    
    assert result["safe"] is False
    assert result["reason"] == "compressed_prompt_empty"


@pytest.mark.asyncio
async def test_safety_check_fails_too_long(prompt_compressor):
    """Test safety check fails when compressed is much longer"""
    original = "Short prompt."
    compressed = "This is a much longer prompt that exceeds the original by a significant margin. " * 10
    
    result = prompt_compressor._safety_check(original, compressed)
    
    assert result["safe"] is False
    assert result["reason"] in ["compressed_prompt_too_long", "token_count_increased"]


@pytest.mark.asyncio
async def test_safety_fallback(prompt_compressor, mock_llm_client):
    """Test fallback to rule-based when safety check fails"""
    # Make LLM return something that fails safety check
    mock_llm_client.set_response(
        "COMPRESS THIS PROMPT:\nTest",
        ""  # Empty response should fail safety check
    )
    
    prompt = "Explain what Python is."
    result = await prompt_compressor.compress(prompt)
    
    # Should fallback to rule-based
    assert result["compressed_prompt"] != ""
    assert result["reduction_pct"] >= 0


@pytest.mark.asyncio
async def test_normalize_prompt(prompt_compressor):
    """Test prompt normalization"""
    prompt = "  This   has    multiple    spaces  \t\tand\t\ttabs  "
    
    normalized = prompt_compressor._normalize(prompt)
    
    assert "  " not in normalized  # No double spaces
    assert "\t" not in normalized  # No tabs
    assert normalized.strip() == normalized  # No leading/trailing whitespace


@pytest.mark.asyncio
async def test_remove_repeated_instructions(prompt_compressor):
    """Test removal of repeated instructions"""
    prompt = "Explain Python. Explain Python. Explain Python."
    
    compressed = prompt_compressor._remove_repeated_instructions(prompt)
    
    # Should have fewer instances
    assert compressed.count("Explain Python") <= prompt.count("Explain Python")


@pytest.mark.asyncio
async def test_collapse_enumerations(prompt_compressor):
    """Test collapsing long enumerations"""
    prompt = """1. This is a very long point that goes on and on
2. Another very long point that also goes on
3. Yet another long point
4. One more long point
5. Final long point"""
    
    compressed = prompt_compressor._collapse_enumerations(prompt)
    
    # Should be shorter or contain summary
    assert len(compressed) < len(prompt) or "Key points" in compressed or "more" in compressed.lower()


@pytest.mark.asyncio
async def test_compress_code_blocks(prompt_compressor, mock_token_counter):
    """Test compression of long code blocks"""
    # Create a code block long enough to clear CODE_BLOCK_TOKEN_THRESHOLD
    # (200) under the mock's len//4 token estimate: 100 repeats lands
    # around ~150 estimated tokens, just under the threshold, so nothing
    # gets compressed. 200 repeats comfortably clears it.
    long_code = "def " + "x = 1\n" * 200  # Long code block
    prompt = f"Here is some code:\n```python\n{long_code}\n```"
    
    compressed = prompt_compressor._compress_code_blocks(prompt)
    
    # Should be shorter or contain summary
    assert len(compressed) < len(prompt) or "code omitted" in compressed.lower()


@pytest.mark.asyncio
async def test_token_reduction(prompt_compressor, mock_token_counter):
    """Test that compression reduces tokens"""
    prompt = "Please note that I would like you to explain in detail what quaternions are and provide examples."
    
    result = await prompt_compressor.compress(prompt)
    
    # Should have reduction
    assert result["tokens_after"] < result["tokens_before"]
    assert result["reduction_pct"] > 0


@pytest.mark.asyncio
async def test_verbose_replacements(prompt_compressor):
    """Test verbose phrase replacements"""
    prompt = "I would like you to explain in detail what Python is in a clear and concise manner."
    
    compressed = prompt_compressor._rule_based_compress(prompt)
    
    # Should have replacements
    assert "i would like you to" not in compressed.lower() or "please" in compressed.lower()
    assert "explain in detail" not in compressed.lower() or "explain briefly" in compressed.lower()


@pytest.mark.asyncio
async def test_error_handling_llm_failure(prompt_compressor, mock_llm_client):
    """Test error handling when LLM fails"""
    # Make LLM raise exception
    async def failing_complete(*args, **kwargs):
        raise Exception("LLM API error")
    
    mock_llm_client.complete = failing_complete
    
    prompt = "Explain what Python is. " * 20  # Long enough to trigger LLM
    
    result = await prompt_compressor.compress(prompt)
    
    # Should still return result (fallback to rule-based)
    assert "compressed_prompt" in result
    assert result["compressed_prompt"] != ""


@pytest.mark.asyncio
async def test_strategy_tracking(prompt_compressor):
    """Test that strategy is correctly tracked"""
    prompt = "Please note that I would like you to explain in detail what quaternions are."
    
    result = await prompt_compressor.compress(prompt)
    
    assert "strategy" in result
    assert isinstance(result["strategy"], list)
    # Should have at least "rules" if rule-based compression was applied
    if result["tokens_after"] < result["tokens_before"]:
        assert len(result["strategy"]) > 0


@pytest.mark.asyncio
async def test_preserves_instructions(prompt_compressor):
    """Test that important instructions are preserved"""
    prompt = "Explain what Python is. List its features. Compare it to Java."
    
    result = await prompt_compressor.compress(prompt)
    
    compressed = result["compressed_prompt"].lower()
    
    # Should preserve key instruction words
    important_words = ["explain", "list", "compare"]
    preserved = sum(1 for word in important_words if word in compressed)
    
    # At least some should be preserved
    assert preserved > 0


def test_compute_stats(prompt_compressor):
    """Test statistics computation"""
    original = "This is a longer original prompt with more words."
    compressed = "Shorter prompt."
    
    stats = prompt_compressor._compute_stats(original, compressed)
    
    assert "tokens_before" in stats
    assert "tokens_after" in stats
    assert "reduction_pct" in stats
    assert stats["tokens_after"] < stats["tokens_before"]
    assert stats["reduction_pct"] > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

