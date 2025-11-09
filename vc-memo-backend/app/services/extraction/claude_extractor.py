"""
Claude extractor for structured data extraction using Claude Sonnet 4.5.
Used in Plan C for complex extractions (team, company).
"""

from typing import Dict, Any, Optional
from anthropic import AsyncAnthropic
from app.core.config import get_claude_api_key
import json
import time


class ClaudeExtractor:
    """Extractor using Claude Sonnet 4.5 for structured data extraction"""

    def __init__(self):
        api_key = get_claude_api_key()
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"  # Claude Sonnet 4.5

    async def extract_json(
        self,
        text: str,
        extraction_prompt: str,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Extract structured JSON data from text using Claude.
        
        Args:
            text: Text to extract from
            extraction_prompt: Prompt template for extraction
            temperature: Temperature for generation
            
        Returns:
            Extracted data as dictionary
        """
        try:
            # Format prompt
            prompt = extraction_prompt.format(text=text)
            
            # Add JSON format requirement
            enhanced_prompt = f"""{prompt}

CRITICAL: You MUST return ONLY valid JSON. Do not include any markdown formatting, code blocks, or explanatory text. Return pure JSON only."""

            start_time = time.time()
            
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ]
            )
            
            elapsed = time.time() - start_time
            
            content = message.content[0].text if message.content else ""
            
            # Parse JSON (Claude may wrap in markdown)
            cleaned = content.strip()
            if cleaned.startswith("```"):
                # Remove markdown code blocks
                parts = cleaned.split("```")
                if len(parts) >= 2:
                    cleaned = parts[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"  → ⚠️  Claude JSON decode error: {e}", flush=True)
            print(f"  → Raw response: {content[:200]}...", flush=True)
            raise
        except Exception as e:
            print(f"  → ⚠️  Claude extraction error: {e}", flush=True)
            raise

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for Claude Sonnet 4.5.
        Pricing: $3/$15 per MTok (input/output) for prompts ≤ 200K tokens
        """
        input_cost = (input_tokens / 1_000_000) * 3.0
        output_cost = (output_tokens / 1_000_000) * 15.0
        return input_cost + output_cost

