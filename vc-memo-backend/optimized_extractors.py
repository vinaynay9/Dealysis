from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from models import (
    ProgressData,
    FinancialData,
    MarketData,
    CompanyData,
    TeamData,
    ExtractedData,
)
from rate_limiter import batch_process_with_rate_limit, RateLimiter
from summary_cache import SummaryCache
from smart_chunker import DocumentChunk
from typing import List, Dict, Any, Type
import asyncio
import json
import tiktoken


# Import extraction prompts from original extractors
from extractors import EXTRACTION_PROMPTS


class OptimizedExtractor:
    """Optimized extractor with caching but direct extraction (no summarization)"""

    def __init__(self, cache_dir: str = "cache"):
        # Use gpt-4o-mini for less critical extractions, gpt-4o for critical ones
        self.mini_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        self.full_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # Use full model for critical extractions that need precision
        self.critical_types = ["financial", "progress"]  # These need high accuracy
        
        self.data_classes = {
            "progress": ProgressData,
            "financial": FinancialData,
            "market": MarketData,
            "company": CompanyData,
            "team": TeamData,
        }
        
        self.cache = SummaryCache(cache_dir)
        self.rate_limiter = RateLimiter(
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
        )
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        
        # Concurrent request limits - lower than before to avoid rate limits
        self.max_concurrent = 4

    def _get_model_for_type(self, extract_type: str) -> ChatOpenAI:
        """Choose model based on extraction type"""
        return self.full_llm if extract_type in self.critical_types else self.mini_llm

    async def _extract_from_chunk(
        self, chunk: DocumentChunk, extract_type: str
    ) -> Dict[str, Any]:
        """Extract data from a single chunk with caching"""
        
        # Check cache first (only for non-critical types to save cost)
        if extract_type not in self.critical_types:
            model_name = "gpt-4o-mini"
            cached = await self.cache.get_summary(
                chunk.content, 
                prompt_type=f"extraction_{extract_type}", 
                model=model_name
            )
            
            if cached:
                # Use cached result
                try:
                    return json.loads(cached["summary"])
                except:
                    pass
        
        # Get appropriate model
        llm = self._get_model_for_type(extract_type)
        model_name = "gpt-4o" if extract_type in self.critical_types else "gpt-4o-mini"
        
        # Prepare prompt
        prompt_template = EXTRACTION_PROMPTS[extract_type]
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Limit input size to avoid token waste (but keep enough context)
        max_input_tokens = 4000 if extract_type in self.critical_types else 3000
        chunk_content = chunk.content
        
        # Truncate if needed, but try to keep it intact
        chunk_tokens = len(self.tokenizer.encode(chunk_content))
        if chunk_tokens > max_input_tokens:
            # Try to truncate at sentence boundary
            sentences = chunk_content.split(". ")
            truncated = []
            current_tokens = 0
            for sent in sentences:
                sent_tokens = len(self.tokenizer.encode(sent))
                if current_tokens + sent_tokens > max_input_tokens:
                    break
                truncated.append(sent)
                current_tokens += sent_tokens
            chunk_content = ". ".join(truncated) + "..."
        
        # Extract with rate limiting
        try:
            response = await self.rate_limiter.execute(
                llm.ainvoke, prompt.format_messages(text=chunk_content)
            )
            
            # Parse JSON response
            result = json.loads(response.content)
            
            # Cache the result (only for non-critical types to save cost)
            if extract_type not in self.critical_types:
                input_tokens = len(self.tokenizer.encode(chunk_content))
                output_tokens = len(self.tokenizer.encode(response.content))
                cost = self.cache.estimate_cost(input_tokens, output_tokens, model_name)
                
                await self.cache.store_summary(
                    text=chunk.content,
                    summary=response.content,
                    prompt_type=f"extraction_{extract_type}",
                    model=model_name,
                    metadata={"chunk_id": chunk.chunk_id, "source": chunk.source_file},
                    token_count=output_tokens,
                    cost_estimate=cost,
                )
            
            return result
            
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            try:
                # Remove markdown code blocks if present
                cleaned = response.content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                    cleaned = cleaned.strip()
                
                return json.loads(cleaned)
            except:
                return {}
        except Exception as e:
            print(f"Error extracting {extract_type} from chunk {chunk.chunk_id}: {e}")
            return {}

    async def extract(
        self, chunks: List[DocumentChunk], extract_type: str
    ) -> ExtractedData:
        """Extract specific type of data from chunks"""

        if extract_type not in EXTRACTION_PROMPTS:
            raise ValueError(f"Unknown extraction type: {extract_type}")

        print(f"  Extracting {extract_type} from {len(chunks)} chunks...")

        # Process chunks with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []

        async def process_chunk(chunk: DocumentChunk):
            async with semaphore:
                return await self._extract_from_chunk(chunk, extract_type)

        # Process all chunks
        tasks = [process_chunk(chunk) for chunk in chunks]
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and empty results
        valid_results = []
        for result in chunk_results:
            if isinstance(result, Exception):
                continue
            if result and isinstance(result, dict):
                valid_results.append(result)

        if not valid_results:
            return self.data_classes[extract_type]()

        # Consolidate results
        data_class = self.data_classes[extract_type]
        consolidated = self._consolidate_results(valid_results, data_class)

        # Calculate confidence
        confidence = self._calculate_confidence(valid_results, len(chunks))
        consolidated.confidence = confidence

        return consolidated

    def _consolidate_results(
        self, results: List[Dict], data_class: Type[ExtractedData]
    ) -> ExtractedData:
        """Merge results from multiple chunks - improved to preserve all data"""
        if not results:
            return data_class()

        consolidated = {}

        for field in data_class.__fields__:
            if field == "confidence":
                continue

            field_info = data_class.__fields__[field]

            # For list fields, combine ALL values from all chunks
            if hasattr(field_info.annotation, "__origin__") and field_info.annotation.__origin__ in [
                list,
                List,
            ]:
                all_items = []
                for r in results:
                    if isinstance(r.get(field), list):
                        all_items.extend(r[field])
                if all_items:
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_items = []
                    for item in all_items:
                        # Use tuple for dict items, string for others
                        item_key = tuple(sorted(item.items())) if isinstance(item, dict) else item
                        if item_key not in seen:
                            seen.add(item_key)
                            unique_items.append(item)
                    consolidated[field] = unique_items

            # For dict fields, merge all non-empty dicts
            elif hasattr(field_info.annotation, "__origin__") and field_info.annotation.__origin__ in [
                dict,
                Dict,
            ]:
                merged_dict = {}
                for r in results:
                    if r.get(field) and isinstance(r.get(field), dict):
                        # Merge dictionaries, preferring later values
                        merged_dict.update(r[field])
                if merged_dict:
                    consolidated[field] = merged_dict

            # For single values, collect all non-null values and take the most detailed
            else:
                all_values = [r.get(field) for r in results if r.get(field) is not None]
                if all_values:
                    # Prefer longer/more detailed values
                    consolidated[field] = max(all_values, key=lambda x: len(str(x)) if x else 0)

        return data_class(**consolidated)

    def _calculate_confidence(self, results: List[Dict], total_chunks: int) -> float:
        """Calculate extraction confidence"""
        if total_chunks == 0:
            return 0.0

        successful = len(results)
        data_richness = 0

        for result in results:
            # Count non-null fields
            data_richness += sum(1 for v in result.values() if v)

        # Confidence based on success rate and data richness
        success_rate = successful / total_chunks
        avg_richness = (data_richness / (successful * 10)) if successful > 0 else 0

        return min(success_rate * 0.7 + avg_richness * 0.3, 0.95)


class OptimizedExtractionCoordinator:
    """Coordinates optimized extractions with caching"""

    def __init__(self, cache_dir: str = "cache"):
        self.extractor = OptimizedExtractor(cache_dir)
        self.extract_types = ["progress", "financial", "market", "company", "team"]

    async def extract_all(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Run all extractors in parallel"""

        print(f"Running optimized extraction on {len(chunks)} chunks...")

        # Create extraction tasks
        tasks = {
            extract_type: self.extractor.extract(chunks, extract_type)
            for extract_type in self.extract_types
        }

        # Run all extractions in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Map results back to types
        extracted_data = {}
        for extract_type, result in zip(self.extract_types, results):
            if isinstance(result, Exception):
                print(f"Extraction failed for {extract_type}: {result}")
                # Use empty data class as fallback
                data_class = self.extractor.data_classes[extract_type]
                extracted_data[extract_type] = data_class()
            else:
                extracted_data[extract_type] = result
                print(f"  ✓ {extract_type}: {result.confidence:.2f} confidence")

        return extracted_data
