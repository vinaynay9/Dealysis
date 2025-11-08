# Testing Guide

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_extractors.py -v
```

## Test Files

- `test_local_llm.py` - Ollama integration & fallback
- `test_extractors.py` - Hallucination prevention, Ollama usage
- `test_fact_checking.py` - Consistency detection
- `test_confidence_scoring.py` - Enhanced confidence with consistency checks
- `test_context_enrichment.py` - Cross-chunk linking
- `test_pipeline_integration.py` - Full pipeline with all features
- `test_api_enhanced.py` - API response structure
- `test_api.py` - End-to-end API test (requires server running)

## Manual End-to-End Test

```bash
# Terminal 1: Start server
uvicorn app.main:app --reload

# Terminal 2: Run test
python -m tests.test_api
```

## What's Tested

- ✅ Hallucination prevention (nulls for missing data)
- ✅ Ollama integration & fallback
- ✅ Fact-checking & consistency
- ✅ Confidence scoring with cross-chunk checks
- ✅ Context enrichment
- ✅ Source citations
- ✅ Uncertainty flags
