"""Extraction services module."""

# Backward compatibility imports
from app.services.extraction.base import OptimizedExtractor, ExtractionCoordinator
from app.services.extraction.prompts import EXTRACTION_PROMPTS
from app.services.extraction.claude_extractor import ClaudeExtractor
from app.services.extraction.semantic_router import SemanticRouter
from app.services.extraction.strategies.plan_a import ExtractorPlanA
from app.services.extraction.strategies.plan_b import ExtractorPlanB
from app.services.extraction.strategies.plan_c import ExtractorPlanC
from app.services.extraction.strategies.plan_d import ExtractorPlanD

__all__ = [
    "OptimizedExtractor",
    "ExtractionCoordinator",
    "EXTRACTION_PROMPTS",
    "ClaudeExtractor",
    "SemanticRouter",
    "ExtractorPlanA",
    "ExtractorPlanB",
    "ExtractorPlanC",
    "ExtractorPlanD",
]




