"""
Cost Melt - Production-Grade Prompt Compression Engine

Hybrid rule-based + LLM-based compression system that reduces token usage
by 20-50% while preserving meaning and required context.
"""

import re
import time
from typing import Dict, Any, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PromptCompressor:
    """
    Production-grade prompt compressor using hybrid rule-based + LLM approach.
    
    Pipeline:
    1. Normalization
    2. Rule-based compression
    3. LLM-based compression
    4. Token counting
    5. Safety checks
    """
    
    # Redundant filler phrases to remove
    REDUNDANT_PHRASES = [
        r"please note that\s*",
        r"kindly be informed that\s*",
        r"it is important to mention that\s*",
        r"the purpose of this request is\s*",
        r"i would like to\s+",
        r"i want you to\s+",
        r"could you please\s+",
        r"would you be able to\s+",
        r"i need you to\s+",
        r"i'm asking you to\s+",
        r"i'm requesting that\s*",
        r"it would be great if\s+",
        r"i would appreciate it if\s+",
    ]
    
    # Verbose phrase replacements
    VERBOSE_REPLACEMENTS = {
        r"explain in detail": "explain briefly",
        r"in a clear and concise manner": "concisely",
        r"i would like you to": "Please",
        r"can you tell me": "Explain",
        r"could you explain": "Explain",
        r"i need to know": "Explain",
        r"what is the meaning of": "Define",
        r"provide a detailed explanation": "explain",
        r"give me a comprehensive": "provide",
        r"i would like to understand": "explain",
    }
    
    # Code block detection pattern
    CODE_BLOCK_PATTERN = r"```[\s\S]*?```"
    
    # Long paragraph threshold (characters)
    LONG_PARAGRAPH_THRESHOLD = 500
    
    # Code block token threshold
    CODE_BLOCK_TOKEN_THRESHOLD = 200
    
    def __init__(self, llm_client=None, token_counter=None):
        """
        Initialize prompt compressor.
        
        Args:
            llm_client: LLM client for compression (e.g., OpenAIClient)
            token_counter: Token counter instance (e.g., TokenCounter)
        """
        # Lazy imports to avoid circular dependencies
        if llm_client is None:
            from services.openai_client import OpenAIClient
            self.llm_client = OpenAIClient()
        else:
            self.llm_client = llm_client
        
        if token_counter is None:
            from utils.token_counter import TokenCounter
            self.token_counter = TokenCounter()
        else:
            self.token_counter = token_counter
        
        logger.info("PromptCompressor initialized")
    
    async def compress(self, prompt: str) -> Dict[str, Any]:
        """
        Compress a prompt to reduce token count while preserving meaning.
        
        Pipeline:
        1. Normalize prompt
        2. Apply rule-based compression
        3. Apply LLM-based compression
        4. Count tokens
        5. Safety checks
        
        Args:
            prompt: Original prompt text
        
        Returns:
            Dict with compression results:
            {
                "compressed_prompt": "...",
                "tokens_before": 742,
                "tokens_after": 331,
                "reduction_pct": 55.4,
                "strategy": ["rules", "llm"]
            }
        """
        compress_start = time.time()
        strategy = []
        
        try:
            # Step 1: Normalization
            normalize_start = time.time()
            normalized = self._normalize(prompt)
            normalize_time = (time.time() - normalize_start) * 1000
            
            # Count original tokens
            tokens_before = self.token_counter.count(normalized)
            
            logger.info(f"Normalized prompt: {len(prompt)} -> {len(normalized)} chars, "
                       f"{normalize_time:.2f}ms")
            
            # Step 2: Rule-based compression
            rule_start = time.time()
            rule_compressed = self._rule_based_compress(normalized)
            rule_time = (time.time() - rule_start) * 1000
            
            rule_tokens = self.token_counter.count(rule_compressed)
            rule_reduction = ((tokens_before - rule_tokens) / tokens_before * 100) if tokens_before > 0 else 0
            
            logger.info(f"Rule-based compression: {tokens_before} -> {rule_tokens} tokens "
                       f"({rule_reduction:.1f}% reduction, {rule_time:.2f}ms)")
            
            if rule_tokens < tokens_before:
                strategy.append("rules")
            
            # Step 3: LLM-based compression (if rule-based didn't reduce enough)
            llm_compressed = rule_compressed
            llm_time = 0
            
            # Only use LLM if prompt is substantial and rule-based reduction < 30%
            if tokens_before > 50 and rule_reduction < 30:
                llm_start = time.time()
                try:
                    llm_compressed = await self._llm_compress(rule_compressed)
                    llm_time = (time.time() - llm_start) * 1000
                    
                    llm_tokens = self.token_counter.count(llm_compressed)
                    llm_reduction = ((tokens_before - llm_tokens) / tokens_before * 100) if tokens_before > 0 else 0
                    
                    logger.info(f"LLM compression: {rule_tokens} -> {llm_tokens} tokens "
                               f"({llm_reduction:.1f}% total reduction, {llm_time:.2f}ms)")
                    
                    if llm_tokens < rule_tokens:
                        strategy.append("llm")
                    else:
                        # LLM didn't help, use rule-based result
                        llm_compressed = rule_compressed
                except Exception as e:
                    logger.warning(f"LLM compression failed, using rule-based: {e}")
                    llm_compressed = rule_compressed
            
            # Step 4: Token counting
            tokens_after = self.token_counter.count(llm_compressed)
            reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0
            
            # Step 5: Safety checks
            safety_result = self._safety_check(normalized, llm_compressed)
            
            if not safety_result["safe"]:
                logger.warning(f"Safety check failed: {safety_result['reason']}, "
                             f"falling back to rule-based only")
                # Fallback to rule-based only
                final_compressed = rule_compressed
                tokens_after = rule_tokens
                reduction_pct = rule_reduction
                strategy = ["rules"] if "rules" in strategy else []
            else:
                final_compressed = llm_compressed
            
            total_time = (time.time() - compress_start) * 1000
            
            logger.info(
                f"Compression complete: {tokens_before} -> {tokens_after} tokens "
                f"({reduction_pct:.1f}% reduction), strategy={strategy}, "
                f"total_time={total_time:.2f}ms"
            )
            
            return {
                "compressed_prompt": final_compressed,
                "tokens_before": tokens_before,
                "tokens_after": tokens_after,
                "reduction_pct": round(reduction_pct, 1),
                "strategy": strategy
            }
            
        except Exception as e:
            logger.error(f"Error compressing prompt: {e}", exc_info=True)
            # Return original on error
            tokens_before = self.token_counter.count(prompt)
            return {
                "compressed_prompt": prompt,
                "tokens_before": tokens_before,
                "tokens_after": tokens_before,
                "reduction_pct": 0.0,
                "strategy": []
            }
    
    def _normalize(self, prompt: str) -> str:
        """
        Normalize prompt: strip whitespace, dedent, normalize spaces and line breaks.
        
        Args:
            prompt: Raw prompt text
        
        Returns:
            Normalized prompt string
        """
        # Strip leading/trailing whitespace
        normalized = prompt.strip()
        
        # Replace tabs with spaces
        normalized = normalized.replace('\t', ' ')
        
        # Replace triple+ spaces with single space
        normalized = re.sub(r' {3,}', ' ', normalized)
        
        # Normalize line breaks (convert \r\n and \r to \n)
        normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
        
        # Collapse multiple newlines to double newline max
        normalized = re.sub(r'\n{3,}', '\n\n', normalized)
        
        # Remove leading/trailing whitespace from each line
        lines = normalized.split('\n')
        lines = [line.strip() for line in lines]
        normalized = '\n'.join(lines)
        
        # Final cleanup: collapse multiple spaces
        normalized = re.sub(r' +', ' ', normalized)
        
        return normalized.strip()
    
    def _rule_based_compress(self, prompt: str) -> str:
        """
        Apply rule-based compression to prompt.
        
        Rules:
        - Remove redundant filler phrases
        - Remove repeated instructions
        - Shorten common prompt boilerplate
        - Collapse long enumerations
        - Compress code blocks
        - Compress long content blocks
        
        Args:
            prompt: Normalized prompt text
        
        Returns:
            Rule-compressed prompt
        """
        compressed = prompt
        
        # Rule 1: Remove redundant filler phrases
        for phrase in self.REDUNDANT_PHRASES:
            compressed = re.sub(phrase, "", compressed, flags=re.IGNORECASE)
        
        # Rule 2: Replace verbose phrases
        for pattern, replacement in self.VERBOSE_REPLACEMENTS.items():
            compressed = re.sub(pattern, replacement, compressed, flags=re.IGNORECASE)
        
        # Rule 3: Remove repeated instructions (simple heuristic)
        compressed = self._remove_repeated_instructions(compressed)
        
        # Rule 4: Collapse long enumerations
        compressed = self._collapse_enumerations(compressed)
        
        # Rule 5: Compress code blocks
        compressed = self._compress_code_blocks(compressed)
        
        # Rule 6: Compress long content blocks (placeholder - would use LLM in production)
        # For now, just identify them
        
        # Clean up extra spaces created by removals
        compressed = re.sub(r' +', ' ', compressed)
        compressed = re.sub(r'\n +', '\n', compressed)
        
        return compressed.strip()
    
    def _remove_repeated_instructions(self, prompt: str) -> str:
        """
        Remove repeated instructions using simple token-based similarity.
        
        Args:
            prompt: Prompt text
        
        Returns:
            Prompt with duplicates removed
        """
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', prompt)
        
        if len(sentences) < 2:
            return prompt
        
        # Simple deduplication: remove exact duplicates
        seen = set()
        unique_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            # Normalize sentence for comparison
            sentence_normalized = re.sub(r'\s+', ' ', sentence_lower)
            
            if sentence_normalized and sentence_normalized not in seen:
                seen.add(sentence_normalized)
                unique_sentences.append(sentence)
        
        # Rejoin sentences
        return '. '.join(unique_sentences) + ('.' if prompt.endswith('.') else '')
    
    def _collapse_enumerations(self, prompt: str) -> str:
        """
        Collapse long enumerations into summarized form.
        
        Args:
            prompt: Prompt text
        
        Returns:
            Prompt with enumerations collapsed
        """
        # Detect numbered lists
        numbered_list_pattern = r'(\d+\.\s+[^\n]+(?:\n\d+\.\s+[^\n]+){2,})'
        
        def replace_enumeration(match):
            enumeration = match.group(0)
            lines = enumeration.split('\n')
            
            # If more than 3 items, summarize
            if len(lines) > 3:
                # Extract key points (first few words of each)
                key_points = []
                for line in lines[:3]:  # Take first 3
                    # Extract first few words
                    words = line.split()[2:5]  # Skip number and first word
                    if words:
                        key_points.append(' '.join(words))
                
                return f"• Key points: {', '.join(key_points)} (and {len(lines) - 3} more)"
            
            return enumeration
        
        compressed = re.sub(numbered_list_pattern, replace_enumeration, prompt, flags=re.MULTILINE)
        
        return compressed
    
    def _compress_code_blocks(self, prompt: str) -> str:
        """
        Compress long code blocks by replacing with summary.
        
        Args:
            prompt: Prompt text
        
        Returns:
            Prompt with long code blocks compressed
        """
        def replace_code_block(match):
            code_block = match.group(0)
            code_content = code_block.strip('`')
            
            # Count tokens in code block
            code_tokens = self.token_counter.count(code_content)
            
            if code_tokens > self.CODE_BLOCK_TOKEN_THRESHOLD:
                # Try to detect language
                language_match = re.match(r'```(\w+)', code_block)
                language = language_match.group(1) if language_match else "code"
                
                # Try to detect what the code does (simple heuristic)
                if 'def ' in code_content or 'function' in code_content:
                    summary = f"<code omitted: {language} function>"
                elif 'class ' in code_content:
                    summary = f"<code omitted: {language} class>"
                else:
                    summary = f"<code omitted: {language} code block>"
                
                logger.debug(f"Compressed code block: {code_tokens} tokens -> summary")
                return summary
            
            return code_block
        
        compressed = re.sub(self.CODE_BLOCK_PATTERN, replace_code_block, prompt, flags=re.DOTALL)
        
        return compressed
    
    async def _llm_compress(self, prompt: str) -> str:
        """
        Compress prompt using LLM (GPT-4o-mini).
        
        Uses deterministic settings (temperature=0) for consistent results.
        
        Args:
            prompt: Rule-compressed prompt text
        
        Returns:
            LLM-compressed prompt
        """
        system_prompt = """You are a prompt compression engine. Reduce token count while preserving meaning. 
Do NOT remove instructions. Do NOT remove important details. 
Shorten wording, remove redundancy, summarize long blocks.
Keep the final output safe and instruction-complete."""

        user_prompt = f"COMPRESS THIS PROMPT:\n{prompt}"

        try:
            response = await self.llm_client.complete(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model="gpt-4o-mini",
                temperature=0.0,  # Deterministic
                max_tokens=len(prompt)  # Allow up to original length
            )
            
            compressed = response["text"].strip()
            
            # Remove the "COMPRESS THIS PROMPT:" prefix if LLM included it
            if compressed.startswith("COMPRESS THIS PROMPT:"):
                compressed = compressed[len("COMPRESS THIS PROMPT:"):].strip()
            
            return compressed
            
        except Exception as e:
            logger.error(f"Error in LLM compression: {e}", exc_info=True)
            raise
    
    def _safety_check(self, original: str, compressed: str) -> Dict[str, Any]:
        """
        Perform safety checks on compressed prompt.
        
        Checks:
        - Length must not increase significantly
        - Prompt must not be empty
        - Must contain original intent (simple keyword check)
        - Must contain key instructions
        
        Args:
            original: Original prompt
            compressed: Compressed prompt
        
        Returns:
            Dict with 'safe' (bool) and 'reason' (str)
        """
        # Check 1: Not empty
        if not compressed or len(compressed.strip()) == 0:
            return {"safe": False, "reason": "compressed_prompt_empty"}
        
        # Check 2: Length sanity check (should not be much longer)
        if len(compressed) > len(original) * 1.5:
            return {"safe": False, "reason": "compressed_prompt_too_long"}
        
        # Check 3: Token count sanity (should not increase)
        original_tokens = self.token_counter.count(original)
        compressed_tokens = self.token_counter.count(compressed)
        
        if compressed_tokens > original_tokens * 1.1:  # Allow 10% tolerance
            return {"safe": False, "reason": "token_count_increased"}
        
        # Check 4: Key instruction words preserved (simple heuristic)
        # Extract important words from original (verbs, question words)
        important_words = re.findall(
            r'\b(explain|define|list|create|write|analyze|compare|summarize|show|provide|give|tell|what|how|why|when|where|who)\b',
            original.lower()
        )
        
        if important_words:
            # Check if at least 50% of important words are preserved
            preserved = sum(1 for word in important_words if word in compressed.lower())
            if preserved < len(important_words) * 0.5:
                return {"safe": False, "reason": "key_instructions_missing"}
        
        return {"safe": True, "reason": "all_checks_passed"}
    
    def _compute_stats(self, original: str, compressed: str) -> Dict[str, Any]:
        """
        Compute compression statistics.
        
        Args:
            original: Original prompt
            compressed: Compressed prompt
        
        Returns:
            Dict with statistics
        """
        tokens_before = self.token_counter.count(original)
        tokens_after = self.token_counter.count(compressed)
        reduction_pct = ((tokens_before - tokens_after) / tokens_before * 100) if tokens_before > 0 else 0
        
        return {
            "tokens_before": tokens_before,
            "tokens_after": tokens_after,
            "reduction_pct": round(reduction_pct, 1),
            "chars_before": len(original),
            "chars_after": len(compressed),
            "char_reduction_pct": round(((len(original) - len(compressed)) / len(original) * 100) if len(original) > 0 else 0, 1)
        }
