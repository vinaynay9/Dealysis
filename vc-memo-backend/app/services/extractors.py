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
from app.utils.rate_limiter import batch_process_with_rate_limit, RateLimiter
from app.utils.summary_cache import SummaryCache
from typing import List, Dict, Any, Type
import asyncio
import json
import tiktoken
import time


EXTRACTION_PROMPTS = {
    "progress": """Extract operational progress metrics from this text. Focus on day-to-day business operations.

TEXT: {text}

CRITICAL: Extract ALL numerical values, dates, percentages, and metrics. Be thorough and comprehensive.

Extract the following metrics if present:
- ARR (Annual Recurring Revenue) - include exact amounts with currency
- MRR (Monthly Recurring Revenue) - include exact amounts with currency
- Monthly burn rate - include exact amounts
- Runway in months - include exact number
- Churn rate (monthly/annual) - include percentages
- Growth rate (MoM/YoY) - include percentages and timeframes
- Customer count - include exact numbers
- CAC (Customer Acquisition Cost) - include exact amounts
- LTV (Lifetime Value) - include exact amounts
- Unit economics ratios (LTV/CAC, etc.)
- Revenue retention rates
- Any time-series data with dates

Output JSON format:
{{
  "arr": "value if found (include currency and time period), null otherwise",
  "mrr": "value if found (include currency and time period), null otherwise",
  "burn_rate": "value if found (include currency and period), null otherwise",
  "runway_months": number or null,
  "churn_rate": "value if found (include period), null otherwise",
  "growth_rate_mom": "value if found (include percentage), null otherwise",
  "growth_rate_yoy": "value if found (include percentage), null otherwise",
  "customer_count": "value if found (include exact number), null otherwise",
  "cac": "value if found (include currency), null otherwise",
  "ltv": "value if found (include currency), null otherwise"
}}

IMPORTANT: Capture ALL numerical values, dates, and metrics mentioned. Include context like time periods, currencies, and units. Return valid JSON only.""",
    "financial": """Extract high-level funding and cap table information from this text.

TEXT: {text}

CRITICAL: Extract ALL funding-related information including the investment ask and use of funds.

Look for:
- Previous funding rounds (Seed, Series A, etc.) - include amounts, dates, investors
- Total funding raised to date - include exact amount
- Last round valuation - include exact amount and date
- Current round valuation target (pre-money/post-money) - include exact amount
- Investment ask / Current round size - CRITICAL: How much the company is raising NOW
- Use of funds - CRITICAL: How the funds will be allocated (e.g., "40% sales, 35% product")
- Funding stage (Seed, Series A, Series B, etc.)
- Ownership percentages by investor type
- Liquidation preferences
- Board composition
- Valuation details (pre-money, post-money, implied valuation)

Output JSON format:
{{
  "previous_rounds": ["list of rounds like 'Seed $2M (2021)', 'Series A $10M (2022)'"],
  "total_funding_raised": "total amount if stated (include currency)",
  "last_valuation": "previous valuation (include amount and date)",
  "current_valuation": "current round target (include pre/post-money if specified)",
  "investment_ask": "amount company is raising in current round (CRITICAL - must extract if mentioned)",
  "current_round_size": "same as investment_ask (alternative field)",
  "use_of_funds": "how funds will be allocated (e.g., '40% sales & marketing, 35% product development')",
  "ownership_percentages": {{"founders": "X%", "employees": "Y%", "investors": "Z%"}},
  "liquidation_preferences": "preference details",
  "board_composition": "board member details"
}}

IMPORTANT: The investment_ask and use_of_funds are critical fields - always extract if mentioned anywhere in the text. Include exact amounts, percentages, and dates. Return valid JSON only.""",
    "market": """Extract market opportunity and competitive information from this text.

TEXT: {text}

Look for:
- Total Addressable Market (TAM)
- Serviceable Addressable Market (SAM)
- Serviceable Obtainable Market (SOM)
- Market growth rates
- Target customer segments
- Key competitors
- Competitive advantages

Output JSON format:
{{
  "tam": "TAM value if stated",
  "sam": "SAM value if stated",
  "som": "SOM value if stated",
  "market_growth_rate": "growth rate if stated",
  "target_segments": ["list of customer segments"],
  "competitors": ["list of competitors"],
  "competitive_advantages": ["list of advantages"]
}}

Return valid JSON only.""",
    "company": """Extract company overview information from this text.

TEXT: {text}

Look for:
- Company name
- Mission statement
- Business model
- Products or services
- Value proposition
- Go-to-market strategy
- Funding stage (Seed, Series A, Series B, etc.) - CRITICAL
- Current round details (round name, target amount, etc.) - CRITICAL

Output JSON format:
{{
  "company_name": "name if found",
  "mission": "mission statement",
  "business_model": "how company makes money",
  "products": ["list of products/services"],
  "value_proposition": "key value prop",
  "go_to_market": "GTM strategy",
  "funding_stage": "funding stage if mentioned (e.g., 'Series A', 'Seed', 'Series B')",
  "current_round_details": "details about current fundraising round (round name, target amount, etc.)"
}}

IMPORTANT: Always extract funding_stage and current_round_details if mentioned. Return valid JSON only.""",
    "team": """Extract team and leadership information from this text.

TEXT: {text}

Look for:
- Founders (names, titles, backgrounds)
- Key employees
- Advisors
- Board members
- Past exits or successes
- Relevant industry experience

Output JSON format:
{{
  "founders": [{{"name": "Name", "title": "Title", "background": "Background"}}],
  "key_employees": ["list of key employees"],
  "advisors": ["list of advisors"],
  "board_members": ["list of board members"],
  "past_exits": ["previous successful exits"],
  "relevant_experience": ["relevant experience points"]
}}

Return valid JSON only.""",
}


class OptimizedExtractor:
    """Optimized extractor with caching and intelligent model selection"""

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

        # Concurrent request limits
        self.max_concurrent = 2

    def _get_model_for_type(self, extract_type: str) -> ChatOpenAI:
        """Choose model based on extraction type"""
        return self.full_llm if extract_type in self.critical_types else self.mini_llm

    async def _extract_from_chunk(
        self, doc: Document, extract_type: str
    ) -> Dict[str, Any]:
        """Extract data from a single document chunk with caching"""

        # Track token usage for this extraction
        token_stats = {"input_tokens": 0, "output_tokens": 0, "cache_hit": False}

        # Check cache first (only for non-critical types to save cost)
        if extract_type not in self.critical_types:
            model_name = "gpt-4o-mini"
            cached = await self.cache.get_summary(
                doc.page_content,
                prompt_type=f"extraction_{extract_type}",
                model=model_name,
            )

            if cached:
                # Use cached result
                try:
                    result = json.loads(cached["summary"])
                    token_stats["cache_hit"] = True
                    result._token_stats = token_stats
                    return result
                except:
                    pass

        # Get appropriate model
        llm = self._get_model_for_type(extract_type)
        model_name = "gpt-4o" if extract_type in self.critical_types else "gpt-4o-mini"

        # Prepare prompt
        prompt_template = EXTRACTION_PROMPTS[extract_type]
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Limit input size to avoid token waste
        max_input_tokens = 4000 if extract_type in self.critical_types else 3000
        chunk_content = doc.page_content

        # Truncate if needed
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

            # Track token usage
            input_tokens = len(self.tokenizer.encode(chunk_content))
            output_tokens = len(self.tokenizer.encode(response.content))
            token_stats["input_tokens"] = input_tokens
            token_stats["output_tokens"] = output_tokens

            # Parse JSON response
            result = json.loads(response.content)
            result._token_stats = token_stats

            # Cache the result (only for non-critical types)
            if extract_type not in self.critical_types:
                input_tokens = len(self.tokenizer.encode(chunk_content))
                output_tokens = len(self.tokenizer.encode(response.content))
                cost = self.cache.estimate_cost(input_tokens, output_tokens, model_name)

                await self.cache.store_summary(
                    text=doc.page_content,
                    summary=response.content,
                    prompt_type=f"extraction_{extract_type}",
                    model=model_name,
                    metadata={
                        "source_file": doc.metadata.get("source_file", "unknown"),
                        "chunk_index": doc.metadata.get("chunk_index", 0),
                    },
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
            source = doc.metadata.get("source_file", "unknown")
            print(f"Error extracting {extract_type} from {source}: {e}")
            return {}

    async def extract(
        self, documents: List[Document], extract_type: str
    ) -> ExtractedData:
        """Extract specific type of data from document chunks"""

        if extract_type not in EXTRACTION_PROMPTS:
            raise ValueError(f"Unknown extraction type: {extract_type}")

        if not documents:
            print(f"  ⚠ {extract_type}: No chunks assigned, skipping")
            return self.data_classes[extract_type]()

        # Get model info for logging
        model_name = "gpt-4o" if extract_type in self.critical_types else "gpt-4o-mini"

        print(f"  🔍 Extracting {extract_type} ({model_name})...")
        print(f"     Processing {len(documents)} chunks")

        # Track extraction statistics
        extraction_start = time.time()
        input_tokens_total = 0
        output_tokens_total = 0
        cache_hits = 0

        # Process documents with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []

        async def process_doc(doc: Document):
            async with semaphore:
                result = await self._extract_from_chunk(doc, extract_type)
                # Track token usage (stored in metadata during extraction)
                if hasattr(result, "_token_stats"):
                    return result, result._token_stats
                return result, None

        # Process all documents
        tasks = [process_doc(doc) for doc in documents]
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and collect token statistics
        valid_results = []
        for result_tuple in chunk_results:
            if isinstance(result_tuple, Exception):
                continue

            # Unpack result and token stats
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

        # Calculate extraction metrics
        extraction_time = time.time() - extraction_start
        total_tokens = input_tokens_total + output_tokens_total

        # Estimate cost based on model
        if model_name == "gpt-4o":
            # GPT-4o pricing: $2.50 per 1M input tokens, $10.00 per 1M output tokens
            cost = (input_tokens_total / 1_000_000 * 2.50) + (
                output_tokens_total / 1_000_000 * 10.00
            )
        else:
            # GPT-4o-mini pricing: $0.15 per 1M input tokens, $0.60 per 1M output tokens
            cost = (input_tokens_total / 1_000_000 * 0.15) + (
                output_tokens_total / 1_000_000 * 0.60
            )

        print(f"     ✓ Completed in {extraction_time:.2f}s")
        print(f"     📊 {len(valid_results)} successful / {len(documents)} chunks")
        print(f"     🔄 Cache hits: {cache_hits}")
        print(
            f"     💾 Tokens: {input_tokens_total:,} in + {output_tokens_total:,} out = {total_tokens:,} total"
        )
        print(f"     💰 Cost: ~${cost:.4f}")

        if not valid_results:
            return self.data_classes[extract_type]()

        # Consolidate results
        data_class = self.data_classes[extract_type]
        consolidated = self._consolidate_results(valid_results, data_class)

        # Calculate confidence
        confidence = self._calculate_confidence(valid_results, len(documents))
        consolidated.confidence = confidence

        # Store extraction statistics for pipeline-level reporting
        consolidated._extraction_stats = {
            "chunks_processed": len(documents),
            "successful_extractions": len(valid_results),
            "cache_hits": cache_hits,
            "input_tokens": input_tokens_total,
            "output_tokens": output_tokens_total,
            "total_tokens": total_tokens,
            "cost": cost,
            "time": extraction_time,
            "model": model_name,
        }

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
            if hasattr(
                field_info.annotation, "__origin__"
            ) and field_info.annotation.__origin__ in [
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
                        item_key = (
                            tuple(sorted(item.items()))
                            if isinstance(item, dict)
                            else item
                        )
                        if item_key not in seen:
                            seen.add(item_key)
                            unique_items.append(item)
                    consolidated[field] = unique_items

            # For dict fields, merge all non-empty dicts
            elif hasattr(
                field_info.annotation, "__origin__"
            ) and field_info.annotation.__origin__ in [
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
                    consolidated[field] = max(
                        all_values, key=lambda x: len(str(x)) if x else 0
                    )

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


class ExtractionCoordinator:
    """Coordinates all extractions with optimized caching and parallel processing"""

    def __init__(self, cache_dir: str = "cache"):
        self.extractor = OptimizedExtractor(cache_dir)
        self.extract_types = ["progress", "financial", "market", "company", "team"]

    async def extract_all(
        self, routed_chunks: Dict[str, List[Document]]
    ) -> Dict[str, Any]:
        """
        Run all extractors in parallel on their assigned chunks.

        Args:
            routed_chunks: Dict mapping extractor names to their assigned document chunks

        Returns:
            Dict of extracted data by type
        """

        total_chunks = sum(len(chunks) for chunks in routed_chunks.values())
        print(f"\n🔍 Running extraction on {total_chunks} routed chunk assignments...")

        # Create extraction tasks with routed chunks
        tasks = {
            extract_type: self.extractor.extract(
                routed_chunks.get(extract_type, []), extract_type
            )
            for extract_type in self.extract_types
        }

        # Run all extractions in parallel
        extraction_start = time.time()
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        extraction_time = time.time() - extraction_start

        # Map results back to types and collect statistics
        extracted_data = {}
        total_api_calls = 0
        total_cost = 0.0
        total_tokens = 0
        total_cache_hits = 0

        print(f"\n📊 Extraction Results:")
        for extract_type, result in zip(self.extract_types, results):
            if isinstance(result, Exception):
                print(f"  ✗ {extract_type}: Extraction failed - {result}")
                # Use empty data class as fallback
                data_class = self.extractor.data_classes[extract_type]
                extracted_data[extract_type] = data_class()
            else:
                extracted_data[extract_type] = result

                # Collect statistics if available
                if hasattr(result, "_extraction_stats"):
                    stats = result._extraction_stats
                    total_api_calls += stats["chunks_processed"]
                    total_cost += stats["cost"]
                    total_tokens += stats["total_tokens"]
                    total_cache_hits += stats["cache_hits"]

                    print(f"  ✓ {extract_type:12} confidence: {result.confidence:.2f}")

        # Print overall extraction summary
        print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📈 Extraction Summary:")
        print(f"   Total API calls:  {total_api_calls}")
        print(f"   Cache hits:       {total_cache_hits}")
        print(f"   Total tokens:     {total_tokens:,}")
        print(f"   Total cost:       ~${total_cost:.4f}")
        print(f"   Time:             {extraction_time:.2f}s")

        # Calculate efficiency vs baseline (all chunks to all extractors)
        baseline_api_calls = sum(len(chunks) for chunks in routed_chunks.values())
        if baseline_api_calls > 0:
            # Baseline would be if every chunk went to every extractor
            theoretical_baseline = (
                len(
                    set(
                        chunk.metadata.get("chunk_id", id(chunk))
                        for chunks in routed_chunks.values()
                        for chunk in chunks
                    )
                )
                * len(self.extract_types)
                if routed_chunks
                else 0
            )

            if theoretical_baseline > 0:
                efficiency = (
                    (theoretical_baseline - total_api_calls)
                    / theoretical_baseline
                    * 100
                )
                print(
                    f"   Efficiency:       {efficiency:.1f}% reduction vs baseline ({theoretical_baseline} calls)"
                )
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return extracted_data
