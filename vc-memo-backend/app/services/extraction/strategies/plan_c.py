"""
Plan C: Hybrid Model Strategy (GPT-4o + Claude Sonnet)
Uses Claude Sonnet 4.5 for complex extractions, GPT-4o for critical metrics
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
from app.utils.validation.data_validator import DataValidator
from app.services.extraction.claude_extractor import ClaudeExtractor
from app.services.extraction.prompts import EXTRACTION_PROMPTS
from app.core.config import get_claude_api_key
from typing import List, Dict, Any, Type, Optional
import asyncio
import json
import tiktoken
import time
import sys


class ExtractorPlanC:
    """Plan C: Hybrid model strategy with Claude and GPT-4o"""

    def __init__(self, cache_dir: str = "runtime/cache", use_cache: bool = True):
        # Use GPT-4o for critical extractions
        self.gpt4o_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        # Use GPT-4o-mini for simple extractions
        self.gpt4o_mini_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        
        # Initialize Claude extractor if API key available
        self.claude_extractor = None
        try:
            if get_claude_api_key():
                self.claude_extractor = ClaudeExtractor()
                print("  ✅ Claude Sonnet 4.5 available for Plan C", flush=True)
        except Exception as e:
            print(f"  ⚠️  Claude not available: {e}", flush=True)
        
        # Model routing strategy
        # Claude for complex extractions (better JSON compliance)
        self.claude_types = ["team", "company"]
        # GPT-4o for critical metrics
        self.critical_types = ["financial", "progress"]
        # GPT-4o-mini for simple extractions
        self.simple_types = ["market"]
        
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

    def _get_model_for_type(self, extract_type: str) -> str:
        """Determine which model to use for extraction type"""
        if extract_type in self.claude_types and self.claude_extractor:
            return "claude"
        elif extract_type in self.critical_types:
            return "gpt-4o"
        else:
            return "gpt-4o-mini"

    async def _extract_from_chunk(
        self, doc: Document, extract_type: str
    ) -> Dict[str, Any]:
        """Extract data from a single chunk using appropriate model"""
        source_file = doc.metadata.get("source_file", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        
        model_name = self._get_model_for_type(extract_type)
        
        token_stats = {
            "model": model_name,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_hit": False,
        }

        prompt_template = EXTRACTION_PROMPTS[extract_type]

        # Use Claude for complex extractions
        if model_name == "claude" and self.claude_extractor:
            try:
                print(f"  → Using Claude Sonnet 4.5 (Plan C: Hybrid Strategy)...", flush=True)
                start_time = time.time()
                
                result = await self.claude_extractor.extract_json(
                    text=doc.page_content,
                    extraction_prompt=prompt_template,
                    temperature=0.1,
                )
                
                elapsed = time.time() - start_time
                
                # Estimate tokens (Claude uses different tokenization)
                input_tokens = count_tokens(doc.page_content, "gpt-4o")  # Approximate
                output_tokens = count_tokens(json.dumps(result), "gpt-4o")  # Approximate
                token_stats["input_tokens"] = input_tokens
                token_stats["output_tokens"] = output_tokens
                
                cost = self.claude_extractor.estimate_cost(input_tokens, output_tokens)
                
                print(f"  → Output: {format_tokens(output_tokens)} tokens", flush=True)
                print(f"  → Time: {elapsed:.2f}s", flush=True)
                print(f"  → Cost: {format_cost(cost)}", flush=True)
                
                # Apply validation and fixing
                result = self._validate_and_fix_result(result, extract_type)
                
                if isinstance(result, dict):
                    result["_token_stats"] = token_stats
                    result["_source_file"] = source_file
                    result["_chunk_id"] = chunk_id
                
                print(f"  → ✅ Complete", flush=True)
                return result
                
            except Exception as e:
                print(f"  → ⚠️  Claude extraction failed: {e}, falling back to GPT-4o", flush=True)
                model_name = "gpt-4o"  # Fallback

        # Use OpenAI models
        if model_name in ["gpt-4o", "gpt-4o-mini"]:
            llm = self.gpt4o_llm if model_name == "gpt-4o" else self.gpt4o_mini_llm
            prompt = ChatPromptTemplate.from_template(prompt_template)

            max_input_tokens = 4000 if model_name == "gpt-4o" else 3000
            chunk_content = doc.page_content

            chunk_tokens = count_tokens(chunk_content, model_name)
            if chunk_tokens > max_input_tokens:
                sentences = chunk_content.split(". ")
                truncated = []
                current_tokens = 0
                for sent in sentences:
                    sent_tokens = count_tokens(sent, model_name)
                    if current_tokens + sent_tokens > max_input_tokens:
                        break
                    truncated.append(sent)
                    current_tokens += sent_tokens
                chunk_content = ". ".join(truncated) + "..."

            try:
                print(f"  → Processing with {model_name.upper()} (Plan C: Hybrid Strategy)...", flush=True)
                start_time = time.time()
                
                # Use OpenAI's JSON mode
                from openai import AsyncOpenAI
                import os
                client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                
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
                        model=model_name,
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

                cost = estimate_cost(input_tokens, output_tokens, model_name)
                
                print(f"  → Output: {format_tokens(output_tokens)} tokens", flush=True)
                print(f"  → Time: {elapsed:.2f}s", flush=True)
                print(f"  → Cost: {format_cost(cost)}", flush=True)

                result = json.loads(content)
                
                # Apply validation and fixing
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
                return {}

        return {}

    def _validate_and_fix_result(self, result: Dict[str, Any], extract_type: str) -> Dict[str, Any]:
        """Apply validation and fixing"""
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

        model_name = self._get_model_for_type(extract_type)
        model_label = "Claude Sonnet 4.5" if model_name == "claude" else model_name.upper()
        
        print(f"  🔍 Extracting {extract_type} using {model_label} (Plan C: Hybrid Strategy)")
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

        # Calculate cost based on models used
        if model_name == "claude":
            cost = self.claude_extractor.estimate_cost(input_tokens_total, output_tokens_total) if self.claude_extractor else 0.0
        elif model_name == "gpt-4o":
            cost = (input_tokens_total / 1_000_000 * 2.50) + (output_tokens_total / 1_000_000 * 10.00)
        else:
            cost = (input_tokens_total / 1_000_000 * 0.15) + (output_tokens_total / 1_000_000 * 0.60)

        print(f"     ✓ Completed in {extraction_time:.2f}s")
        print(f"     📊 {len(valid_results)} successful / {len(documents)} chunks")
        print(f"     🔄 Cache hits: {cache_hits}")
        print(f"     💾 Tokens: {input_tokens_total:,} in + {output_tokens_total:,} out = {total_tokens:,} total")
        print(f"     💰 Cost: ~${cost:.4f}")

        if not valid_results:
            return self.data_classes[extract_type]()

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
            "model": model_label,
        }

        return consolidated

