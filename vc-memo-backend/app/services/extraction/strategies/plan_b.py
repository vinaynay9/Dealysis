"""
Plan B: Enhanced Prompts + Post-Processing Layer
Improves prompts with explicit examples and adds validation/fixing layer
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
    estimate_ollama_tokens,
    estimate_cost,
    format_cost,
    format_tokens,
)
from app.utils.validation.data_validator import DataValidator
from app.services.llm.local_llm import get_local_llm
from typing import List, Dict, Any, Type, Optional
import asyncio
import json
import tiktoken
import time
import sys

# Enhanced prompts with explicit examples and type requirements
ENHANCED_EXTRACTION_PROMPTS = {
    "progress": """Extract operational progress metrics from this text. Focus on day-to-day business operations.

TEXT: {text}

CRITICAL ACCURACY REQUIREMENTS:
- Extract ONLY information that is explicitly stated in the text
- If a metric is NOT mentioned, you MUST return null (not a placeholder, not an estimate, not an inference)
- NEVER invent, estimate, or infer values that are not directly stated
- If you are uncertain about a value, return null
- If the text mentions a metric but the exact value is unclear, return null

CRITICAL TYPE REQUIREMENTS:
- customer_count MUST be a STRING, e.g., "45" NOT 45 (number)
- All monetary values MUST be strings with currency, e.g., "$2.4 million" NOT 2400000
- runway_months MUST be a NUMBER (integer), e.g., 18 NOT "18"
- All percentage values MUST be strings, e.g., "15%" NOT 15

EXAMPLE CORRECT OUTPUT:
{{
  "arr": "$2.4 million in 2024",
  "mrr": "$200,000",
  "burn_rate": "$180,000 per month",
  "runway_months": 18,
  "churn_rate": "3%",
  "growth_rate_mom": "15%",
  "growth_rate_yoy": "120%",
  "customer_count": "45",
  "cac": "$12,000",
  "ltv": "$180,000"
}}

Extract the following metrics ONLY if explicitly present:
- ARR (Annual Recurring Revenue) - include exact amounts with currency
- MRR (Monthly Recurring Revenue) - include exact amounts with currency
- Monthly burn rate - include exact amounts
- Runway in months - include exact number
- Churn rate (monthly/annual) - include percentages
- Growth rate (MoM/YoY) - include percentages and timeframes
- Customer count - include exact numbers (AS A STRING)
- CAC (Customer Acquisition Cost) - include exact amounts
- LTV (Lifetime Value) - include exact amounts

Output JSON format:
{{
  "arr": "exact value if explicitly stated (include currency and time period), null if not mentioned",
  "mrr": "exact value if explicitly stated (include currency and time period), null if not mentioned",
  "burn_rate": "exact value if explicitly stated (include currency and period), null if not mentioned",
  "runway_months": exact number if explicitly stated, null if not mentioned,
  "churn_rate": "exact value if explicitly stated (include period), null if not mentioned",
  "growth_rate_mom": "exact value if explicitly stated (include percentage), null if not mentioned",
  "growth_rate_yoy": "exact value if explicitly stated (include percentage), null if not mentioned",
  "customer_count": "exact value as STRING if explicitly stated (e.g., '45' not 45), null if not mentioned",
  "cac": "exact value if explicitly stated (include currency), null if not mentioned",
  "ltv": "exact value if explicitly stated (include currency), null if not mentioned"
}}

STRICT RULES:
1. Return null for any field where the information is not explicitly stated in the text
2. Do NOT use placeholder values like "N/A", "unknown", "not specified" - use null
3. Do NOT estimate or infer values based on context
4. Do NOT make assumptions about what the value "probably" is
5. If you cannot find the exact information, return null - this is correct behavior
6. customer_count MUST be a STRING type, not a number

IMPORTANT: Capture ONLY numerical values, dates, and metrics that are explicitly mentioned. Include context like time periods, currencies, and units when available. Return valid JSON only.""",
    
    "financial": """Extract high-level funding and cap table information from this text.

TEXT: {text}

CRITICAL ACCURACY REQUIREMENTS:
- Extract ONLY information that is explicitly stated in the text
- If a field is NOT mentioned, you MUST return null (not a placeholder, not an estimate, not an inference)
- NEVER invent, estimate, or infer values that are not directly stated
- If you are uncertain about a value, return null
- If the text mentions something but the exact value is unclear, return null

EXAMPLE CORRECT OUTPUT:
{{
  "previous_rounds": ["Seed $2.5M (June 2023)"],
  "total_funding_raised": "$2.5 million",
  "last_valuation": "$8 million (Seed round, June 2023)",
  "current_valuation": "$32 million post-money",
  "investment_ask": "$8 million",
  "current_round_size": "$8 million",
  "use_of_funds": "40% sales and marketing, 35% product development, 25% operations",
  "ownership_percentages": {{"founders": "25.0%", "employees": "8.3%", "investors": "8.3%"}},
  "liquidation_preferences": null,
  "board_composition": null
}}

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

EXAMPLE CORRECT OUTPUT:
{{
  "tam": "$45 billion globally",
  "sam": "$8.5 billion in North America enterprise market",
  "som": "$420 million addressable in next 3 years",
  "market_growth_rate": "18% CAGR over next 5 years",
  "target_segments": ["Fortune 500 manufacturing companies", "large retail chains", "e-commerce platforms"],
  "competitors": ["SAP", "Oracle", "Blue Yonder", "Kinaxis"],
  "competitive_advantages": ["AI-first architecture", "40% average cost reduction", "faster implementation"]
}}

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

EXAMPLE CORRECT OUTPUT:
{{
  "company_name": "Nexus AI",
  "mission": "Optimize global supply chains with AI to reduce waste, improve efficiency, and enable sustainable operations.",
  "business_model": "SaaS subscription + professional services",
  "products": ["Nexus Optimizer", "Nexus Predict", "Nexus Connect"],
  "value_proposition": "Reduce supply chain costs by 40% with AI-powered optimization",
  "go_to_market": "Enterprise sales + strategic partnerships with SAP, Oracle",
  "funding_stage": "Series A",
  "current_round_details": "Raising $8 million Series A at $32 million post-money valuation"
}}

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

CRITICAL TYPE REQUIREMENTS:
- founders MUST be a list of objects with name, title, background (all strings)
- key_employees, advisors, board_members, past_exits, relevant_experience MUST be lists of STRINGS, not objects

EXAMPLE CORRECT OUTPUT:
{{
  "founders": [
    {{"name": "Sarah Chen", "title": "CEO", "background": "Former VP at Amazon Supply Chain"}},
    {{"name": "Michael Rodriguez", "title": "CTO", "background": "Former Google AI researcher"}}
  ],
  "key_employees": ["James Park, VP of Sales", "Lisa Wang, VP of Engineering"],
  "advisors": ["Robert Thompson, Former CEO of FedEx Supply Chain"],
  "board_members": ["Sarah Chen", "Michael Rodriguez"],
  "past_exits": ["Sarah Chen sold previous logistics startup to Oracle for $50 million in 2019"],
  "relevant_experience": ["Combined 40+ years in supply chain optimization and AI/ML"]
}}

Look for ONLY explicitly stated information:
- Founders (names, titles, backgrounds) - ONLY if explicitly stated with at least name
- Key employees - ONLY if explicitly named (return as STRING, not object)
- Advisors - ONLY if explicitly named (return as STRING, not object)
- Board members - ONLY if explicitly named (return as STRING, not object)
- Past exits or successes - ONLY if explicitly described (return as STRING, not object)
- Relevant industry experience - ONLY if explicitly described (return as STRING, not object)

Output JSON format:
{{
  "founders": [{{"name": "exact name if stated", "title": "exact title if stated", "background": "exact background if stated"}}] - empty list if not mentioned,
  "key_employees": ["exact list of key employees as STRINGS if explicitly named, empty list if not mentioned"],
  "advisors": ["exact list of advisors as STRINGS if explicitly named, empty list if not mentioned"],
  "board_members": ["exact list of board members as STRINGS if explicitly named, empty list if not mentioned"],
  "past_exits": ["exact list of exits as STRINGS if explicitly described, empty list if not mentioned"],
  "relevant_experience": ["exact list of experience points as STRINGS if explicitly described, empty list if not mentioned"]
}}

STRICT RULES:
1. Return empty list [] for any field where the information is not explicitly stated in the text
2. Do NOT use placeholder values like "N/A", "unknown", "not specified" - use empty list
3. Do NOT estimate or infer values based on context
4. Do NOT make assumptions about what the value "probably" is
5. If you cannot find the exact information, return empty list - this is correct behavior
6. For founders: only include if at least the name is explicitly stated. If only partial info is available, include what is stated and use null for missing fields.
7. key_employees, advisors, board_members, past_exits, relevant_experience MUST be lists of STRINGS, not objects

Return valid JSON only.""",
}


class ExtractorPlanB:
    """Plan B: Enhanced prompts with post-processing validation layer"""

    def __init__(self, cache_dir: str = "runtime/cache", use_cache: bool = True):
        # Use gpt-4o-mini for less critical extractions, gpt-4o for critical ones
        self.mini_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        self.full_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

        # Use full model for critical extractions that need precision
        self.critical_types = ["financial", "progress"]  # These need high accuracy
        
        # Check if Ollama is available for non-critical extractions
        self.local_llm = get_local_llm()
        self.ollama_available = False
        if self.local_llm:
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

        self.use_cache = use_cache
        self.cache = SummaryCache(cache_dir) if use_cache else None
        self.rate_limiter = RateLimiter(
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
        )
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.max_concurrent = 2

    async def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available (lazy check)"""
        if self._ollama_checked:
            return self.ollama_available
        
        if not self.local_llm:
            self._ollama_checked = True
            self.ollama_available = False
            return False
        
        try:
            available = await self.local_llm.is_available()
            self.ollama_available = available
            self._ollama_checked = True
            return available
        except:
            self.ollama_available = False
            self._ollama_checked = True
            return False

    def _should_use_ollama(self, extract_type: str) -> bool:
        """Determine if Ollama should be used for this extraction type"""
        if extract_type in self.critical_types:
            return False
        return self.ollama_available

    def _get_model_for_type(self, extract_type: str) -> ChatOpenAI:
        """Get appropriate model for extraction type"""
        if extract_type in self.critical_types:
            return self.full_llm
        return self.mini_llm

    async def _extract_from_chunk(
        self, doc: Document, extract_type: str
    ) -> Dict[str, Any]:
        """Extract data from a single chunk with validation"""
        source_file = doc.metadata.get("source_file", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        
        token_stats = {
            "model": "unknown",
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_hit": False,
        }

        # Try Ollama first for non-critical types
        if extract_type not in self.critical_types:
            await self._check_ollama_availability()
            if self._should_use_ollama(extract_type):
                try:
                    print(f"  → Using Ollama (llama3.2:3b) for cost-effective extraction...", flush=True)
                    start_time = time.time()
                    prompt_template = ENHANCED_EXTRACTION_PROMPTS[extract_type]
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
                    
                    if isinstance(result, dict):
                        result["_token_stats"] = token_stats
                        result["_source_file"] = source_file
                        result["_chunk_id"] = chunk_id
                    
                    # Apply validation and fixing
                    result = self._validate_and_fix_result(result, extract_type)
                    
                    print(f"  → Output: {format_tokens(output_tokens)} tokens", flush=True)
                    print(f"  → Time: {elapsed:.2f}s", flush=True)
                    print(f"  → Cost: {format_cost(0.0)} (Ollama)", flush=True)
                    
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
                        cost_estimate=0.0,
                    )
                    
                    print(f"  → ✅ Complete", flush=True)
                    return result
                except Exception as e:
                    print(f"  → ⚠️  Ollama extraction failed: {e}", flush=True)
                    print(f"  → Falling back to OpenAI", flush=True)

        # Get appropriate model (OpenAI)
        llm = self._get_model_for_type(extract_type)
        model_name = "gpt-4o" if extract_type in self.critical_types else "gpt-4o-mini"
        token_stats["model"] = model_name

        # Prepare prompt
        prompt_template = ENHANCED_EXTRACTION_PROMPTS[extract_type]
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Limit input size
        max_input_tokens = 4000 if extract_type in self.critical_types else 3000
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

        # Extract with rate limiting
        try:
            print(f"  → Processing with {model_name.upper()}...", flush=True)
            start_time = time.time()
            response = await self.rate_limiter.execute(
                llm.ainvoke, prompt.format_messages(text=chunk_content)
            )
            elapsed = time.time() - start_time

            input_tokens = count_tokens(chunk_content, model_name)
            output_tokens = count_tokens(response.content, model_name)
            token_stats["input_tokens"] = input_tokens
            token_stats["output_tokens"] = output_tokens

            cost = estimate_cost(input_tokens, output_tokens, model_name)
            
            print(f"  → Output: {format_tokens(output_tokens)} tokens", flush=True)
            print(f"  → Time: {elapsed:.2f}s", flush=True)
            print(f"  → Cost: {format_cost(cost)}", flush=True)

            # Parse JSON response
            result = json.loads(response.content)
            
            # Apply validation and fixing
            result = self._validate_and_fix_result(result, extract_type)
            
            if isinstance(result, dict):
                result["_token_stats"] = token_stats
                result["_source_file"] = source_file
                result["_chunk_id"] = chunk_id

            if self.use_cache and extract_type not in self.critical_types:
                await self.cache.store_summary(
                    text=doc.page_content,
                    summary=json.dumps(result),
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
            try:
                cleaned = response.content.strip()
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

    def _validate_and_fix_result(self, result: Dict[str, Any], extract_type: str) -> Dict[str, Any]:
        """Apply validation and fixing based on extraction type"""
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
        if extract_type not in ENHANCED_EXTRACTION_PROMPTS:
            raise ValueError(f"Unknown extraction type: {extract_type}")

        if not documents:
            print(f"  ⚠ {extract_type}: No chunks assigned, skipping")
            return self.data_classes[extract_type]()

        if extract_type not in self.critical_types:
            await self._check_ollama_availability()

        use_ollama = self._should_use_ollama(extract_type)
        model_name = "ollama" if use_ollama else ("gpt-4o" if extract_type in self.critical_types else "gpt-4o-mini")
        
        print(f"  🔍 Extracting {extract_type} using {model_name.upper()} (Plan B: Enhanced Prompts + Validation)")
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

        if model_name == "gpt-4o":
            cost = (input_tokens_total / 1_000_000 * 2.50) + (output_tokens_total / 1_000_000 * 10.00)
        elif model_name == "ollama":
            cost = 0.0
        else:
            cost = (input_tokens_total / 1_000_000 * 0.15) + (output_tokens_total / 1_000_000 * 0.60)

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
            "model": model_name,
        }

        return consolidated

