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
from app.utils.token_counter import (
    count_tokens,
    estimate_ollama_tokens,
    estimate_cost,
    format_cost,
    format_tokens,
)
from app.services.local_llm import get_local_llm
from typing import List, Dict, Any, Type, Optional
import asyncio
import json
import tiktoken
import time
import sys


EXTRACTION_PROMPTS = {
    "progress": """Extract operational progress metrics from this text. Focus on day-to-day business operations.

TEXT: {text}

CRITICAL ACCURACY REQUIREMENTS:
- Extract ONLY information that is explicitly stated in the text
- If a metric is NOT mentioned, you MUST return null (not a placeholder, not an estimate, not an inference)
- NEVER invent, estimate, or infer values that are not directly stated
- If you are uncertain about a value, return null
- If the text mentions a metric but the exact value is unclear, return null

Extract the following metrics ONLY if explicitly present:
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
  "arr": "exact value if explicitly stated (include currency and time period), null if not mentioned",
  "mrr": "exact value if explicitly stated (include currency and time period), null if not mentioned",
  "burn_rate": "exact value if explicitly stated (include currency and period), null if not mentioned",
  "runway_months": exact number if explicitly stated, null if not mentioned,
  "churn_rate": "exact value if explicitly stated (include period), null if not mentioned",
  "growth_rate_mom": "exact value if explicitly stated (include percentage), null if not mentioned",
  "growth_rate_yoy": "exact value if explicitly stated (include percentage), null if not mentioned",
  "customer_count": "exact value if explicitly stated (include exact number), null if not mentioned",
  "cac": "exact value if explicitly stated (include currency), null if not mentioned",
  "ltv": "exact value if explicitly stated (include currency), null if not mentioned"
}}

STRICT RULES:
1. Return null for any field where the information is not explicitly stated in the text
2. Do NOT use placeholder values like "N/A", "unknown", "not specified" - use null
3. Do NOT estimate or infer values based on context
4. Do NOT make assumptions about what the value "probably" is
5. If you cannot find the exact information, return null - this is correct behavior

IMPORTANT: Capture ONLY numerical values, dates, and metrics that are explicitly mentioned. Include context like time periods, currencies, and units when available. Return valid JSON only.""",
    "financial": """Extract high-level funding and cap table information from this text.

TEXT: {text}

CRITICAL ACCURACY REQUIREMENTS:
- Extract ONLY information that is explicitly stated in the text
- If a field is NOT mentioned, you MUST return null (not a placeholder, not an estimate, not an inference)
- NEVER invent, estimate, or infer values that are not directly stated
- If you are uncertain about a value, return null
- If the text mentions something but the exact value is unclear, return null

Look for ONLY explicitly stated information:
- Previous funding rounds (Seed, Series A, etc.) - include amounts, dates, investors ONLY if all are stated
- Total funding raised to date - include exact amount ONLY if explicitly stated
- Last round valuation - include exact amount and date ONLY if both are stated
- Current round valuation target (pre-money/post-money) - include exact amount ONLY if stated
- Investment ask / Current round size - CRITICAL: How much the company is raising NOW (ONLY if explicitly stated)
- Use of funds - CRITICAL: How the funds will be allocated (e.g., "40% sales, 35% product") ONLY if explicitly stated
- Funding stage (Seed, Series A, Series B, etc.) ONLY if explicitly stated
- Ownership percentages by investor type ONLY if explicitly stated
- Liquidation preferences ONLY if explicitly stated
- Board composition ONLY if explicitly stated
- Valuation details (pre-money, post-money, implied valuation) ONLY if explicitly stated

Output JSON format:
{{
  "previous_rounds": ["list of rounds like 'Seed $2M (2021)', 'Series A $10M (2022)'] ONLY if explicitly stated, null otherwise"],
  "total_funding_raised": "exact amount if explicitly stated (include currency), null if not mentioned",
  "last_valuation": "exact amount and date if both explicitly stated, null if either is missing",
  "current_valuation": "exact amount if explicitly stated (include pre/post-money if specified), null if not mentioned",
  "investment_ask": "exact amount if explicitly stated, null if not mentioned (CRITICAL: do NOT infer)",
  "current_round_size": "exact amount if explicitly stated (same as investment_ask if mentioned), null if not mentioned",
  "use_of_funds": "exact allocation if explicitly stated (e.g., '40% sales & marketing, 35% product development'), null if not mentioned",
  "ownership_percentages": {{"founders": "X%", "employees": "Y%", "investors": "Z%"}} ONLY if explicitly stated, null otherwise,
  "liquidation_preferences": "exact details if explicitly stated, null if not mentioned",
  "board_composition": "exact details if explicitly stated, null if not mentioned"
}}

STRICT RULES:
1. Return null for any field where the information is not explicitly stated in the text
2. Do NOT use placeholder values like "N/A", "unknown", "not specified" - use null
3. Do NOT estimate or infer values based on context
4. Do NOT make assumptions about what the value "probably" is
5. If you cannot find the exact information, return null - this is correct behavior
6. For investment_ask and use_of_funds: extract ONLY if explicitly mentioned. Do NOT infer from other financial data.

IMPORTANT: Extract ONLY exact amounts, percentages, and dates that are explicitly stated. Return valid JSON only.""",
    "market": """Extract market opportunity and competitive information from this text.

TEXT: {text}

CRITICAL ACCURACY REQUIREMENTS:
- Extract ONLY information that is explicitly stated in the text
- If a field is NOT mentioned, you MUST return null (not a placeholder, not an estimate, not an inference)
- NEVER invent, estimate, or infer values that are not directly stated
- If you are uncertain about a value, return null
- If the text mentions something but the exact value is unclear, return null

Look for ONLY explicitly stated information:
- Total Addressable Market (TAM) - ONLY if explicitly stated with exact value
- Serviceable Addressable Market (SAM) - ONLY if explicitly stated with exact value
- Serviceable Obtainable Market (SOM) - ONLY if explicitly stated with exact value
- Market growth rates - ONLY if explicitly stated
- Target customer segments - ONLY if explicitly listed
- Key competitors - ONLY if explicitly named
- Competitive advantages - ONLY if explicitly described

Output JSON format:
{{
  "tam": "exact TAM value if explicitly stated, null if not mentioned",
  "sam": "exact SAM value if explicitly stated, null if not mentioned",
  "som": "exact SOM value if explicitly stated, null if not mentioned",
  "market_growth_rate": "exact growth rate if explicitly stated, null if not mentioned",
  "target_segments": ["list of customer segments if explicitly stated, empty list if not mentioned"],
  "competitors": ["list of competitors if explicitly named, empty list if not mentioned"],
  "competitive_advantages": ["list of advantages if explicitly described, empty list if not mentioned"]
}}

STRICT RULES:
1. Return null for any field where the information is not explicitly stated in the text
2. For lists, return empty list [] if not mentioned (not null, but empty)
3. Do NOT use placeholder values like "N/A", "unknown", "not specified" - use null or empty list
4. Do NOT estimate or infer values based on context
5. Do NOT make assumptions about what the value "probably" is
6. If you cannot find the exact information, return null or empty list - this is correct behavior

Return valid JSON only.""",
    "company": """Extract company overview information from this text.

TEXT: {text}

CRITICAL ACCURACY REQUIREMENTS:
- Extract ONLY information that is explicitly stated in the text
- If a field is NOT mentioned, you MUST return null (not a placeholder, not an estimate, not an inference)
- NEVER invent, estimate, or infer values that are not directly stated
- If you are uncertain about a value, return null
- If the text mentions something but the exact value is unclear, return null

Look for ONLY explicitly stated information:
- Company name - ONLY if explicitly stated
- Mission statement - ONLY if explicitly stated
- Business model - ONLY if explicitly described
- Products or services - ONLY if explicitly listed
- Value proposition - ONLY if explicitly described
- Go-to-market strategy - ONLY if explicitly described
- Funding stage (Seed, Series A, Series B, etc.) - CRITICAL: ONLY if explicitly stated
- Current round details (round name, target amount, etc.) - CRITICAL: ONLY if explicitly stated

Output JSON format:
{{
  "company_name": "exact name if explicitly stated, null if not mentioned",
  "mission": "exact mission statement if explicitly stated, null if not mentioned",
  "business_model": "exact description if explicitly stated, null if not mentioned",
  "products": ["list of products/services if explicitly listed, empty list if not mentioned"],
  "value_proposition": "exact value prop if explicitly stated, null if not mentioned",
  "go_to_market": "exact GTM strategy if explicitly stated, null if not mentioned",
  "funding_stage": "exact funding stage if explicitly stated (e.g., 'Series A', 'Seed', 'Series B'), null if not mentioned",
  "current_round_details": "exact details if explicitly stated (round name, target amount, etc.), null if not mentioned"
}}

STRICT RULES:
1. Return null for any field where the information is not explicitly stated in the text
2. For lists, return empty list [] if not mentioned (not null, but empty)
3. Do NOT use placeholder values like "N/A", "unknown", "not specified" - use null or empty list
4. Do NOT estimate or infer values based on context
5. Do NOT make assumptions about what the value "probably" is
6. If you cannot find the exact information, return null or empty list - this is correct behavior
7. For funding_stage and current_round_details: extract ONLY if explicitly mentioned. Do NOT infer from other context.

IMPORTANT: Extract ONLY information that is explicitly stated. Return valid JSON only.""",
    "team": """Extract team and leadership information from this text.

TEXT: {text}

CRITICAL ACCURACY REQUIREMENTS:
- Extract ONLY information that is explicitly stated in the text
- If a field is NOT mentioned, you MUST return null or empty list (not a placeholder, not an estimate, not an inference)
- NEVER invent, estimate, or infer values that are not directly stated
- If you are uncertain about a value, return null or empty list
- If the text mentions something but the exact details are unclear, return null or empty list

Look for ONLY explicitly stated information:
- Founders (names, titles, backgrounds) - ONLY if explicitly stated with at least name
- Key employees - ONLY if explicitly named
- Advisors - ONLY if explicitly named
- Board members - ONLY if explicitly named
- Past exits or successes - ONLY if explicitly described
- Relevant industry experience - ONLY if explicitly described

Output JSON format:
{{
  "founders": [{{"name": "exact name if stated", "title": "exact title if stated", "background": "exact background if stated"}}] - empty list if not mentioned,
  "key_employees": ["exact list of key employees if explicitly named, empty list if not mentioned"],
  "advisors": ["exact list of advisors if explicitly named, empty list if not mentioned"],
  "board_members": ["exact list of board members if explicitly named, empty list if not mentioned"],
  "past_exits": ["exact list of exits if explicitly described, empty list if not mentioned"],
  "relevant_experience": ["exact list of experience points if explicitly described, empty list if not mentioned"]
}}

STRICT RULES:
1. Return empty list [] for any field where the information is not explicitly stated in the text
2. Do NOT use placeholder values like "N/A", "unknown", "not specified" - use empty list
3. Do NOT estimate or infer values based on context
4. Do NOT make assumptions about what the value "probably" is
5. If you cannot find the exact information, return empty list - this is correct behavior
6. For founders: only include if at least the name is explicitly stated. If only partial info is available, include what is stated and use null for missing fields.

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
        
        # Check if Ollama is available for non-critical extractions
        self.local_llm = get_local_llm()
        self.ollama_available = False
        if self.local_llm:
            # Check availability asynchronously (will be checked on first use)
            self._ollama_checked = False
        else:
            self._ollama_checked = True

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

    async def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available (lazy check)"""
        if self._ollama_checked:
            return self.ollama_available
        
        if self.local_llm:
            print(f"  🔍 Checking Ollama availability...", flush=True)
            self.ollama_available = await self.local_llm.check_availability()
            self._ollama_checked = True
            if self.ollama_available:
                print(f"  ✅ Ollama available - will use for non-critical extractions (market, company, team)", flush=True)
                print(f"     This will save costs on non-critical data extraction", flush=True)
            else:
                print(f"  ⚠️  Ollama not available - service may not be running or not installed", flush=True)
                print(f"     Falling back to OpenAI for all extractions", flush=True)
                print(f"     Note: Set OLLAMA_AUTO_SETUP=true to auto-configure Ollama", flush=True)
                print(f"     For manual setup: Install from https://ollama.ai or run: brew install ollama", flush=True)
        else:
            print(f"  ⚠️  Ollama service not initialized", flush=True)
            print(f"     Using OpenAI for all extractions", flush=True)
        
        return self.ollama_available
    
    def _get_model_for_type(self, extract_type: str) -> ChatOpenAI:
        """Choose model based on extraction type"""
        return self.full_llm if extract_type in self.critical_types else self.mini_llm
    
    def _should_use_ollama(self, extract_type: str) -> bool:
        """Determine if Ollama should be used for this extraction type"""
        # Only use Ollama for non-critical types
        return extract_type not in self.critical_types and self.ollama_available

    async def _extract_from_chunk(
        self, doc: Document, extract_type: str
    ) -> Dict[str, Any]:
        """Extract data from a single document chunk with caching"""

        # Track token usage for this extraction
        token_stats = {"input_tokens": 0, "output_tokens": 0, "cache_hit": False, "model": "unknown"}
        
        # Track source information for citations
        source_file = doc.metadata.get("source_file", "unknown")
        chunk_id = doc.metadata.get("chunk_id", id(doc))
        chunk_index = doc.metadata.get("chunk_index", 0)

        # Check if we should use Ollama (for non-critical types)
        use_ollama = self._should_use_ollama(extract_type)
        
        # Determine model selection and reason
        if extract_type in self.critical_types:
            model_name = "gpt-4o"
            model_reason = "critical extraction (financial/progress)"
        elif use_ollama:
            model_name = "ollama"
            model_reason = "non-critical extraction (cost-saving)"
        else:
            model_name = "gpt-4o-mini"
            model_reason = "non-critical extraction (Ollama unavailable)"
        
        # Log extraction start
        print(f"\n[EXTRACTION] {extract_type} (chunk {chunk_index + 1} from \"{source_file}\")", flush=True)
        print(f"  → Using: {model_name.upper()}{' (llama3.2:3b)' if model_name == 'ollama' else ''} - {model_reason}", flush=True)
        
        # Estimate input tokens
        if model_name == "ollama":
            input_tokens_est = estimate_ollama_tokens(doc.page_content)
        else:
            input_tokens_est = count_tokens(doc.page_content, model_name)
        print(f"  → Input: {format_tokens(input_tokens_est)} tokens", flush=True)
        
        # Check cache first (only for non-critical types to save cost)
        if extract_type not in self.critical_types:
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
                    token_stats["model"] = model_name
                    # Store metadata in the dict
                    if isinstance(result, dict):
                        result["_token_stats"] = token_stats
                    else:
                        result._token_stats = token_stats
                    print(f"  → Cache: ✅ HIT (saved {format_cost(estimate_cost(input_tokens_est, len(json.dumps(result)) // 4, model_name))})", flush=True)
                    print(f"  → ✅ Complete (cached)", flush=True)
                    return result
                except:
                    pass
            else:
                print(f"  → Cache: ❌ MISS", flush=True)

        # Use Ollama for non-critical extractions if available (always prefer Ollama when available)
        if use_ollama and self.local_llm:
            try:
                print(f"  → Using Ollama (llama3.2:3b) for cost-effective extraction...", flush=True)
                start_time = time.time()
                prompt_template = EXTRACTION_PROMPTS[extract_type]
                result = await self.local_llm.extract_json(
                    text=doc.page_content,
                    extraction_prompt=prompt_template,
                    temperature=0.1,
                )
                elapsed = time.time() - start_time
                
                input_tokens = estimate_ollama_tokens(doc.page_content)
                output_tokens = estimate_ollama_tokens(json.dumps(result))
                token_stats["model"] = "ollama"
                token_stats["input_tokens"] = input_tokens
                token_stats["output_tokens"] = output_tokens
                # Store metadata in the dict
                if isinstance(result, dict):
                    result["_token_stats"] = token_stats
                    result["_source_file"] = source_file
                    result["_chunk_id"] = chunk_id
                else:
                    result._token_stats = token_stats
                    result._source_file = source_file
                    result._chunk_id = chunk_id
                
                print(f"  → Output: {format_tokens(output_tokens)} tokens", flush=True)
                print(f"  → Time: {elapsed:.2f}s", flush=True)
                print(f"  → Cost: {format_cost(0.0)} (Ollama)", flush=True)
                
                # Cache the result
                await self.cache.store_summary(
                    text=doc.page_content,
                    summary=json.dumps(result),
                    prompt_type=f"extraction_{extract_type}",
                    model="ollama",
                    metadata={
                        "source_file": source_file,
                        "chunk_index": doc.metadata.get("chunk_index", 0),
                    },
                    token_count=output_tokens,
                    cost_estimate=0.0,  # Ollama is free
                )
                
                print(f"  → ✅ Complete", flush=True)
                return result
            except Exception as e:
                print(f"  → ⚠️  Ollama extraction failed: {e}", flush=True)
                print(f"  → Falling back to OpenAI (this extraction will use OpenAI instead)", flush=True)
                # Fall through to OpenAI

        # Get appropriate model (OpenAI)
        llm = self._get_model_for_type(extract_type)
        model_name = "gpt-4o" if extract_type in self.critical_types else "gpt-4o-mini"
        token_stats["model"] = model_name

        # Prepare prompt
        prompt_template = EXTRACTION_PROMPTS[extract_type]
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Limit input size to avoid token waste
        max_input_tokens = 4000 if extract_type in self.critical_types else 3000
        chunk_content = doc.page_content

        # Truncate if needed
        chunk_tokens = count_tokens(chunk_content, model_name)
        if chunk_tokens > max_input_tokens:
            # Try to truncate at sentence boundary
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
            print(f"  → ⚠ Truncated from {format_tokens(chunk_tokens)} to {format_tokens(count_tokens(chunk_content, model_name))} tokens", flush=True)

        # Extract with rate limiting
        try:
            print(f"  → Processing with {model_name.upper()}...", flush=True)
            start_time = time.time()
            response = await self.rate_limiter.execute(
                llm.ainvoke, prompt.format_messages(text=chunk_content)
            )
            elapsed = time.time() - start_time

            # Track token usage
            input_tokens = count_tokens(chunk_content, model_name)
            output_tokens = count_tokens(response.content, model_name)
            token_stats["input_tokens"] = input_tokens
            token_stats["output_tokens"] = output_tokens

            # Calculate cost
            cost = estimate_cost(input_tokens, output_tokens, model_name)
            
            print(f"  → Output: {format_tokens(output_tokens)} tokens", flush=True)
            print(f"  → Time: {elapsed:.2f}s", flush=True)
            print(f"  → Cost: {format_cost(cost)}", flush=True)

            # Parse JSON response
            result = json.loads(response.content)
            # Store metadata in the dict (can't set attributes on dict)
            if isinstance(result, dict):
                result["_token_stats"] = token_stats
                result["_source_file"] = source_file
                result["_chunk_id"] = chunk_id
            else:
                # If it's a Pydantic model, set attributes
                result._token_stats = token_stats
                result._source_file = source_file
                result._chunk_id = chunk_id

            # Cache the result (only for non-critical types)
            if extract_type not in self.critical_types:
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

            print(f"  → ✅ Complete", flush=True)
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

        # Check Ollama availability for non-critical types (always check to ensure we use it when available)
        if extract_type not in self.critical_types:
            await self._check_ollama_availability()

        # Get model info for logging
        use_ollama = self._should_use_ollama(extract_type)
        model_name = "ollama" if use_ollama else ("gpt-4o" if extract_type in self.critical_types else "gpt-4o-mini")
        
        # Log model selection reason clearly
        if extract_type in self.critical_types:
            model_reason = "critical extraction (financial/progress) - requires high accuracy"
        elif use_ollama:
            model_reason = "non-critical extraction - using Ollama for cost savings"
        else:
            model_reason = "non-critical extraction - Ollama unavailable, using OpenAI"

        print(f"  🔍 Extracting {extract_type} using {model_name.upper()}")
        print(f"     Reason: {model_reason}")
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
                # Get token stats from dict or object
                if isinstance(result, dict) and "_token_stats" in result:
                    return result, result["_token_stats"]
                elif hasattr(result, "_token_stats"):
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
        consolidated = self._consolidate_results(valid_results, data_class, documents)

        # Calculate confidence with cross-chunk consistency
        confidence, uncertainty_flags = self._calculate_confidence_with_consistency(
            valid_results, len(documents), extract_type
        )
        consolidated.confidence = confidence
        consolidated.uncertainty_flags = uncertainty_flags
        
        # Build source citations
        source_citations = self._build_source_citations(valid_results, extract_type)
        consolidated.source_citations = source_citations

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
        self, results: List[Dict], data_class: Type[ExtractedData], documents: List[Document]
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

    def _calculate_confidence_with_consistency(
        self, results: List[Dict], total_chunks: int, extract_type: str
    ) -> tuple[float, List[str]]:
        """Calculate extraction confidence with cross-chunk consistency checking"""
        if total_chunks == 0:
            return 0.0, []

        successful = len(results)
        data_richness = 0
        uncertainty_flags = []

        # Count non-null fields and check for consistency
        field_values = {}  # Track values across chunks for consistency
        
        for result in results:
            # Count non-null fields
            non_null_count = sum(1 for v in result.values() if v is not None and v != [])
            data_richness += non_null_count
            
            # Track field values for consistency checking
            for key, value in result.items():
                if value is not None and value != []:
                    if key not in field_values:
                        field_values[key] = []
                    field_values[key].append(str(value).lower().strip())

        # Check for inconsistencies (same field with different values across chunks)
        for field, values in field_values.items():
            if len(values) > 1:
                unique_values = set(values)
                if len(unique_values) > 1:
                    # Inconsistency detected
                    uncertainty_flags.append(
                        f"{field}: conflicting values found across chunks ({len(unique_values)} different values)"
                    )

        # Confidence based on success rate, data richness, and consistency
        success_rate = successful / total_chunks
        
        # Calculate average data richness per result (normalize by expected fields ~10)
        expected_fields_per_result = 10  # Rough estimate of fields per extractor type
        avg_richness = min(1.0, (data_richness / (successful * expected_fields_per_result))) if successful > 0 else 0
        
        # Consistency penalty: reduce confidence if there are inconsistencies (less harsh)
        consistency_score = 1.0 - (len(uncertainty_flags) * 0.05)  # Reduced from 0.1
        consistency_score = max(0.7, consistency_score)  # Don't penalize too heavily (raised from 0.5)
        
        # Base confidence calculation - weight data richness more heavily
        base_confidence = success_rate * 0.4 + avg_richness * 0.5 + consistency_score * 0.1
        
        # Additional penalty for missing critical fields (less harsh)
        critical_fields = {
            "financial": ["investment_ask", "current_round_size", "funding_stage"],
            "progress": ["arr", "mrr", "growth_rate_mom"],
            "company": ["company_name", "funding_stage"],
            "market": ["tam", "sam"],
            "team": ["founders"]
        }
        
        critical_missing = []
        if extract_type in critical_fields:
            for critical_field in critical_fields[extract_type]:
                if critical_field not in field_values or not field_values[critical_field]:
                    critical_missing.append(critical_field)
        
        if critical_missing:
            uncertainty_flags.extend([f"Missing critical field: {field}" for field in critical_missing])
            # Less harsh penalty - only reduce by 10% instead of 20%
            base_confidence *= 0.9  # Reduced from 0.8

        final_confidence = min(base_confidence, 0.95)
        # Ensure minimum confidence if we have any data
        if successful > 0 and data_richness > 0:
            final_confidence = max(final_confidence, 0.3)  # Minimum 30% if we extracted something
        
        return final_confidence, uncertainty_flags
    
    def _build_source_citations(
        self, results: List[Dict], extract_type: str
    ) -> Dict[str, List[str]]:
        """Build source citations mapping fields to source documents"""
        citations = {}
        
        for result in results:
            source_file = result.get("_source_file", "unknown")
            
            for key, value in result.items():
                # Skip metadata fields
                if key.startswith("_"):
                    continue
                    
                if value is not None and value != []:
                    if key not in citations:
                        citations[key] = []
                    if source_file not in citations[key]:
                        citations[key].append(source_file)
        
        return citations


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
