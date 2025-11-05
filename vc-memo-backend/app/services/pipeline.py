from langgraph.graph import StateGraph, START, END
from app.core.models import MemoState, DEFAULT_TEMPLATE, ExtractedData
from app.services.document_parser import LangChainDocumentParser
from app.services.extractors import ExtractionCoordinator
from app.services.memo_generator import MemoGenerator
from app.services.financial_analyzer import FinancialAnalyzer
from app.services.semantic_router import SemanticRouter
from app.utils.summary_cache import SummaryCache
from typing import Dict, Any
import asyncio
import time


def create_memo_pipeline():
    """Create optimized LangGraph pipeline with LangChain document loaders"""

    # Initialize components
    document_parser = LangChainDocumentParser()
    semantic_router = SemanticRouter()
    extraction_coordinator = ExtractionCoordinator()
    memo_generator = MemoGenerator()
    financial_analyzer = FinancialAnalyzer()
    cache = SummaryCache()

    # Define node functions
    async def parse_and_chunk_documents_node(state: MemoState) -> MemoState:
        """Parse documents using LangChain loaders and split into chunks"""
        start_time = time.time()
        print(
            f"[{state['job_id']}] Parsing and chunking {len(state['uploaded_documents'])} documents..."
        )

        try:
            # Use LangChain parser to get Document objects with metadata
            documents = await document_parser.parse_documents(
                state["uploaded_documents"]
            )
            state["parsed_chunks"] = (
                documents  # Now these are LangChain Document objects
            )
            state["processing_stage"] = "documents_chunked"

            elapsed = time.time() - start_time
            print(f"  ✓ Generated {len(documents)} chunks in {elapsed:.1f}s")

            # Store chunk statistics for monitoring
            if not hasattr(state, "statistics"):
                state["statistics"] = {}
            state["statistics"]["chunk_count"] = len(documents)
            state["statistics"]["parsing_time"] = elapsed

        except Exception as e:
            error_msg = f"Document parsing failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")
            import traceback

            traceback.print_exc()

        return state

    async def route_chunks_node(state: MemoState) -> MemoState:
        """Route chunks to relevant extractors using semantic similarity"""
        start_time = time.time()
        print(f"\n[{state['job_id']}] 🧭 Semantic Routing Stage")
        print("=" * 60)

        try:
            # Route chunks to extractors
            routed = await semantic_router.route_chunks(state["parsed_chunks"])

            state["routed_chunks"] = routed
            state["processing_stage"] = "chunks_routed"

            # Log routing results
            elapsed = time.time() - start_time
            total_routed = sum(len(chunks) for chunks in routed.values())
            original_chunks = len(state["parsed_chunks"])

            # Calculate routing efficiency
            baseline_assignments = original_chunks * 5  # 5 extractors
            reduction_pct = (
                ((baseline_assignments - total_routed) / baseline_assignments * 100)
                if baseline_assignments > 0
                else 0
            )

            print(f"\n✅ Routing Complete:")
            print(f"   Original chunks:      {original_chunks}")
            print(f"   Total assignments:    {total_routed}")
            print(f"   Baseline (no routing): {baseline_assignments} assignments")
            print(f"   Efficiency gain:      {reduction_pct:.1f}% reduction")
            print(f"   Time:                 {elapsed:.2f}s")

            # Store routing statistics
            if "statistics" not in state:
                state["statistics"] = {}
            state["statistics"]["routing_time"] = elapsed
            state["statistics"]["routing_efficiency"] = reduction_pct
            state["statistics"]["total_assignments"] = total_routed
            state["statistics"]["baseline_assignments"] = baseline_assignments

            # Get routing cost from semantic router
            routing_stats = semantic_router.get_routing_stats()
            state["statistics"]["routing_tokens"] = routing_stats["total_tokens"]
            state["statistics"]["routing_cost"] = routing_stats["total_cost"]

        except Exception as e:
            error_msg = f"Semantic routing failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")
            import traceback

            traceback.print_exc()

            # Fallback: route all chunks to all extractors
            print("  ⚠ Falling back to routing all chunks to all extractors")
            all_chunks = state["parsed_chunks"]
            state["routed_chunks"] = {
                "progress": all_chunks,
                "financial": all_chunks,
                "market": all_chunks,
                "company": all_chunks,
                "team": all_chunks,
            }

        print("=" * 60)
        return state

    async def analyze_financial_files_node(state: MemoState) -> MemoState:
        """Analyze Excel/CSV financial files separately"""
        print(f"[{state['job_id']}] Analyzing financial files...")

        try:
            financial_files = []
            for doc in state["uploaded_documents"]:
                filename = doc["filename"]
                file_type = filename.split(".")[-1].lower()
                if file_type in ["xlsx", "xls", "csv"]:
                    financial_files.append(
                        {
                            "filename": filename,
                            "content": doc["content"],
                            "file_type": file_type,
                        }
                    )

            if financial_files:
                print(f"  Found {len(financial_files)} financial file(s)")

                # Analyze each financial file
                financial_analyses = []
                for file_info in financial_files:
                    try:
                        analysis = await financial_analyzer.analyze_financial_file(
                            file_info["content"],
                            file_info["filename"],
                            file_info["file_type"],
                        )
                        if "error" not in analysis:
                            financial_analyses.append(analysis)
                            print(f"  ✓ Analyzed {file_info['filename']}")
                    except Exception as e:
                        print(f"  ✗ Error analyzing {file_info['filename']}: {e}")

                # Store analyses for later use
                state["financial_analyses"] = financial_analyses
            else:
                print("  No financial files detected")
                state["financial_analyses"] = []

        except Exception as e:
            error_msg = f"Financial file analysis failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")

        return state

    async def extract_information_node(state: MemoState) -> MemoState:
        """Run direct extraction with caching on routed chunks"""
        start_time = time.time()
        print(f"\n[{state['job_id']}] 🔍 Extraction Stage")
        print("=" * 60)

        try:
            # Run extraction on routed chunks
            extracted_data = await extraction_coordinator.extract_all(
                state["routed_chunks"]
            )

            # Merge financial analysis results
            if state.get("financial_analyses"):
                _merge_financial_analyses(extracted_data, state["financial_analyses"])

            state["extracted_data"] = extracted_data
            state["processing_stage"] = "information_extracted"

            elapsed = time.time() - start_time

            # Collect extraction statistics from extracted data
            total_extraction_cost = 0.0
            total_extraction_tokens = 0
            total_extraction_calls = 0

            for extract_type, data in extracted_data.items():
                if hasattr(data, "_extraction_stats"):
                    stats = data._extraction_stats
                    total_extraction_cost += stats.get("cost", 0)
                    total_extraction_tokens += stats.get("total_tokens", 0)
                    total_extraction_calls += stats.get("chunks_processed", 0)

            print(f"\n✅ Extraction Stage Complete:")
            print(f"   Total time:       {elapsed:.2f}s")
            print(f"   Total API calls:  {total_extraction_calls}")
            print(f"   Total tokens:     {total_extraction_tokens:,}")
            print(f"   Total cost:       ~${total_extraction_cost:.4f}")

            # Store statistics
            if "statistics" not in state:
                state["statistics"] = {}
            state["statistics"].update(
                {
                    "extraction_time": elapsed,
                    "extraction_api_calls": total_extraction_calls,
                    "extraction_tokens": total_extraction_tokens,
                    "extraction_cost": total_extraction_cost,
                }
            )

        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")
            import traceback

            traceback.print_exc()

        print("=" * 60)
        return state

    async def generate_memo_node(state: MemoState) -> MemoState:
        """Generate final memo sections"""
        start_time = time.time()
        print(f"[{state['job_id']}] Generating memo sections...")

        try:
            # Use template structure
            template = state.get("template_structure", DEFAULT_TEMPLATE)

            memo_result = await memo_generator.generate_complete_memo(
                state["extracted_data"], template
            )

            state["memo_sections"] = memo_result["sections"]
            state["confidence_scores"] = memo_result["confidence_scores"]
            state["flagged_items"] = memo_result["flagged_items"]
            state["final_memo"] = memo_result["final_memo"]
            state["processing_stage"] = "memo_generated"

            elapsed = time.time() - start_time
            print(
                f"  ✓ Generated memo with {len(memo_result['sections'])} sections in {elapsed:.1f}s"
            )
            print(f"  ⚠ {len(memo_result['flagged_items'])} items flagged for review")

            # Final comprehensive statistics
            if "statistics" in state:
                stats = state["statistics"]
                stats["memo_generation_time"] = elapsed

                # Calculate total time and costs
                total_time = sum(
                    [
                        stats.get("parsing_time", 0),
                        stats.get("routing_time", 0),
                        stats.get("extraction_time", 0),
                        stats.get("memo_generation_time", 0),
                    ]
                )
                stats["total_time"] = total_time

                # Calculate total costs
                routing_cost = stats.get("routing_cost", 0)
                extraction_cost = stats.get("extraction_cost", 0)
                # Estimate memo generation cost (8 calls to gpt-4o, ~26K tokens)
                memo_gen_cost = 0.18  # Approximate based on typical usage
                total_cost = routing_cost + extraction_cost + memo_gen_cost

                # Calculate API call totals
                routing_api_calls = (
                    len(state.get("parsed_chunks", [])) + 5
                )  # Chunk embeddings + intent embeddings
                extraction_api_calls = stats.get("extraction_api_calls", 0)
                memo_api_calls = 8  # 8 sections
                total_api_calls = (
                    routing_api_calls + extraction_api_calls + memo_api_calls
                )

                # Calculate baseline (old approach)
                chunk_count = stats.get("chunk_count", 0)
                baseline_extraction_calls = chunk_count * 5  # 5 extractors
                baseline_api_calls = baseline_extraction_calls + memo_api_calls

                # Calculate token totals
                total_tokens = (
                    stats.get("routing_tokens", 0)
                    + stats.get("extraction_tokens", 0)
                    + 26400  # Approximate memo generation tokens
                )

                # Print comprehensive final summary
                print(f"\n\n{'=' * 60}")
                print(f"📊 PIPELINE COMPLETE - Job {state['job_id']}")
                print(f"{'=' * 60}")

                print(f"\n⏱️  TIMING BREAKDOWN:")
                print(f"   Parsing:          {stats.get('parsing_time', 0):.2f}s")
                print(
                    f"   Routing:          {stats.get('routing_time', 0):.2f}s ({routing_api_calls} API calls)"
                )
                print(f"   Financial:        0.0s (pandas-based, no API calls)")
                print(
                    f"   Extraction:       {stats.get('extraction_time', 0):.2f}s ({extraction_api_calls} API calls)"
                )
                print(
                    f"   Generation:       {elapsed:.2f}s ({memo_api_calls} API calls)"
                )
                print(f"   ─────────────────────────────────────")
                print(f"   TOTAL:            {total_time:.2f}s")

                print(f"\n💰 COST BREAKDOWN:")
                print(
                    f"   Embeddings:       ${routing_cost:.4f} ({stats.get('routing_tokens', 0):,} tokens)"
                )
                print(
                    f"   Extraction:       ${extraction_cost:.4f} ({stats.get('extraction_tokens', 0):,} tokens)"
                )
                print(f"   Generation:       ${memo_gen_cost:.4f} (~26,400 tokens)")
                print(f"   ─────────────────────────────────────")
                print(f"   TOTAL:            ${total_cost:.4f}")

                print(f"\n📈 EFFICIENCY METRICS:")
                print(f"   Total API calls:      {total_api_calls}")
                print(f"   Baseline (old way):   {baseline_api_calls}")
                if baseline_api_calls > 0:
                    api_reduction = (
                        (baseline_api_calls - total_api_calls)
                        / baseline_api_calls
                        * 100
                    )
                    print(f"   API call reduction:   {api_reduction:.1f}%")

                print(f"\n   Total tokens:         {total_tokens:,}")
                print(
                    f"   Routing efficiency:   {stats.get('routing_efficiency', 0):.1f}% reduction in assignments"
                )

                print(f"\n   Chunks processed:     {chunk_count}")
                print(f"   Chunk assignments:    {stats.get('total_assignments', 0)}")
                print(
                    f"   Baseline assignments: {stats.get('baseline_assignments', 0)}"
                )

                print(f"\n💾 MEMO DETAILS:")
                print(
                    f"   Sections generated:   {len(memo_result.get('sections', {}))}"
                )
                print(
                    f"   Flagged items:        {len(memo_result.get('flagged_items', []))}"
                )

                print(f"\n{'=' * 60}")
                print(f"✅ SUCCESS - Memo generated successfully!")
                print(f"{'=' * 60}\n")

        except Exception as e:
            error_msg = f"Memo generation failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")

        return state

    # Build the graph
    workflow = StateGraph(MemoState)

    # Add nodes
    workflow.add_node("parse_and_chunk_documents", parse_and_chunk_documents_node)
    workflow.add_node("route_chunks", route_chunks_node)
    workflow.add_node("analyze_financial_files", analyze_financial_files_node)
    workflow.add_node("extract_information", extract_information_node)
    workflow.add_node("generate_memo", generate_memo_node)

    # Define edges
    workflow.add_edge(START, "parse_and_chunk_documents")
    workflow.add_edge("parse_and_chunk_documents", "route_chunks")
    workflow.add_edge("route_chunks", "analyze_financial_files")
    workflow.add_edge("analyze_financial_files", "extract_information")
    workflow.add_edge("extract_information", "generate_memo")
    workflow.add_edge("generate_memo", END)

    # Compile and return
    return workflow.compile()


def _merge_financial_analyses(extracted_data: Dict[str, Any], financial_analyses: list):
    """Merge financial analysis results into extracted data"""
    if "financial" in extracted_data and financial_analyses:
        financial_data = extracted_data["financial"]
        if hasattr(financial_data, "__dict__"):
            financial_dict = financial_data.__dict__
        else:
            financial_dict = {}

        # Aggregate metrics and red flags
        all_metrics = {}
        all_red_flags = []

        for analysis in financial_analyses:
            if "metrics" in analysis:
                all_metrics.update(analysis["metrics"])
            if "red_flags" in analysis:
                all_red_flags.extend(analysis["red_flags"])

        # Store analysis data
        financial_dict["financial_analysis"] = {
            "metrics": all_metrics,
            "red_flags": all_red_flags,
            "files_analyzed": [a.get("filename") for a in financial_analyses],
        }

    # Also enhance progress data with calculated metrics
    if "progress" in extracted_data and financial_analyses:
        progress_data = extracted_data["progress"]
        if hasattr(progress_data, "__dict__"):
            progress_dict = progress_data.__dict__
        else:
            progress_dict = {}

        for analysis in financial_analyses:
            if "metrics" in analysis:
                metrics = analysis["metrics"]

                # Map calculated metrics
                if "calculated_arr" in metrics and not progress_dict.get("arr"):
                    arr_val = metrics["calculated_arr"].get("value")
                    if arr_val:
                        progress_dict["arr"] = f"${arr_val:,.0f}"

                if "calculated_runway_months" in metrics and not progress_dict.get(
                    "runway_months"
                ):
                    runway_val = metrics["calculated_runway_months"].get("value")
                    if runway_val:
                        progress_dict["runway_months"] = int(runway_val)

                if "mom_growth_rate" in metrics and not progress_dict.get(
                    "growth_rate_mom"
                ):
                    progress_dict["growth_rate_mom"] = (
                        f"{metrics['mom_growth_rate']:.1f}%"
                    )

                if "yoy_growth_rate" in metrics and not progress_dict.get(
                    "growth_rate_yoy"
                ):
                    progress_dict["growth_rate_yoy"] = (
                        f"{metrics['yoy_growth_rate']:.1f}%"
                    )


async def run_memo_pipeline(
    job_id: str, documents: list, template_structure: dict = None
) -> dict:
    """Execute the optimized memo generation pipeline"""

    print(f"\n🚀 Starting pipeline for job {job_id}")
    print(f"📄 Processing {len(documents)} documents")

    # Use provided template or default
    template = template_structure if template_structure else DEFAULT_TEMPLATE

    # Initialize state
    initial_state: MemoState = {
        "job_id": job_id,
        "uploaded_documents": documents,
        "template_structure": template,
        "parsed_chunks": [],
        "routed_chunks": {},
        "financial_analyses": [],
        "extracted_data": {},
        "memo_sections": {},
        "confidence_scores": {},
        "flagged_items": [],
        "final_memo": "",
        "processing_stage": "initialized",
        "error_messages": [],
        "statistics": {},  # Track performance metrics
    }

    # Create and run pipeline
    pipeline = create_memo_pipeline()

    try:
        final_state = await pipeline.ainvoke(initial_state)

        # Prepare response with statistics
        response = {
            "success": len(final_state["error_messages"]) == 0,
            "memo_content": final_state["final_memo"],
            "confidence_scores": final_state["confidence_scores"],
            "flagged_items": final_state["flagged_items"],
            "error_messages": final_state["error_messages"],
            "processing_stage": final_state["processing_stage"],
        }

        # Include performance statistics if available
        if hasattr(final_state, "statistics"):
            response["performance"] = {
                "total_time_seconds": final_state["statistics"].get("total_time", 0),
                "chunks_processed": final_state["statistics"].get("chunk_count", 0),
                "cache_hits": final_state["statistics"].get("cache_hits", 0),
            }

        return response

    except Exception as e:
        import traceback

        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "memo_content": "",
            "confidence_scores": {},
            "flagged_items": [],
            "processing_stage": "failed",
        }
