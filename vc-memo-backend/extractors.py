from langchain_core.prompts import ChatPromptTemplate
from llm_config import get_extraction_llm
from models import (
    ProgressData,
    FinancialData,
    MarketData,
    CompanyData,
    TeamData,
    ExtractedData,
)
from rate_limiter import batch_process_with_rate_limit, RateLimiter
from typing import List, Dict, Any, Type
import asyncio
import json


EXTRACTION_PROMPTS = {
    "progress": """Extract operational progress metrics from this text. Focus on day-to-day business operations.

TEXT: {text}

Extract the following metrics if present:
- ARR (Annual Recurring Revenue)
- MRR (Monthly Recurring Revenue)
- Monthly burn rate
- Runway in months
- Churn rate (monthly/annual)
- Growth rate (MoM/YoY)
- Customer count
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)

Output JSON format:
{{
  "arr": "value if found, null otherwise",
  "mrr": "value if found, null otherwise",
  "burn_rate": "value if found, null otherwise",
  "runway_months": number or null,
  "churn_rate": "value if found, null otherwise",
  "growth_rate_mom": "value if found, null otherwise",
  "growth_rate_yoy": "value if found, null otherwise",
  "customer_count": "value if found, null otherwise",
  "cac": "value if found, null otherwise",
  "ltv": "value if found, null otherwise"
}}

Only include values explicitly stated in the text. Return valid JSON only.""",
    "financial": """Extract high-level funding and cap table information from this text.

TEXT: {text}

Look for:
- Previous funding rounds (Seed, Series A, etc.)
- Total funding raised to date
- Last round valuation
- Current round valuation target
- Ownership percentages by investor type
- Liquidation preferences
- Board composition

Output JSON format:
{{
  "previous_rounds": ["list of rounds like 'Seed $2M', 'Series A $10M'"],
  "total_funding_raised": "total amount if stated",
  "last_valuation": "previous valuation",
  "current_valuation": "current round target",
  "ownership_percentages": {{"founders": "X%", "employees": "Y%", "investors": "Z%"}},
  "liquidation_preferences": "preference details",
  "board_composition": "board member details"
}}

Only extract explicitly stated information. Return valid JSON only.""",
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

Output JSON format:
{{
  "company_name": "name if found",
  "mission": "mission statement",
  "business_model": "how company makes money",
  "products": ["list of products/services"],
  "value_proposition": "key value prop",
  "go_to_market": "GTM strategy"
}}

Return valid JSON only.""",
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


class UniversalExtractor:
    """Single extractor that handles all data types"""

    def __init__(self):
        self.llm = get_extraction_llm()
        self.data_classes = {
            "progress": ProgressData,
            "financial": FinancialData,
            "market": MarketData,
            "company": CompanyData,
            "team": TeamData,
        }
        self.rate_limiter = RateLimiter(
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
        )

    async def _extract_chunk(self, prompt, chunk: str):
        """Extract data from a single chunk with rate limiting"""
        return await self.rate_limiter.execute(
            self.llm.ainvoke, prompt.format_messages(text=chunk[:3000])
        )

    async def extract(self, chunks: List[str], extract_type: str) -> ExtractedData:
        """Extract specific type of data from chunks"""

        if extract_type not in EXTRACTION_PROMPTS:
            raise ValueError(f"Unknown extraction type: {extract_type}")

        prompt_template = EXTRACTION_PROMPTS[extract_type]
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Extract from chunks in batches with rate limiting
        # Process in smaller batches to avoid hitting rate limits
        batch_size = min(5, len(chunks))  # Process max 5 chunks in parallel
        delay_between_batches = 0.5  # 500ms delay between batches

        async def process_chunk(chunk: str):
            return await self._extract_chunk(prompt, chunk)

        responses = await batch_process_with_rate_limit(
            chunks,
            process_chunk,
            batch_size=batch_size,
            delay_between_batches=delay_between_batches,
        )

        # Filter out exceptions
        valid_responses = [r for r in responses if not isinstance(r, Exception)]

        # Consolidate results
        data_class = self.data_classes[extract_type]
        consolidated = self._consolidate_results(valid_responses, data_class)

        # Calculate confidence
        confidence = self._calculate_confidence(valid_responses, len(chunks))
        consolidated.confidence = confidence

        return consolidated

    def _consolidate_results(
        self, responses, data_class: Type[ExtractedData]
    ) -> ExtractedData:
        """Merge results from multiple chunks"""
        results = []

        for response in responses:
            try:
                result = json.loads(response.content)
                results.append(result)
            except (json.JSONDecodeError, AttributeError):
                continue

        if not results:
            return data_class()

        # Consolidation strategy: take first non-null value for each field
        consolidated = {}

        for field in data_class.__fields__:
            if field == "confidence":
                continue

            # Handle different field types
            field_info = data_class.__fields__[field]

            # For list fields, combine unique values
            if hasattr(
                field_info.annotation, "__origin__"
            ) and field_info.annotation.__origin__ in [list, List]:
                all_items = []
                for r in results:
                    if isinstance(r.get(field), list):
                        all_items.extend(r[field])
                if all_items:
                    # Remove duplicates while preserving order
                    seen = set()
                    consolidated[field] = [
                        x for x in all_items if not (x in seen or seen.add(x))
                    ]

            # For dict fields, take first non-empty
            elif hasattr(
                field_info.annotation, "__origin__"
            ) and field_info.annotation.__origin__ in [dict, Dict]:
                for r in results:
                    if r.get(field) and isinstance(r.get(field), dict):
                        consolidated[field] = r[field]
                        break

            # For single values, take first non-null
            else:
                for r in results:
                    if r.get(field) is not None:
                        consolidated[field] = r[field]
                        break

        return data_class(**consolidated)

    def _calculate_confidence(self, responses, total_chunks: int) -> float:
        """Calculate extraction confidence"""
        if total_chunks == 0:
            return 0.0

        successful = len(responses)
        data_richness = 0

        for response in responses:
            try:
                result = json.loads(response.content)
                # Count non-null fields
                data_richness += sum(1 for v in result.values() if v)
            except:
                continue

        # Confidence based on success rate and data richness
        success_rate = successful / total_chunks
        avg_richness = (data_richness / (successful * 10)) if successful > 0 else 0

        return min(success_rate * 0.7 + avg_richness * 0.3, 0.95)


class ExtractionCoordinator:
    """Coordinates all extractions in parallel"""

    def __init__(self):
        self.extractor = UniversalExtractor()
        self.extract_types = ["progress", "financial", "market", "company", "team"]

    async def extract_all(self, chunks: List[str]) -> Dict[str, Any]:
        """Run all extractors in parallel"""

        print(f"Running extraction on {len(chunks)} chunks...")

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
