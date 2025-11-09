"""
Plan A: OpenAI Structured Outputs (JSON Mode + Schema Enforcement)
Uses OpenAI's JSON mode to enforce exact schema compliance
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from app.core.models import (
    ProgressData,
    FinancialData,
    MarketData,
    CompanyData,
    TeamData,
    ExtractedData,
)
from app.utils.llm.rate_limiter import batch_process_with_rate_limit, RateLimiter
from app.utils.caching.summary_cache import SummaryCache
from app.utils.llm.token_counter import (
    count_tokens,
    estimate_cost,
    format_cost,
    format_tokens,
)
from app.utils.validation.json_schema import get_extraction_schema
from app.utils.validation.data_validator import DataValidator
from app.services.extraction.prompts import EXTRACTION_PROMPTS
from typing import List, Dict, Any, Type, Optional
import asyncio
import json
import tiktoken
import time
import sys


class ExtractorPlanA:
    """Plan A: Structured outputs with JSON mode and schema enforcement"""

    def __init__(self, cache_dir: str = "runtime/cache", use_cache: bool = True):
        # Use GPT-4o for ALL extractions to maximize quality
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        self.critical_types = ["financial", "progress", "market", "company", "team"]  # All critical in Plan A

        self.data_classes = {
            "progress": ProgressData,
            "financial": FinancialData,
            "market": MarketData,
            "company": CompanyData,
            "team": TeamData,
        }

        self.use_cache = use_cache
        self.cache = SummaryCache(cache_dir) if use_cache else None
        self.rate_limiter = RateLimiter(
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
        )
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.max_concurrent = 2

    async def _extract_from_chunk(
        self, doc: Document, extract_type: str
    ) -> Dict[str, Any]:
        """Extract data from a single chunk with JSON mode"""
        source_file = doc.metadata.get("source_file", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        
        token_stats = {
            "model": "gpt-4o",
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_hit": False,
        }

        # Get JSON schema for this extraction type
        try:
            json_schema = get_extraction_schema(extract_type)
        except Exception as e:
            print(f"  → ⚠️  Schema generation error: {e}, using basic JSON mode", flush=True)
            json_schema = None

        # Prepare prompt with schema information
        prompt_template = EXTRACTION_PROMPTS[extract_type]
        
        # Enhance prompt with schema information if available
        if json_schema:
            schema_str = json.dumps(json_schema, indent=2)
            # Escape curly braces for ChatPromptTemplate by doubling them
            # In f-strings, {{ becomes {, which ChatPromptTemplate will treat as literal
            schema_str_escaped = schema_str.replace("{", "{{").replace("}", "}}")
            enhanced_prompt = prompt_template + f"""

CRITICAL: You MUST return valid JSON that matches this exact schema:
{schema_str_escaped}

The JSON must conform to this schema exactly. All field types must match."""
        else:
            enhanced_prompt = prompt_template + """

CRITICAL: You MUST return valid JSON only. Use response_format={"type": "json_object"}."""

        prompt = ChatPromptTemplate.from_template(enhanced_prompt)

        # Limit input size
        max_input_tokens = 4000
        chunk_content = doc.page_content

        chunk_tokens = count_tokens(chunk_content, "gpt-4o")
        if chunk_tokens > max_input_tokens:
            sentences = chunk_content.split(". ")
            truncated = []
            current_tokens = 0
            for sent in sentences:
                sent_tokens = count_tokens(sent, "gpt-4o")
                if current_tokens + sent_tokens > max_input_tokens:
                    break
                truncated.append(sent)
                current_tokens += sent_tokens
            chunk_content = ". ".join(truncated) + "..."

        # Extract with JSON mode
        try:
            print(f"  → Processing with GPT-4O (Plan A: Structured Outputs)...", flush=True)
            start_time = time.time()
            
            # Use OpenAI's JSON mode by setting response_format
            # Note: LangChain may not directly support this, so we'll use the underlying client
            from openai import AsyncOpenAI
            import os
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Build messages
            messages = prompt.format_messages(text=chunk_content)
            # Convert LangChain messages to OpenAI format
            openai_messages = []
            for msg in messages:
                # Map LangChain message types to OpenAI roles
                role = "user"
                if hasattr(msg, 'type'):
                    if msg.type == "human":
                        role = "user"
                    elif msg.type == "system":
                        role = "system"
                    elif msg.type == "ai":
                        role = "assistant"
                    else:
                        role = "user"
                
                openai_messages.append({
                    "role": role,
                    "content": msg.content if hasattr(msg, 'content') else str(msg)
                })
            
            # Use lambda to ensure proper async handling
            async def create_completion():
                return await client.chat.completions.create(
                    model="gpt-4o",
                    messages=openai_messages,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
            
            response = await self.rate_limiter.execute(create_completion)
            
            elapsed = time.time() - start_time
            content = response.choices[0].message.content

            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            token_stats["input_tokens"] = input_tokens
            token_stats["output_tokens"] = output_tokens

            cost = estimate_cost(input_tokens, output_tokens, "gpt-4o")
            
            print(f"  → Output: {format_tokens(output_tokens)} tokens", flush=True)
            print(f"  → Time: {elapsed:.2f}s", flush=True)
            print(f"  → Cost: {format_cost(cost)}", flush=True)

            # Parse JSON response (should be valid due to JSON mode)
            result = json.loads(content)
            
            # Apply validation and fixing as backup
            result = self._validate_and_fix_result(result, extract_type)
            
            if isinstance(result, dict):
                result["_token_stats"] = token_stats
                result["_source_file"] = source_file
                result["_chunk_id"] = chunk_id

            print(f"  → ✅ Complete", flush=True)
            return result

        except json.JSONDecodeError as e:
            print(f"  → ⚠️  JSON decode error: {e}", flush=True)
            try:
                cleaned = content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                result = json.loads(cleaned)
                result = self._validate_and_fix_result(result, extract_type)
                return result
            except:
                return {}
        except Exception as e:
            source = doc.metadata.get("source_file", "unknown")
            print(f"Error extracting {extract_type} from {source}: {e}")
            import traceback
            print(traceback.format_exc())
            return {}

    def _validate_and_fix_result(self, result: Dict[str, Any], extract_type: str) -> Dict[str, Any]:
        """Apply validation and fixing as backup"""
        if not result:
            return result
        
        try:
            if extract_type == "progress":
                return DataValidator.fix_progress_data(result)
            elif extract_type == "team":
                return DataValidator.fix_team_data(result)
            elif extract_type == "financial":
                return DataValidator.fix_financial_data(result)
            elif extract_type == "market":
                return DataValidator.fix_market_data(result)
            elif extract_type == "company":
                return DataValidator.fix_company_data(result)
        except Exception as e:
            print(f"  → ⚠️  Validation error: {e}", flush=True)
            return result
        
        return result

    async def extract(
        self, documents: List[Document], extract_type: str
    ) -> ExtractedData:
        """Extract specific type of data from document chunks"""
        if extract_type not in EXTRACTION_PROMPTS:
            raise ValueError(f"Unknown extraction type: {extract_type}")

        if not documents:
            print(f"  ⚠ {extract_type}: No chunks assigned, skipping")
            return self.data_classes[extract_type]()

        print(f"  🔍 Extracting {extract_type} using GPT-4O (Plan A: Structured Outputs)")
        print(f"     Processing {len(documents)} chunks")

        extraction_start = time.time()
        input_tokens_total = 0
        output_tokens_total = 0
        cache_hits = 0

        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []

        async def process_doc(doc: Document):
            async with semaphore:
                result = await self._extract_from_chunk(doc, extract_type)
                if isinstance(result, dict) and "_token_stats" in result:
                    return result, result["_token_stats"]
                elif hasattr(result, "_token_stats"):
                    return result, result._token_stats
                return result, None

        tasks = [process_doc(doc) for doc in documents]
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for result_tuple in chunk_results:
            if isinstance(result_tuple, Exception):
                continue

            if isinstance(result_tuple, tuple) and len(result_tuple) == 2:
                result, token_stats = result_tuple
                if token_stats:
                    input_tokens_total += token_stats.get("input_tokens", 0)
                    output_tokens_total += token_stats.get("output_tokens", 0)
                    if token_stats.get("cache_hit", False):
                        cache_hits += 1
            else:
                result = result_tuple

            if result and isinstance(result, dict):
                valid_results.append(result)

        extraction_time = time.time() - extraction_start
        total_tokens = input_tokens_total + output_tokens_total
        cost = (input_tokens_total / 1_000_000 * 2.50) + (output_tokens_total / 1_000_000 * 10.00)

        print(f"     ✓ Completed in {extraction_time:.2f}s")
        print(f"     📊 {len(valid_results)} successful / {len(documents)} chunks")
        print(f"     🔄 Cache hits: {cache_hits}")
        print(f"     💾 Tokens: {input_tokens_total:,} in + {output_tokens_total:,} out = {total_tokens:,} total")
        print(f"     💰 Cost: ~${cost:.4f}")

        if not valid_results:
            return self.data_classes[extract_type]()

        # Import consolidation and confidence calculation from base extractor
        from app.services.extraction.base import OptimizedExtractor
        base_extractor = OptimizedExtractor()
        
        data_class = self.data_classes[extract_type]
        consolidated = base_extractor._consolidate_results(valid_results, data_class, documents)

        confidence, uncertainty_flags = base_extractor._calculate_confidence_with_consistency(
            valid_results, len(documents), extract_type
        )
        consolidated.confidence = confidence
        consolidated.uncertainty_flags = uncertainty_flags
        
        source_citations = base_extractor._build_source_citations(valid_results, extract_type)
        consolidated.source_citations = source_citations

        consolidated._extraction_stats = {
            "chunks_processed": len(documents),
            "successful_extractions": len(valid_results),
            "cache_hits": cache_hits,
            "input_tokens": input_tokens_total,
            "output_tokens": output_tokens_total,
            "total_tokens": total_tokens,
            "cost": cost,
            "time": extraction_time,
            "model": "gpt-4o",
        }

        return consolidated

