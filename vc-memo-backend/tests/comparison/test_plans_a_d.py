"""
Test script to run only Plan A and Plan D with --no-cache flag.
"""

import sys
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.document.parser import LangChainDocumentParser
from app.services.extraction.semantic_router import SemanticRouter
from app.services.extraction.strategies.plan_a import ExtractorPlanA
from app.services.extraction.strategies.plan_d import ExtractorPlanD
from tests.comparison.test_all_extraction_plans import (
    load_test_documents,
    run_extraction_plan,
    print_comprehensive_summary
)


async def main(use_cache: bool = True):
    """Run Plan A and Plan D only"""
    cache_status = "ENABLED" if use_cache else "DISABLED"
    print("="*70)
    print("TESTING PLAN A AND PLAN D")
    print("="*70)
    print(f"\nCache: {cache_status}")
    print("\nTesting on Nexus AI mock data")
    
    results = {}
    
    # Load documents once
    documents = load_test_documents("Nexus AI")
    print(f"\nLoaded {len(documents)} documents for Nexus AI")
    
    # Parse and chunk once
    parser = LangChainDocumentParser()
    chunks = await parser.parse_documents(documents)
    print(f"Generated {len(chunks)} chunks")
    
    # Route chunks once
    router = SemanticRouter()
    routed_chunks = await router.route_chunks(chunks)
    
    # Plan A
    print("\n" + "="*70)
    print("PLAN A (Structured Outputs)")
    print("="*70)
    try:
        extractor_a = ExtractorPlanA(use_cache=use_cache)
        extraction_types = ["progress", "financial", "market", "company", "team"]
        results["Plan A"] = await run_extraction_plan("Plan A", extractor_a, routed_chunks, extraction_types)
    except Exception as e:
        print(f"Plan A failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Plan D
    print("\n" + "="*70)
    print("PLAN D (Cost-Optimized with Retry)")
    print("="*70)
    try:
        extractor_d = ExtractorPlanD(use_cache=use_cache)
        results["Plan D"] = await run_extraction_plan("Plan D", extractor_d, routed_chunks, extraction_types)
    except Exception as e:
        print(f"Plan D failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    if results:
        print_comprehensive_summary(results)
    else:
        print("\n⚠️  No results to display")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Plan A and Plan D only")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable cache for all extractions (fresh test run)"
    )
    args = parser.parse_args()
    
    use_cache = not args.no_cache
    asyncio.run(main(use_cache=use_cache))

