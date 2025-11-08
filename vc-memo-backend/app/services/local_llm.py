"""
Local LLM service using Ollama for cost-effective document processing.
Uses Ollama for non-critical extractions and document parsing.
"""

import os
import httpx
from typing import Optional, Dict, Any, List
import json
import time
import sys
from app.utils.token_counter import estimate_ollama_tokens, format_tokens


class LocalLLMService:
    """Service for interacting with Ollama local LLM"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2:3b"):
        """
        Initialize Ollama service
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model name to use (default: llama3.2:3b for cost efficiency)
        """
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
        
    async def check_availability(self) -> bool:
        """Check if Ollama is available and model is installed"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return any(self.model in name for name in model_names)
            return False
        except Exception as e:
            print(f"⚠ Ollama not available: {e}")
            return False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using Ollama
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Temperature for generation (default: 0.1 for accuracy)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            print(f"⚠ Ollama generation error: {e}")
            raise
    
    async def extract_json(
        self,
        text: str,
        extraction_prompt: str,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Extract structured data from text using Ollama
        
        Args:
            text: Text to extract from
            extraction_prompt: Prompt template for extraction
            temperature: Temperature for generation
            
        Returns:
            Extracted data as dictionary
        """
        system_prompt = """You are a precise data extraction assistant. Extract information from text and return ONLY valid JSON. Do not include any markdown formatting, explanations, or additional text. Return only the JSON object."""
        
        full_prompt = extraction_prompt.format(text=text)
        
        # Log Ollama call details
        input_tokens = estimate_ollama_tokens(full_prompt)
        print(f"    [OLLAMA] Calling {self.model}", flush=True)
        print(f"    [OLLAMA] Input: {format_tokens(input_tokens)} tokens", flush=True)
        
        try:
            start_time = time.time()
            response = await self.generate(
                prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=2000,  # Limit for structured output
            )
            elapsed = time.time() - start_time
            
            # Clean response - remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Remove markdown code blocks
                parts = cleaned.split("```")
                if len(parts) > 1:
                    cleaned = parts[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
            
            # Parse JSON
            result = json.loads(cleaned)
            output_tokens = estimate_ollama_tokens(json.dumps(result))
            
            print(f"    [OLLAMA] Output: {format_tokens(output_tokens)} tokens", flush=True)
            print(f"    [OLLAMA] Time: {elapsed:.2f}s", flush=True)
            print(f"    [OLLAMA] Cost: FREE (local processing)", flush=True)
            
            return result
        except json.JSONDecodeError as e:
            print(f"    [OLLAMA] ⚠ Failed to parse JSON: {e}", flush=True)
            print(f"    [OLLAMA] Response preview: {response[:200]}...", flush=True)
            return {}
        except Exception as e:
            print(f"    [OLLAMA] ⚠ Error: {e}", flush=True)
            return {}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance
_local_llm: Optional[LocalLLMService] = None


def get_local_llm() -> Optional[LocalLLMService]:
    """Get or create global Ollama service instance"""
    global _local_llm
    
    if _local_llm is None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        _local_llm = LocalLLMService(base_url=base_url, model=model)
    
    return _local_llm

