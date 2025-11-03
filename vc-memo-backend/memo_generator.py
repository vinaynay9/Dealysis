from langchain_core.prompts import ChatPromptTemplate
from llm_config import get_generation_llm
from rate_limiter import RateLimiter
from typing import Dict, Any, List
from datetime import datetime
import asyncio


class MemoGenerator:
    """Generate investment memo sections from extracted data"""

    def __init__(self):
        self.llm = get_generation_llm()
        self.rate_limiter = RateLimiter(
            max_retries=5,
            initial_delay=1.0,
            max_delay=60.0,
        )

    async def generate_complete_memo(
        self, extracted_data: Dict[str, Any], template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate all memo sections based on template"""

        sections = template["sections"]
        memo_sections = {}
        confidence_scores = {}
        flagged_items = []

        # Generate each section sequentially with rate limiting and delays
        for i, section in enumerate(sections):
            section_key = section["key"]
            section_title = section["title"]

            print(f"Generating section {i+1}/{len(sections)}: {section_title}")

            # Map section to relevant extracted data
            relevant_data = self._get_relevant_data(section_key, extracted_data)

            # Generate section content with rate limiting
            content, confidence = await self._generate_section(
                section_title,
                section["description"],
                relevant_data,
                section.get("min_paragraphs", 1),
                section.get("max_paragraphs", 3),
            )

            memo_sections[section_key] = content
            confidence_scores[section_key] = confidence

            # Flag low confidence sections
            if confidence < 0.6:
                flagged_items.append(
                    {
                        "section": section_title,
                        "reason": f"Low confidence ({confidence:.2f}) - may need human review",
                        "missing_data": self._identify_missing_data(
                            section_key, relevant_data
                        ),
                    }
                )

            # Add delay between sections to avoid rate limits (except for last section)
            if i < len(sections) - 1:
                await asyncio.sleep(0.5)  # 500ms delay between sections

        # Compile final memo
        final_memo = self._compile_memo(memo_sections, template)

        return {
            "sections": memo_sections,
            "confidence_scores": confidence_scores,
            "flagged_items": flagged_items,
            "final_memo": final_memo,
        }

    def _get_relevant_data(
        self, section_key: str, extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map extracted data to memo sections"""

        mapping = {
            "exec_summary": ["company", "financial", "market"],
            "company_overview": ["company"],
            "market_opportunity": ["market"],
            "progress_metrics": ["progress"],
            "financial_overview": ["financial"],
            "team": ["team"],
            "thesis_risks": ["market", "company", "financial", "progress"],
            "recommendation": ["progress", "financial", "market", "team"],
        }

        relevant_keys = mapping.get(section_key, None)

        # If section key not in mapping (custom section), use all available data
        if relevant_keys is None:
            relevant_keys = list(extracted_data.keys())

        relevant_data = {}

        for key in relevant_keys:
            if key in extracted_data:
                data = extracted_data[key]
                # Convert Pydantic models to dict
                if hasattr(data, "dict"):
                    relevant_data[key] = data.dict()
                else:
                    relevant_data[key] = data

        return relevant_data

    async def _generate_section(
        self,
        title: str,
        description: str,
        data: Dict[str, Any],
        min_paragraphs: int,
        max_paragraphs: int,
    ) -> tuple[str, float]:
        """Generate a single memo section"""

        prompt = ChatPromptTemplate.from_template(
            """
You are a senior venture capital analyst writing the "{title}" section of an investment memo for your investment committee.

Section description: {description}
Required length: {min_paragraphs} to {max_paragraphs} paragraphs

Available extracted data:
{data}

CRITICAL INSTRUCTIONS - Think like a VC analyst:

1. ANALYTICAL RIGOR:
   - Use ALL specific numbers, metrics, and data points provided. Never omit quantitative information.
   - Include exact amounts (e.g., "$5.2M ARR", "Series A $15M", "45% MoM growth")
   - Include dates, timeframes, and percentages when available
   - Cite specific sources if data came from different documents

2. COMPREHENSIVE DETAIL:
   - Investment ask and funding stage MUST be included if present in the data
   - Use of funds allocation must be included if available
   - All financial metrics (ARR, MRR, burn rate, runway) must be explicitly stated
   - Market size (TAM/SAM/SOM) must be included with exact numbers
   - Team background must include specific past experiences and achievements

3. VC PERSPECTIVE:
   - Analyze the data critically - highlight strengths AND concerns
   - Compare metrics to industry benchmarks where relevant
   - Identify what's impressive vs. what's concerning
   - Note gaps or missing critical information explicitly
   - Consider what matters most to investors at this stage

4. MISSING INFORMATION:
   - If critical data is missing (investment ask, key metrics, etc.), explicitly state: "This information was not provided in the materials"
   - Flag important omissions that would affect investment decision
   - Don't make up or infer data that isn't present

5. PROFESSIONAL TONE:
   - Write in a concise, analytical style typical of VC memos
   - Be objective and data-driven
   - Use professional terminology (ARR, MRR, CAC, LTV, runway, etc.)
   - Structure paragraphs logically with clear topic sentences

SPECIFIC REQUIREMENTS:
- ALWAYS include investment ask/round size if present in financial data
- ALWAYS include use of funds if present
- ALWAYS include funding stage if present
- ALWAYS include exact numerical values (don't round unnecessarily)
- ALWAYS note when critical information is missing

Write the section content now, ensuring you include ALL available details and explicitly note any missing critical information:
"""
        )

        # Use rate limiter to handle API calls with retry logic
        response = await self.rate_limiter.execute(
            self.llm.ainvoke,
            prompt.format_messages(
                title=title,
                description=description,
                min_paragraphs=min_paragraphs,
                max_paragraphs=max_paragraphs,
                data=self._format_data_for_prompt(data),
            ),
        )

        content = response.content

        # Calculate confidence based on data completeness
        confidence = self._calculate_section_confidence(data)

        return content, confidence

    def _format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """Format extracted data for LLM prompt with emphasis on key metrics"""
        formatted = []

        # Define critical fields that should be highlighted
        critical_fields = {
            "financial": [
                "investment_ask",
                "current_round_size",
                "use_of_funds",
                "funding_stage",
                "current_valuation",
                "total_funding_raised",
            ],
            "company": ["funding_stage", "current_round_details", "company_name"],
            "progress": [
                "arr",
                "mrr",
                "burn_rate",
                "runway_months",
                "growth_rate_mom",
                "growth_rate_yoy",
                "cac",
                "ltv",
            ],
            "market": ["tam", "sam", "som", "market_growth_rate"],
        }

        for category, values in data.items():
            if isinstance(values, dict):
                formatted.append(f"\n{category.upper()}:")

                # First, list critical fields if present
                critical_in_category = critical_fields.get(category, [])
                critical_found = []
                regular_fields = []

                for key, value in values.items():
                    if key == "confidence":
                        continue
                    if value:
                        if key in critical_in_category:
                            critical_found.append((key, value))
                        else:
                            regular_fields.append((key, value))

                # Format critical fields with emphasis
                if critical_found:
                    formatted.append("  CRITICAL METRICS:")
                    for key, value in critical_found:
                        formatted.append(f"  ⚠ {key}: {value}")
                    formatted.append("")

                # Format regular fields
                for key, value in regular_fields:
                    formatted.append(f"  - {key}: {value}")

        if not formatted:
            return "No specific data available - this section will need to be written based on general context."

        return "\n".join(formatted)

    def _calculate_section_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence for a section based on available data"""
        if not data:
            return 0.3

        total_confidence = 0
        count = 0

        for category_data in data.values():
            if isinstance(category_data, dict) and "confidence" in category_data:
                total_confidence += category_data["confidence"]
                count += 1

        if count == 0:
            return 0.5

        return min(total_confidence / count, 0.95)

    def _identify_missing_data(
        self, section_key: str, data: Dict[str, Any]
    ) -> List[str]:
        """Identify what data is missing for a section"""
        missing = []

        required_data = {
            "exec_summary": [
                "company_name",
                "investment_ask",
                "current_round_size",
                "funding_stage",
                "current_valuation",
                "use_of_funds",
            ],
            "company_overview": [
                "mission",
                "business_model",
                "products",
                "funding_stage",
            ],
            "market_opportunity": ["tam", "sam", "competitors", "market_growth_rate"],
            "progress_metrics": [
                "arr",
                "mrr",
                "growth_rate_mom",
                "growth_rate_yoy",
                "burn_rate",
            ],
            "financial_overview": [
                "total_funding_raised",
                "investment_ask",
                "current_round_size",
                "use_of_funds",
                "current_valuation",
                "last_valuation",
            ],
            "team": ["founders", "relevant_experience"],
            "thesis_risks": ["competitive_advantages"],
            "recommendation": [],
        }

        required = required_data.get(section_key, [])

        for req in required:
            found = False
            for category_data in data.values():
                if isinstance(category_data, dict) and req in category_data:
                    if category_data[req]:
                        found = True
                        break
            if not found:
                missing.append(req)

        return missing

    def _compile_memo(self, sections: Dict[str, str], template: Dict[str, Any]) -> str:
        """Compile all sections into final memo"""
        memo_parts = [f"# {template['template_name']}\n"]
        memo_parts.append(f"Generated: {datetime.now().isoformat()}\n")
        memo_parts.append("---\n")

        for section in template["sections"]:
            section_key = section["key"]
            section_title = section["title"]

            if section_key in sections:
                memo_parts.append(f"\n## {section_title}\n")
                memo_parts.append(sections[section_key])
                memo_parts.append("\n")

        return "\n".join(memo_parts)
