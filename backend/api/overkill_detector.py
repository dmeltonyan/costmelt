"""
Cost Melt - Production-Grade Overkill Detector

Multi-signal classifier that determines prompt complexity to route to
appropriate LLM models (0=simple, 1=medium, 2=complex).
"""

import re
import numpy as np
from typing import Dict, Any, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Example prompts for embedding-based similarity
SIMPLE_EXAMPLES = [
    "summarize this text",
    "rewrite this email",
    "give me synonyms",
    "explain this simply",
    "paraphrase this paragraph",
    "make this shorter",
    "what does this mean",
    "translate this"
]

COMPLEX_EXAMPLES = [
    "write a python function",
    "design a database schema",
    "optimize this algorithm",
    "debug this code",
    "derive a mathematical proof",
    "implement a neural network",
    "create a distributed system",
    "build a RAG pipeline"
]

# Keyword lists
SIMPLE_KEYWORDS = [
    "summarize", "rewrite", "paraphrase", "bullet points",
    "short answer", "explain briefly", "simplify", "synonyms",
    "translate", "make shorter", "what does", "define"
]

MEDIUM_KEYWORDS = [
    "sql", "mongodb", "csv", "json", "data cleaning",
    "marketing plan", "analysis", "optimize this",
    "email draft", "user story", "acceptance criteria",
    "describe", "explain how", "list", "compare"
]

COMPLEX_KEYWORDS = [
    "algorithm", "big o", "time complexity",
    "build a class", "python function", "debug this code",
    "financial model", "derivative", "proof", "chain of thought",
    "multi-step reasoning", "architecture", "design a system",
    "neural network", "rag pipeline", "transformer block",
    "implement", "create a", "build a", "develop"
]

# Regex patterns
CODE_PATTERNS = [
    r'```[\s\S]*?```',  # Code blocks
    r'def\s+\w+\s*\(',  # Python function
    r'function\s+\w+\s*\(',  # JavaScript function
    r'SELECT\s+.*\s+FROM',  # SQL query
    r'<html|<div|<script',  # HTML/JS
    r'\{[\s\S]*?\}',  # JSON structures
    r'class\s+\w+',  # Class definition
]

MATH_PATTERNS = [
    r'prove that',
    r'show that',
    r'derive',
    r'calculate',
    r'solve for [xyz]',
    r'minimize loss',
    r'maximize',
    r'equation',
    r'formula',
    r'integral',
    r'derivative',
    r'theorem',
    r'proof'
]

MULTISTEP_PATTERNS = [
    r'step\s+1[:\s]',
    r'step\s+2[:\s]',
    r'step\s+3[:\s]',
    r'first[,\s]',
    r'second[,\s]',
    r'third[,\s]',
    r'chain of thought',
    r'step by step',
    r'step-by-step'
]


class OverkillDetector:
    """
    Production-grade overkill detector using multiple signals.
    
    Complexity levels:
    0 = Simple: Basic Q&A, simple instructions, straightforward tasks
    1 = Medium: Multi-step reasoning, moderate context, structured output
    2 = Complex: Deep reasoning, extensive context, creative tasks, analysis
    """
    
    # Token count thresholds
    TOKEN_SIMPLE_THRESHOLD = 80
    TOKEN_MEDIUM_THRESHOLD = 250
    
    # Code detection threshold
    CODE_COMPLEX_THRESHOLD = 150  # tokens
    
    # Weight configuration (normalized to sum to ~2.0 for max complexity)
    WEIGHTS = {
        "token": 0.4,
        "keyword": 0.3,
        "code": 0.3,
        "math": 0.4,
        "multistep": 0.3,
        "embedding": 0.3
    }
    
    def __init__(self, embedding_client=None, token_counter=None):
        """
        Initialize overkill detector.
        
        Args:
            embedding_client: Client for computing embeddings (e.g., OpenAIClient)
            token_counter: Token counter instance (e.g., TokenCounter)
        """
        # Lazy imports to avoid circular dependencies
        if embedding_client is None:
            from services.openai_client import OpenAIClient
            self.embedding_client = OpenAIClient()
        else:
            self.embedding_client = embedding_client
        
        if token_counter is None:
            from utils.token_counter import TokenCounter
            self.token_counter = TokenCounter()
        else:
            self.token_counter = token_counter
        
        # Pre-compute embeddings for example prompts (cache)
        self._simple_embeddings: Optional[List[List[float]]] = None
        self._complex_embeddings: Optional[List[List[float]]] = None
        
        logger.info("OverkillDetector initialized")
    
    async def score(self, prompt: str) -> int:
        """
        Score prompt complexity using multi-signal analysis.
        
        Pipeline:
        1. Normalize prompt
        2. Token count
        3. Keyword detection
        4. Code detection
        5. Math/reasoning detection
        6. Multi-step detection
        7. Embedding similarity
        8. Weighted scoring
        9. Final classification
        
        Args:
            prompt: Prompt text to analyze
        
        Returns:
            Complexity score: 0 (simple), 1 (medium), or 2 (complex)
        """
        try:
            # Step 1: Normalize
            normalized = self._normalize(prompt)
            prompt_length = len(normalized)
            
            # Step 2: Token count
            token_count = self.token_counter.count(normalized)
            token_score = self._token_score(token_count)
            
            # Step 3: Keyword detection
            keyword_score = self._keyword_score(normalized)
            
            # Step 4: Code detection
            code_score, has_code, code_length = self._detect_code(normalized)
            
            # Step 5: Math/reasoning detection
            math_score = self._detect_math(normalized)
            
            # Step 6: Multi-step detection
            multistep_score = self._detect_multistep(normalized)
            
            # Step 7: Embedding similarity
            embedding_score = await self._embedding_complexity(normalized)
            
            # Step 8: Calculate final weighted score
            final_score = self._calculate_final_score(
                token_score=token_score,
                keyword_score=keyword_score,
                code_score=code_score,
                math_score=math_score,
                multistep_score=multistep_score,
                embedding_score=embedding_score
            )
            
            # Step 9: Final classification
            complexity = self._classify(final_score)
            
            # Log structured data
            logger.info(
                f"OverkillDetector: prompt_length={prompt_length}, "
                f"token_count={token_count}, token_score={token_score:.2f}, "
                f"keyword_score={keyword_score:.2f}, code_score={code_score:.2f} "
                f"(has_code={has_code}, code_length={code_length}), "
                f"math_score={math_score:.2f}, multistep_score={multistep_score:.2f}, "
                f"embedding_score={embedding_score:.2f}, final_score={final_score:.2f}, "
                f"complexity={complexity}"
            )
            
            return complexity
            
        except Exception as e:
            logger.error(f"Error in overkill detection: {e}", exc_info=True)
            # Fallback: use simple heuristic
            return self._heuristic_fallback(prompt)
    
    def _normalize(self, prompt: str) -> str:
        """
        Normalize prompt: strip whitespace, collapse spaces, lowercase.
        
        Args:
            prompt: Raw prompt text
        
        Returns:
            Normalized prompt string
        """
        # Strip leading/trailing whitespace
        normalized = prompt.strip()
        
        # Collapse multiple spaces
        normalized = re.sub(r' +', ' ', normalized)
        
        # Convert to lowercase for analysis
        normalized = normalized.lower()
        
        return normalized
    
    def _token_score(self, token_count: int) -> float:
        """
        Score based on token count.
        
        Thresholds:
        <80 tokens → 0.0 (simple)
        80-250 tokens → 0.5 (medium)
        >250 tokens → 1.0 (complex)
        
        Args:
            token_count: Number of tokens
        
        Returns:
            Score from 0.0 to 1.0
        """
        if token_count < self.TOKEN_SIMPLE_THRESHOLD:
            return 0.0
        elif token_count < self.TOKEN_MEDIUM_THRESHOLD:
            # Linear interpolation between 0.0 and 0.5
            ratio = (token_count - self.TOKEN_SIMPLE_THRESHOLD) / (
                self.TOKEN_MEDIUM_THRESHOLD - self.TOKEN_SIMPLE_THRESHOLD
            )
            return 0.5 * ratio
        else:
            # >250 tokens, scale from 0.5 to 1.0
            excess = token_count - self.TOKEN_MEDIUM_THRESHOLD
            # Cap at 1.0 for very long prompts
            return min(0.5 + (excess / 500.0), 1.0)
    
    def _keyword_score(self, prompt: str) -> float:
        """
        Score based on keyword detection.
        
        Simple keywords → -0.3 (reduce complexity)
        Medium keywords → +0.3
        Complex keywords → +0.8
        
        Args:
            prompt: Normalized prompt text
        
        Returns:
            Score from -0.3 to 0.8
        """
        score = 0.0
        
        # Check simple keywords (reduce complexity)
        simple_matches = sum(1 for kw in SIMPLE_KEYWORDS if kw in prompt)
        if simple_matches > 0:
            score -= 0.3 * min(simple_matches, 2) / 2  # Max -0.3
        
        # Check medium keywords
        medium_matches = sum(1 for kw in MEDIUM_KEYWORDS if kw in prompt)
        if medium_matches > 0:
            score += 0.3 * min(medium_matches, 3) / 3  # Max +0.3
        
        # Check complex keywords
        complex_matches = sum(1 for kw in COMPLEX_KEYWORDS if kw in prompt)
        if complex_matches > 0:
            score += 0.8 * min(complex_matches, 2) / 2  # Max +0.8
        
        return max(-0.3, min(0.8, score))  # Clamp between -0.3 and 0.8
    
    def _detect_code(self, prompt: str) -> tuple[float, bool, int]:
        """
        Detect code in prompt.
        
        Returns:
            Tuple of (score, has_code, code_length_tokens)
        """
        has_code = False
        code_length = 0
        
        # Check for code patterns
        for pattern in CODE_PATTERNS:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            if matches:
                has_code = True
                # Calculate total code length
                for match in matches:
                    code_length += self.token_counter.count(match)
                break
        
        if not has_code:
            return (0.0, False, 0)
        
        # If code detected
        if code_length > self.CODE_COMPLEX_THRESHOLD:
            return (1.0, True, code_length)  # Force complex
        else:
            return (0.5, True, code_length)  # Medium complexity
    
    def _detect_math(self, prompt: str) -> float:
        """
        Detect math/reasoning patterns.
        
        Args:
            prompt: Normalized prompt text
        
        Returns:
            Score (0.0 or 1.0)
        """
        for pattern in MATH_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                return 1.0  # Force complex
        
        return 0.0
    
    def _detect_multistep(self, prompt: str) -> float:
        """
        Detect multi-step instructions.
        
        Returns:
            Score based on number of steps:
            >= 3 steps → 1.0 (complex)
            >= 2 steps → 0.5 (medium, rounds up)
            < 2 steps → 0.0
        """
        step_count = 0
        
        # Count step markers
        for pattern in MULTISTEP_PATTERNS:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            step_count += len(matches)
        
        # Also count explicit "step N" patterns
        step_number_pattern = r'step\s+(\d+)'
        step_numbers = re.findall(step_number_pattern, prompt, re.IGNORECASE)
        if step_numbers:
            step_count = max(step_count, len(step_numbers))
        
        if step_count >= 3:
            return 1.0
        elif step_count >= 2:
            return 0.5  # Will round up to 1
        else:
            return 0.0
    
    async def _embedding_complexity(self, prompt: str) -> float:
        """
        Compute embedding-based complexity score.
        
        Compares prompt embedding to simple and complex example embeddings.
        If closer to complex → +1.0, if closer to simple → -0.3
        
        Args:
            prompt: Normalized prompt text
        
        Returns:
            Score from -0.3 to 1.0
        """
        try:
            # Get embedding for prompt
            result = await self.embedding_client.get_embedding(
                text=prompt,
                model="text-embedding-3-small"
            )
            prompt_embedding = np.array(result["embedding"])
            
            # Get or compute example embeddings
            if self._simple_embeddings is None:
                await self._load_example_embeddings()
            
            # Compute average similarity to simple examples
            simple_similarities = [
                self._cosine_similarity(prompt_embedding, np.array(emb))
                for emb in self._simple_embeddings
            ]
            avg_simple_sim = np.mean(simple_similarities) if simple_similarities else 0.0
            
            # Compute average similarity to complex examples
            complex_similarities = [
                self._cosine_similarity(prompt_embedding, np.array(emb))
                for emb in self._complex_embeddings
            ]
            avg_complex_sim = np.mean(complex_similarities) if complex_similarities else 0.0
            
            # Determine which is closer
            if avg_complex_sim > avg_simple_sim:
                # Closer to complex
                delta = avg_complex_sim - avg_simple_sim
                return min(1.0, 0.5 + delta * 2)  # Scale to 0.5-1.0
            else:
                # Closer to simple
                delta = avg_simple_sim - avg_complex_sim
                return max(-0.3, -0.3 * delta)  # Scale to -0.3-0.0
            
        except Exception as e:
            logger.warning(f"Error computing embedding complexity: {e}")
            return 0.0  # Neutral score on error
    
    async def _load_example_embeddings(self):
        """Load embeddings for example prompts (cache them)"""
        try:
            # Compute simple example embeddings
            self._simple_embeddings = []
            for example in SIMPLE_EXAMPLES:
                result = await self.embedding_client.get_embedding(
                    text=example,
                    model="text-embedding-3-small"
                )
                self._simple_embeddings.append(result["embedding"])
            
            # Compute complex example embeddings
            self._complex_embeddings = []
            for example in COMPLEX_EXAMPLES:
                result = await self.embedding_client.get_embedding(
                    text=example,
                    model="text-embedding-3-small"
                )
                self._complex_embeddings.append(result["embedding"])
            
            logger.debug(f"Loaded {len(self._simple_embeddings)} simple and "
                        f"{len(self._complex_embeddings)} complex example embeddings")
            
        except Exception as e:
            logger.error(f"Error loading example embeddings: {e}", exc_info=True)
            # Set empty lists to avoid repeated failures
            self._simple_embeddings = []
            self._complex_embeddings = []
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _calculate_final_score(
        self,
        token_score: float,
        keyword_score: float,
        code_score: float,
        math_score: float,
        multistep_score: float,
        embedding_score: float
    ) -> float:
        """
        Calculate weighted final complexity score.
        
        Args:
            token_score: Token-based score
            keyword_score: Keyword-based score
            code_score: Code detection score
            math_score: Math detection score
            multistep_score: Multi-step detection score
            embedding_score: Embedding-based score
        
        Returns:
            Final weighted score
        """
        # Normalize keyword score to 0-1 range (it can be negative)
        normalized_keyword = (keyword_score + 0.3) / 1.1  # Shift and scale
        
        # Normalize embedding score to 0-1 range (it can be negative)
        normalized_embedding = (embedding_score + 0.3) / 1.3  # Shift and scale
        
        # Weighted sum
        final_score = (
            self.WEIGHTS["token"] * token_score +
            self.WEIGHTS["keyword"] * normalized_keyword +
            self.WEIGHTS["code"] * code_score +
            self.WEIGHTS["math"] * math_score +
            self.WEIGHTS["multistep"] * multistep_score +
            self.WEIGHTS["embedding"] * normalized_embedding
        )
        
        return final_score
    
    def _classify(self, score: float) -> int:
        """
        Classify final score into complexity level.
        
        Args:
            score: Final weighted score
        
        Returns:
            Complexity level: 0, 1, or 2
        """
        if score < 1.0:
            return 0
        elif score < 2.0:
            return 1
        else:
            return 2
    
    def _heuristic_fallback(self, prompt: str) -> int:
        """
        Fallback heuristic when main detection fails.
        
        Args:
            prompt: Prompt text
        
        Returns:
            Complexity level (0, 1, or 2)
        """
        prompt_lower = prompt.lower()
        
        # Simple heuristics
        if any(kw in prompt_lower for kw in COMPLEX_KEYWORDS):
            return 2
        elif any(kw in prompt_lower for kw in MEDIUM_KEYWORDS):
            return 1
        else:
            return 0
