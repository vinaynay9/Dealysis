# Code Structure Refactoring Plan

## Overview

This document outlines the proposed refactoring of the `vc-memo-backend` codebase to improve organization, maintainability, and reduce technical debt. The refactoring will reorganize files into a clear domain-driven structure while maintaining backward compatibility.

## Current Issues

### 1. **Extractors Organization**

- `extractors.py` is 941 lines (too large, violates single responsibility)
- 4 plan files (`extractors_plan_a.py`, `extractors_plan_b.py`, etc.) scattered in services/
- No clear separation between base extractor and strategy implementations

### 2. **Services Directory**

- 13 files in flat structure
- Mix of core services (pipeline, extractors) and supporting services (document_parser, semantic_router)
- No clear grouping by domain

### 3. **Utils Directory**

- 9 utility files in flat structure
- Mix of concerns: caching, rate limiting, token counting, text processing, LLM setup
- Should be grouped by purpose

### 4. **Tests Organization**

- All tests at root of `tests/` directory
- No mirroring of app structure
- Hard to find tests for specific modules

### 5. **Documentation**

- Markdown files scattered at root (`IMPLEMENTATION_SUMMARY.md`, `OPENAI_API_CALL_ANALYSIS.md`)
- No `docs/` directory
- Documentation mixed with code

### 6. **Runtime Artifacts**

- `cache/` directory at root (should be in `.gitignore` or `runtime/`)
- Output files in `mock-data/outputs/` (should be in separate `outputs/` or `runtime/`)

## Proposed Refactored Structure

```
vc-memo-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── cli.py                     # CLI entry point
│   │
│   ├── api/                       # API layer
│   │   ├── __init__.py
│   │   ├── routes.py              # API endpoints (upload, status, memo download)
│   │   └── dependencies.py        # API dependencies (auth, validation, etc.)
│   │
│   ├── core/                      # Core domain models and config
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management (API keys, settings)
│   │   ├── models.py              # Pydantic models (ExtractedData, MemoState, etc.)
│   │   └── constants.py           # Constants and enums (JobStatus, DEFAULT_TEMPLATE)
│   │
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   │
│   │   ├── extraction/            # Extraction domain
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base OptimizedExtractor class (core extraction logic)
│   │   │   ├── coordinator.py    # ExtractionCoordinator (orchestrates all extractions)
│   │   │   ├── prompts.py        # EXTRACTION_PROMPTS dictionary (all prompt templates)
│   │   │   ├── strategies/        # Extraction strategies
│   │   │   │   ├── __init__.py
│   │   │   │   ├── baseline.py    # Baseline strategy (current OptimizedExtractor)
│   │   │   │   ├── plan_a.py      # Plan A: Structured outputs (JSON mode + schema)
│   │   │   │   ├── plan_b.py      # Plan B: Enhanced prompts + validation layer
│   │   │   │   ├── plan_c.py      # Plan C: Hybrid (GPT-4o + Claude Sonnet)
│   │   │   │   └── plan_d.py      # Plan D: Cost-optimized (GPT-4o-mini with retry)
│   │   │   ├── claude_extractor.py # Claude Sonnet 4.5 integration
│   │   │   └── semantic_router.py  # Routes chunks to relevant extractors using embeddings
│   │   │
│   │   ├── document/              # Document processing
│   │   │   ├── __init__.py
│   │   │   ├── parser.py          # LangChainDocumentParser (parses PDF, DOCX, XLSX, etc.)
│   │   │   └── chunker.py         # Smart chunking logic (token-aware, context-preserving)
│   │   │
│   │   ├── generation/            # Memo generation
│   │   │   ├── __init__.py
│   │   │   ├── memo_generator.py  # Generates investment memo from extracted data
│   │   │   └── template_parser.py # Parses memo templates (YAML, structured format)
│   │   │
│   │   ├── analysis/              # Analysis services
│   │   │   ├── __init__.py
│   │   │   └── financial_analyzer.py # Analyzes Excel/CSV financial files
│   │   │
│   │   ├── pipeline/              # Pipeline orchestration
│   │   │   ├── __init__.py
│   │   │   └── pipeline.py       # LangGraph pipeline (orchestrates entire memo generation)
│   │   │
│   │   └── llm/                   # LLM services
│   │       ├── __init__.py
│   │       └── local_llm.py       # Ollama integration (local LLM for cost savings)
│   │
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       │
│       ├── caching/               # Caching utilities
│       │   ├── __init__.py
│       │   └── summary_cache.py  # SQLite-based cache for LLM responses
│       │
│       ├── llm/                   # LLM utilities
│       │   ├── __init__.py
│       │   ├── rate_limiter.py    # Rate limiting for API calls (exponential backoff)
│       │   ├── token_counter.py  # Token counting and cost estimation
│       │   └── ollama_setup.py   # Ollama installation and setup automation
│       │
│       ├── text/                  # Text processing
│       │   ├── __init__.py
│       │   ├── preprocessor.py   # Text preprocessing (cleaning, normalization)
│       │   └── chunker.py         # Smart chunker (from smart_chunker.py)
│       │
│       └── validation/            # Data validation
│           ├── __init__.py
│           ├── data_validator.py  # Type coercion and validation (fixes extraction issues)
│           └── json_schema.py     # Pydantic-to-JSON-Schema conversion
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration and shared fixtures
│   │
│   ├── unit/                      # Unit tests
│   │   ├── __init__.py
│   │   ├── test_extractors.py    # Test individual extractors
│   │   ├── test_validators.py    # Test data validation
│   │   ├── test_token_counter.py # Test token counting
│   │   └── ...
│   │
│   ├── integration/               # Integration tests
│   │   ├── __init__.py
│   │   ├── test_pipeline.py      # Test full pipeline
│   │   ├── test_api.py           # Test API endpoints
│   │   └── ...
│   │
│   ├── comparison/                # Comparison tests
│   │   ├── __init__.py
│   │   ├── test_all_extraction_plans.py # Compare all extraction strategies
│   │   └── extraction_comparison.ipynb  # Jupyter notebook for analysis
│   │
│   └── fixtures/                  # Test fixtures
│       ├── __init__.py
│       └── sample_documents.py    # Sample documents for testing
│
├── config/                         # Configuration files
│   ├── render.yaml                # Render.com deployment config
│   ├── template_standard.yaml     # Standard memo template
│   └── logging.yaml               # Logging configuration (if needed)
│
├── docs/                           # Documentation
│   ├── README.md                  # Main README (links to other docs)
│   ├── ARCHITECTURE.md            # Architecture overview
│   ├── API.md                     # API documentation
│   ├── IMPLEMENTATION_SUMMARY.md  # Implementation details
│   └── OPENAI_API_CALL_ANALYSIS.md # API call analysis
│
├── mock-data/                      # Test data
│   ├── nexus-ai/                  # Nexus AI test documents
│   ├── zinnia/                    # Zinnia test documents
│   └── README.md                  # Mock data documentation
│
├── runtime/                        # Runtime artifacts (gitignored)
│   ├── cache/                     # SQLite cache database
│   └── outputs/                  # Generated outputs (memos, summaries)
│       └── .gitkeep
│
├── .env.example
├── requirements.txt
├── runtime.txt
└── README.md                       # Quick start guide (links to docs/)
```

## File Descriptions

### API Layer (`app/api/`)

- **`routes.py`**: FastAPI route handlers for memo generation API endpoints
  - `POST /upload-and-process`: Upload documents and start processing
  - `GET /status/{job_id}`: Check processing status
  - `GET /memo/{job_id}`: Get completed memo
  - `GET /memo/{job_id}/download`: Download memo as markdown
  - `DELETE /job/{job_id}`: Delete a job
  - `GET /health`: Health check endpoint
- **`dependencies.py`**: API dependencies like authentication, request validation, error handlers

### Core (`app/core/`)

- **`config.py`**: Configuration management
  - Environment variable loading
  - API key management (OpenAI, Anthropic)
  - Ollama configuration
  - LLM instance creation helpers
- **`models.py`**: Pydantic data models
  - `ExtractedData`: Base class for all extracted data types
  - `ProgressData`, `FinancialData`, `MarketData`, `CompanyData`, `TeamData`: Specific extraction types
  - `MemoState`: Pipeline state management
  - `JobStatus`: Enum for job statuses
- **`constants.py`**: Constants and default values
  - `DEFAULT_TEMPLATE`: Default memo template structure
  - Extraction type constants
  - Model configuration constants

### Extraction Services (`app/services/extraction/`)

- **`base.py`**: Base extractor class
  - `OptimizedExtractor`: Core extraction logic with caching and model selection
  - Handles chunk processing, result consolidation, confidence scoring
  - Model selection (GPT-4o for critical, GPT-4o-mini/Ollama for non-critical)
- **`coordinator.py`**: Extraction coordinator
  - `ExtractionCoordinator`: Orchestrates parallel extraction across all types
  - Manages extraction tasks and aggregates results
- **`prompts.py`**: Extraction prompts
  - `EXTRACTION_PROMPTS`: Dictionary of prompt templates for each extraction type
  - Centralized prompt management
- **`strategies/baseline.py`**: Baseline extraction strategy
  - Current `OptimizedExtractor` implementation
  - Uses GPT-4o for critical, GPT-4o-mini/Ollama for non-critical
- **`strategies/plan_a.py`**: Plan A - Structured Outputs
  - Uses OpenAI JSON mode with schema enforcement
  - All extractions use GPT-4o for maximum quality
- **`strategies/plan_b.py`**: Plan B - Enhanced Prompts + Validation
  - Enhanced prompts with explicit examples and type requirements
  - Post-processing validation layer using `DataValidator`
- **`strategies/plan_c.py`**: Plan C - Hybrid Model Strategy
  - Uses Claude Sonnet 4.5 for complex extractions (team, company)
  - Uses GPT-4o for critical metrics (financial, progress)
  - Uses GPT-4o-mini for simple extractions (market)
- **`strategies/plan_d.py`**: Plan D - Cost-Optimized
  - Uses GPT-4o-mini for all extractions
  - Retries with GPT-4o on validation failure
  - Maximum cost efficiency
- **`claude_extractor.py`**: Claude integration
  - `ClaudeExtractor`: Wrapper for Anthropic Claude API
  - Handles JSON extraction from Claude responses
  - Cost estimation for Claude Sonnet 4.5
- **`semantic_router.py`**: Semantic routing
  - `SemanticRouter`: Routes document chunks to relevant extractors using embeddings
  - Reduces unnecessary API calls by only sending chunks to relevant extractors
  - Uses OpenAI `text-embedding-3-small` for similarity matching

### Document Services (`app/services/document/`)

- **`parser.py`**: Document parser
  - `LangChainDocumentParser`: Parses various document formats (PDF, DOCX, XLSX, etc.)
  - Uses LangChain document loaders
  - Extracts text and metadata from documents
- **`chunker.py`**: Smart chunking
  - Token-aware chunking that preserves context
  - Two-stage process: semantic chunking then token-aware splitting
  - Ensures chunks fit within LLM token limits

### Generation Services (`app/services/generation/`)

- **`memo_generator.py`**: Memo generator
  - `MemoGenerator`: Generates investment memo from extracted data
  - Uses template structure to organize memo sections
  - Calculates confidence scores and flags uncertain data
- **`template_parser.py`**: Template parser
  - `TemplateParser`: Parses memo templates (YAML format)
  - Extracts section structure and requirements
  - Validates template format

### Analysis Services (`app/services/analysis/`)

- **`financial_analyzer.py`**: Financial analyzer
  - `FinancialAnalyzer`: Analyzes Excel/CSV financial files
  - Extracts financial metrics and trends
  - Performs financial calculations and analysis

### Pipeline (`app/services/pipeline/`)

- **`pipeline.py`**: Pipeline orchestration
  - `create_memo_pipeline()`: Creates LangGraph pipeline
  - Defines pipeline nodes: parse, route, extract, analyze, generate
  - Manages pipeline state and error handling

### LLM Services (`app/services/llm/`)

- **`local_llm.py`**: Local LLM integration
  - `get_local_llm()`: Gets Ollama LLM instance
  - Handles Ollama availability checking
  - Auto-setup functionality for development

### Caching Utilities (`app/utils/caching/`)

- **`summary_cache.py`**: Summary cache
  - `SummaryCache`: SQLite-based cache for LLM responses
  - Reduces API costs by caching identical requests
  - Tracks cache hits and access statistics

### LLM Utilities (`app/utils/llm/`)

- **`rate_limiter.py`**: Rate limiter
  - `RateLimiter`: Handles API rate limiting with exponential backoff
  - Retries failed requests with increasing delays
  - Prevents hitting API rate limits
- **`token_counter.py`**: Token counter
  - Token counting functions for different models
  - Cost estimation based on token usage
  - Formatting helpers for token/cost display
- **`ollama_setup.py`**: Ollama setup
  - Automated Ollama installation and configuration
  - Model downloading and service management
  - Development environment setup helpers

### Text Utilities (`app/utils/text/`)

- **`preprocessor.py`**: Text preprocessor
  - Text cleaning and normalization
  - Removes noise and standardizes format
- **`chunker.py`**: Text chunker
  - Smart text chunking algorithms
  - Context-aware splitting

### Validation Utilities (`app/utils/validation/`)

- **`data_validator.py`**: Data validator
  - `DataValidator`: Validates and fixes extracted data
  - Type coercion (e.g., int to string for `customer_count`)
  - Fixes common extraction issues
- **`json_schema.py`**: JSON schema utilities
  - Converts Pydantic models to JSON Schema
  - Used for structured outputs in Plan A

## Migration Strategy

### Phase 1: Create New Directory Structure

1. Create all new subdirectories
2. Add `__init__.py` files to maintain Python packages

### Phase 2: Move Files Incrementally

1. Move files one domain at a time (extraction, document, generation, etc.)
2. Update imports after each move
3. Run tests after each move to ensure nothing breaks

### Phase 3: Update All Imports

1. Use find/replace with careful verification
2. Update `__init__.py` files to expose public APIs
3. Ensure backward compatibility during transition

### Phase 4: Move Configuration and Documentation

1. Move config files to `config/`
2. Move documentation to `docs/`
3. Update references in code

### Phase 5: Organize Tests

1. Move tests to appropriate subdirectories
2. Create shared fixtures in `tests/fixtures/`
3. Update test imports

### Phase 6: Update Runtime Artifacts

1. Move `cache/` to `runtime/cache/`
2. Move `mock-data/outputs/` to `runtime/outputs/`
3. Update `.gitignore`
4. Update all code references

## Benefits

1. **Better Organization**: Clear separation of concerns by domain
2. **Easier Navigation**: Related files grouped together
3. **Scalability**: Easy to add new extraction strategies, services, or utilities
4. **Maintainability**: Smaller, focused files instead of large monoliths
5. **Testability**: Tests mirror app structure, easier to find and maintain
6. **Documentation**: Centralized in `docs/` directory
7. **Configuration**: All config files in one place
8. **Runtime Artifacts**: Clearly separated from source code

## Backward Compatibility

During migration, we'll maintain backward compatibility by:

- Keeping old import paths working temporarily (using re-exports in `__init__.py`)
- Gradual migration with deprecation warnings
- Clear migration guide for any breaking changes

## Estimated Impact

- **Files to Move**: ~30 files
- **Import Statements to Update**: ~100+ imports
- **New Directories**: ~15 new directories
- **Breaking Changes**: None (if done correctly with proper imports)
