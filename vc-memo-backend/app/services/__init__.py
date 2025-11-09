"""Services module - backward compatibility."""

# Re-export for backward compatibility
from app.services.extraction import (
    OptimizedExtractor,
    ExtractionCoordinator,
    EXTRACTION_PROMPTS,
    SemanticRouter,
    ExtractorPlanA,
    ExtractorPlanB,
    ExtractorPlanC,
    ExtractorPlanD,
)

__all__ = [
    "OptimizedExtractor",
    "ExtractionCoordinator",
    "EXTRACTION_PROMPTS",
    "SemanticRouter",
    "ExtractorPlanA",
    "ExtractorPlanB",
    "ExtractorPlanC",
    "ExtractorPlanD",
]
