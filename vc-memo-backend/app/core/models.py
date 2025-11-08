from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MemoState(TypedDict):
    """State for LangGraph pipeline"""

    job_id: str
    uploaded_documents: List[Dict[str, Any]]
    template_structure: Dict[str, Any]
    parsed_chunks: List[str]
    routed_chunks: Dict[str, List[Any]]  # Maps extractor names to their assigned chunks
    context_links: Dict[str, List[str]]  # Maps extractor names to related chunk IDs for context enrichment
    financial_analyses: List[Dict[str, Any]]
    extracted_data: Dict[str, Any]
    memo_sections: Dict[str, str]
    confidence_scores: Dict[str, float]
    flagged_items: List[Dict[str, str]]
    uncertainty_flags: List[Dict[str, Any]]  # List of uncertainty flags with details
    final_memo: str
    processing_stage: str
    error_messages: List[str]


class ExtractedData(BaseModel):
    """Base class for all extracted data types"""

    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty_flags: List[str] = Field(default_factory=list, description="List of fields with uncertain or missing data")
    source_citations: Dict[str, List[str]] = Field(default_factory=dict, description="Map of field names to source document names")

    class Config:
        extra = "allow"


class ProgressData(ExtractedData):
    """Operational metrics"""

    arr: Optional[str] = None
    mrr: Optional[str] = None
    burn_rate: Optional[str] = None
    runway_months: Optional[int] = None
    churn_rate: Optional[str] = None
    growth_rate_mom: Optional[str] = None
    growth_rate_yoy: Optional[str] = None
    customer_count: Optional[str] = None
    cac: Optional[str] = None
    ltv: Optional[str] = None


class FinancialData(ExtractedData):
    """Funding & cap table info"""

    previous_rounds: Optional[List[str]] = None
    total_funding_raised: Optional[str] = None
    last_valuation: Optional[str] = None
    current_valuation: Optional[str] = None
    investment_ask: Optional[str] = None  # Amount company is raising in current round
    current_round_size: Optional[str] = (
        None  # Alternative field name for investment ask
    )
    use_of_funds: Optional[str] = None  # How funds will be allocated
    ownership_percentages: Optional[Dict[str, str]] = None
    liquidation_preferences: Optional[str] = None
    board_composition: Optional[str] = None


class MarketData(ExtractedData):
    """Market analysis"""

    tam: Optional[str] = None
    sam: Optional[str] = None
    som: Optional[str] = None
    market_growth_rate: Optional[str] = None
    target_segments: Optional[List[str]] = None
    competitors: Optional[List[str]] = None
    competitive_advantages: Optional[List[str]] = None


class CompanyData(ExtractedData):
    """Company overview"""

    company_name: Optional[str] = None
    mission: Optional[str] = None
    business_model: Optional[str] = None
    products: Optional[List[str]] = None
    value_proposition: Optional[str] = None
    go_to_market: Optional[str] = None
    funding_stage: Optional[str] = None  # Seed, Series A, Series B, etc.
    current_round_details: Optional[str] = None  # Round name, target amount, etc.


class TeamData(ExtractedData):
    """Team information"""

    founders: Optional[List[Dict[str, str]]] = None
    key_employees: Optional[List[str]] = None
    advisors: Optional[List[str]] = None
    board_members: Optional[List[str]] = None
    past_exits: Optional[List[str]] = None
    relevant_experience: Optional[List[str]] = None


# Default VC memo template structure
DEFAULT_TEMPLATE = {
    "template_name": "Standard VC Investment Memo",
    "sections": [
        {
            "title": "Executive Summary",
            "key": "exec_summary",
            "required": True,
            "min_paragraphs": 1,
            "max_paragraphs": 2,
            "description": "Company overview, stage, investment ask, and thesis",
        },
        {
            "title": "Company Overview",
            "key": "company_overview",
            "required": True,
            "min_paragraphs": 2,
            "max_paragraphs": 3,
            "description": "Mission, business model, products, and value proposition",
        },
        {
            "title": "Market Opportunity",
            "key": "market_opportunity",
            "required": True,
            "min_paragraphs": 2,
            "max_paragraphs": 4,
            "description": "TAM, SAM, SOM, competitive landscape",
        },
        {
            "title": "Progress & Metrics",
            "key": "progress_metrics",
            "required": True,
            "min_paragraphs": 2,
            "max_paragraphs": 3,
            "description": "ARR, MRR, growth, churn, unit economics",
        },
        {
            "title": "Financial Overview",
            "key": "financial_overview",
            "required": True,
            "min_paragraphs": 1,
            "max_paragraphs": 2,
            "description": "Funding history, cap table, valuation",
        },
        {
            "title": "Management Team",
            "key": "team",
            "required": True,
            "min_paragraphs": 1,
            "max_paragraphs": 2,
            "description": "Founder backgrounds, relevant experience",
        },
        {
            "title": "Investment Thesis & Risks",
            "key": "thesis_risks",
            "required": True,
            "min_paragraphs": 2,
            "max_paragraphs": 3,
            "description": "Why invest, key risks, mitigation strategies",
        },
        {
            "title": "Recommendation",
            "key": "recommendation",
            "required": True,
            "min_paragraphs": 1,
            "max_paragraphs": 1,
            "description": "Investment decision with rationale",
        },
    ],
}
