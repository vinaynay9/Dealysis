"""Extraction prompts for all extraction types."""

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

