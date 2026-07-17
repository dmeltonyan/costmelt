"""
Cost Melt - Overkill Detector Tests

Test suite for the production-grade overkill detector.
"""

import pytest
import asyncio
import re
import numpy as np
from unittest.mock import Mock, AsyncMock
from typing import List


# Mock classes for testing
class MockEmbeddingClient:
    """Mock embedding client"""
    
    def __init__(self):
        self.embeddings = {}
        self.call_count = 0
    
    async def get_embedding(self, text: str, model: str = "text-embedding-3-small"):
        """Return mock embedding"""
        self.call_count += 1
        
        if text in self.embeddings:
            return {"embedding": self.embeddings[text]}
        
        # Generate mock embedding (1536 dimensions)
        # For testing, use simple patterns
        if any(kw in text.lower() for kw in ["python", "function", "code", "algorithm"]):
            # Complex-like embedding (all positive)
            embedding = [0.1] * 1536
        else:
            # Simple-like embedding (mixed)
            embedding = [0.05 if i % 2 == 0 else -0.05 for i in range(1536)]
        
        self.embeddings[text] = embedding
        return {"embedding": embedding}
    
    def set_embedding(self, text: str, embedding: List[float]):
        """Set custom embedding for text"""
        self.embeddings[text] = embedding


class MockTokenCounter:
    """Mock token counter"""
    
    def __init__(self):
        self.counts = {}
    
    def count(self, text: str) -> int:
        """Count tokens (simple approximation: 1 token ≈ 4 chars)"""
        if not text:
            return 0

        if text in self.counts:
            return self.counts[text]

        # OverkillDetector._normalize() lowercases and collapses whitespace
        # before code/pattern detection runs, so an exact-match lookup
        # against a raw string set via set_count() would miss the
        # normalized text that actually reaches this method. Fall back to
        # a whitespace/case-normalized substring match so tests can still
        # target specific snippets (e.g. code block contents).
        normalized_text = re.sub(r'\s+', ' ', text).strip().lower()
        for key, count in self.counts.items():
            normalized_key = re.sub(r'\s+', ' ', key).strip().lower()
            if normalized_key and normalized_key in normalized_text:
                return count

        # Simple approximation
        return len(text) // 4
    
    def set_count(self, text: str, count: int):
        """Set custom count for text"""
        self.counts[text] = count


@pytest.fixture
def mock_embedding_client():
    """Fixture for mock embedding client"""
    return MockEmbeddingClient()


@pytest.fixture
def mock_token_counter():
    """Fixture for mock token counter"""
    return MockTokenCounter()


@pytest.fixture
def overkill_detector(mock_embedding_client, mock_token_counter):
    """Fixture for overkill detector with mocks"""
    from api.overkill_detector import OverkillDetector
    
    return OverkillDetector(
        embedding_client=mock_embedding_client,
        token_counter=mock_token_counter
    )


@pytest.mark.asyncio
async def test_basic_simple_prompt(overkill_detector, mock_token_counter):
    """Test that basic simple prompts return class 0"""
    prompt = "Summarize this text"
    mock_token_counter.set_count(prompt, 5)  # Very short
    
    complexity = await overkill_detector.score(prompt)
    
    assert complexity == 0


@pytest.mark.asyncio
async def test_sql_prompt_medium(overkill_detector, mock_token_counter):
    """Test that SQL prompts return class 1"""
    prompt = "Write a SQL query to select all users from the database"
    mock_token_counter.set_count(prompt, 15)  # Medium length
    
    complexity = await overkill_detector.score(prompt)
    
    # Should be at least medium (1) due to SQL keyword
    assert complexity >= 1


@pytest.mark.asyncio
async def test_python_code_complex(overkill_detector, mock_token_counter):
    """Test that Python code prompts return class 2"""
    prompt = "Write a Python function to sort a list using quicksort algorithm"
    mock_token_counter.set_count(prompt, 20)
    
    complexity = await overkill_detector.score(prompt)
    
    # Should be complex (2) due to code keywords and algorithm
    assert complexity == 2


@pytest.mark.asyncio
async def test_long_reasoning_prompt_complex(overkill_detector, mock_token_counter):
    """Test that long reasoning prompts return class 2"""
    prompt = "Explain step by step how to derive the quadratic formula and prove that it works for all quadratic equations"
    mock_token_counter.set_count(prompt, 300)  # Long prompt
    
    complexity = await overkill_detector.score(prompt)
    
    # Should be complex due to length, math keywords, and multi-step
    assert complexity == 2


@pytest.mark.asyncio
async def test_embeddings_shift_complexity(overkill_detector, mock_embedding_client, mock_token_counter):
    """Test that embeddings can shift complexity upward"""
    # Create a prompt that's borderline
    prompt = "Write a function"
    mock_token_counter.set_count(prompt, 5)  # Short
    
    # Set embedding to be similar to complex examples
    complex_embedding = [0.1] * 1536
    mock_embedding_client.set_embedding(prompt, complex_embedding)
    
    complexity = await overkill_detector.score(prompt)
    
    # Should be at least medium due to embedding similarity
    assert complexity >= 1


@pytest.mark.asyncio
async def test_multistep_instructions(overkill_detector, mock_token_counter):
    """Test multi-step instruction detection"""
    prompt = "Step 1: Analyze the data. Step 2: Create a model. Step 3: Validate results."
    mock_token_counter.set_count(prompt, 20)
    
    complexity = await overkill_detector.score(prompt)
    
    # Should be complex (2) due to 3+ steps
    assert complexity == 2


@pytest.mark.asyncio
async def test_math_proof_detection(overkill_detector, mock_token_counter):
    """Test math proof detection"""
    prompt = "Prove that the sum of angles in a triangle equals 180 degrees"
    mock_token_counter.set_count(prompt, 15)
    
    complexity = await overkill_detector.score(prompt)
    
    # Should be complex (2) due to "prove that"
    assert complexity == 2


@pytest.mark.asyncio
async def test_code_block_detection(overkill_detector, mock_token_counter):
    """Test code block detection"""
    prompt = "Here is some code:\n```python\ndef hello():\n    print('world')\n```"
    mock_token_counter.set_count(prompt, 10)
    # Set code block to be long
    mock_token_counter.set_count("def hello():\n    print('world')", 200)  # Long code
    
    complexity = await overkill_detector.score(prompt)
    
    # Should be complex due to long code block
    assert complexity == 2


@pytest.mark.asyncio
async def test_token_count_scoring(overkill_detector, mock_token_counter):
    """Test token count scoring"""
    # Very short prompt
    prompt1 = "Hi"
    mock_token_counter.set_count(prompt1, 2)
    complexity1 = await overkill_detector.score(prompt1)
    assert complexity1 == 0  # Should be simple
    
    # Medium length prompt
    prompt2 = "Explain how machine learning works in detail with examples"
    mock_token_counter.set_count(prompt2, 150)
    complexity2 = await overkill_detector.score(prompt2)
    assert complexity2 >= 0  # At least simple, likely medium
    
    # Very long prompt
    prompt3 = "A" * 2000  # Very long
    mock_token_counter.set_count(prompt3, 500)
    complexity3 = await overkill_detector.score(prompt3)
    assert complexity3 >= 1  # Should be at least medium


@pytest.mark.asyncio
async def test_keyword_detection(overkill_detector, mock_token_counter):
    """Test keyword-based scoring"""
    # Simple keyword
    prompt1 = "Summarize this text"
    mock_token_counter.set_count(prompt1, 5)
    complexity1 = await overkill_detector.score(prompt1)
    assert complexity1 == 0
    
    # Complex keyword
    prompt2 = "Design a neural network architecture"
    mock_token_counter.set_count(prompt2, 10)
    complexity2 = await overkill_detector.score(prompt2)
    assert complexity2 == 2


@pytest.mark.asyncio
async def test_normalize_prompt(overkill_detector):
    """Test prompt normalization"""
    prompt = "  This   has    multiple    spaces  "
    
    normalized = overkill_detector._normalize(prompt)
    
    assert "  " not in normalized  # No double spaces
    assert normalized == normalized.lower()  # Lowercase
    assert normalized.strip() == normalized  # No leading/trailing whitespace


def test_token_score_calculation(overkill_detector):
    """Test token score calculation"""
    # Very short
    score1 = overkill_detector._token_score(50)
    assert score1 == 0.0
    
    # Medium
    score2 = overkill_detector._token_score(150)
    assert 0.0 < score2 < 0.5
    
    # Long
    score3 = overkill_detector._token_score(300)
    assert score3 > 0.5


def test_keyword_score_calculation(overkill_detector):
    """Test keyword score calculation"""
    # Simple keyword
    score1 = overkill_detector._keyword_score("summarize this")
    assert score1 < 0  # Negative (reduces complexity)
    
    # Complex keyword
    score2 = overkill_detector._keyword_score("design a neural network")
    assert score2 > 0  # Positive (increases complexity)


def test_code_detection(overkill_detector, mock_token_counter):
    """Test code detection"""
    # No code
    score1, has_code1, _ = overkill_detector._detect_code("just text")
    assert has_code1 is False
    assert score1 == 0.0
    
    # Has code
    prompt2 = "Here is code:\n```python\ndef x():\n    pass\n```"
    mock_token_counter.set_count("def x():\n    pass", 10)  # Short code
    score2, has_code2, _ = overkill_detector._detect_code(prompt2)
    assert has_code2 is True
    assert score2 > 0


def test_math_detection(overkill_detector):
    """Test math pattern detection"""
    # No math
    score1 = overkill_detector._detect_math("just text")
    assert score1 == 0.0
    
    # Has math
    score2 = overkill_detector._detect_math("prove that 1+1=2")
    assert score2 == 1.0


def test_multistep_detection(overkill_detector):
    """Test multi-step detection"""
    # No steps
    score1 = overkill_detector._detect_multistep("single instruction")
    assert score1 == 0.0
    
    # 2 steps
    score2 = overkill_detector._detect_multistep("Step 1: do this. Step 2: do that.")
    assert score2 == 0.5
    
    # 3+ steps
    score3 = overkill_detector._detect_multistep("Step 1: a. Step 2: b. Step 3: c.")
    assert score3 == 1.0


@pytest.mark.asyncio
async def test_embedding_complexity(overkill_detector, mock_embedding_client):
    """Test embedding-based complexity"""
    # Load example embeddings first
    await overkill_detector._load_example_embeddings()
    
    # Simple prompt
    prompt1 = "summarize this"
    embedding1 = await mock_embedding_client.get_embedding(prompt1)
    score1 = await overkill_detector._embedding_complexity(prompt1)
    assert score1 <= 0.5  # Should lean simple
    
    # Complex prompt
    prompt2 = "write a python function"
    embedding2 = await mock_embedding_client.get_embedding(prompt2)
    score2 = await overkill_detector._embedding_complexity(prompt2)
    assert score2 >= 0.5  # Should lean complex


def test_final_classification(overkill_detector):
    """Test final classification"""
    assert overkill_detector._classify(0.5) == 0
    assert overkill_detector._classify(1.5) == 1
    assert overkill_detector._classify(2.5) == 2


@pytest.mark.asyncio
async def test_error_handling(overkill_detector, mock_embedding_client):
    """Test error handling when embedding fails"""
    # Make embedding client raise exception
    async def failing_embed(text, model):
        raise Exception("Embedding failed")
    
    mock_embedding_client.get_embedding = failing_embed
    
    prompt = "Test prompt"
    complexity = await overkill_detector.score(prompt)
    
    # Should still return a valid complexity (fallback)
    assert complexity in [0, 1, 2]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

