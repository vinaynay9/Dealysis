from langgraph.graph import StateGraph, START, END
from models import MemoState, DEFAULT_TEMPLATE
from document_parser import DocumentParser
from extractors import ExtractionCoordinator
from memo_generator import MemoGenerator
from financial_analyzer import FinancialAnalyzer
from typing import Dict, Any
import asyncio


def create_memo_pipeline():
    """Create LangGraph pipeline for memo generation"""

    # Initialize components
    document_parser = DocumentParser()
    extraction_coordinator = ExtractionCoordinator()
    memo_generator = MemoGenerator()
    financial_analyzer = FinancialAnalyzer()

    # Define node functions
    async def parse_documents_node(state: MemoState) -> MemoState:
        """Parse all uploaded documents"""
        print(
            f"[{state['job_id']}] Parsing {len(state['uploaded_documents'])} documents..."
        )

        try:
            chunks = await document_parser.parse_documents(state["uploaded_documents"])
            state["parsed_chunks"] = chunks
            state["processing_stage"] = "documents_parsed"
            print(f"  ✓ Generated {len(chunks)} text chunks")

        except Exception as e:
            error_msg = f"Document parsing failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")

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

                            # Add financial analysis summary to parsed chunks for LLM extraction
                            analysis_text = financial_analyzer.format_analysis_for_llm(
                                analysis
                            )
                            state["parsed_chunks"].append(
                                f"[SOURCE: {file_info['filename']} - Financial Analysis]\n{analysis_text}\n[END SOURCE]\n"
                            )
                    except Exception as e:
                        print(f"  ✗ Error analyzing {file_info['filename']}: {e}")

                # Store financial analyses in state for later use
                if "financial_analyses" not in state:
                    state["financial_analyses"] = []
                state["financial_analyses"].extend(financial_analyses)
            else:
                print("  No financial files detected")

        except Exception as e:
            error_msg = f"Financial file analysis failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")

        return state

    async def extract_information_node(state: MemoState) -> MemoState:
        """Run all extractors in parallel"""
        print(f"[{state['job_id']}] Running information extraction...")

        try:
            extracted_data = await extraction_coordinator.extract_all(
                state["parsed_chunks"]
            )

            # Merge financial analysis results into extracted data
            if "financial_analyses" in state and state["financial_analyses"]:
                # Enhance financial data with analysis results
                if "financial" in extracted_data:
                    financial_data = extracted_data["financial"]
                    if hasattr(financial_data, "dict"):
                        financial_dict = financial_data.dict()
                    else:
                        financial_dict = financial_data

                    # Add financial analysis insights
                    all_metrics = {}
                    all_red_flags = []
                    for analysis in state["financial_analyses"]:
                        if "metrics" in analysis:
                            all_metrics.update(analysis["metrics"])
                        if "red_flags" in analysis:
                            all_red_flags.extend(analysis["red_flags"])

                    # Store financial analysis data
                    financial_dict["financial_analysis"] = {
                        "metrics": all_metrics,
                        "red_flags": all_red_flags,
                        "files_analyzed": [
                            a.get("filename") for a in state["financial_analyses"]
                        ],
                    }

                    # Update the financial data object
                    from models import FinancialData

                    extracted_data["financial"] = FinancialData(**financial_dict)

                # Also enhance progress data with calculated metrics
                if "progress" in extracted_data:
                    progress_data = extracted_data["progress"]
                    if hasattr(progress_data, "dict"):
                        progress_dict = progress_data.dict()
                    else:
                        progress_dict = progress_data

                    # Extract calculated metrics from financial analyses
                    for analysis in state["financial_analyses"]:
                        if "metrics" in analysis:
                            metrics = analysis["metrics"]

                            # Map calculated metrics to progress data
                            if "calculated_arr" in metrics:
                                arr_val = metrics["calculated_arr"].get("value")
                                if arr_val and not progress_dict.get("arr"):
                                    progress_dict["arr"] = f"${arr_val:,.0f}"

                            if "calculated_runway_months" in metrics:
                                runway_val = metrics["calculated_runway_months"].get(
                                    "value"
                                )
                                if runway_val and not progress_dict.get(
                                    "runway_months"
                                ):
                                    progress_dict["runway_months"] = int(runway_val)

                            if "mom_growth_rate" in metrics:
                                mom_growth = metrics["mom_growth_rate"]
                                if mom_growth and not progress_dict.get(
                                    "growth_rate_mom"
                                ):
                                    progress_dict["growth_rate_mom"] = (
                                        f"{mom_growth:.1f}%"
                                    )

                            if "yoy_growth_rate" in metrics:
                                yoy_growth = metrics["yoy_growth_rate"]
                                if yoy_growth and not progress_dict.get(
                                    "growth_rate_yoy"
                                ):
                                    progress_dict["growth_rate_yoy"] = (
                                        f"{yoy_growth:.1f}%"
                                    )

                    from models import ProgressData

                    extracted_data["progress"] = ProgressData(**progress_dict)

            state["extracted_data"] = extracted_data
            state["processing_stage"] = "information_extracted"

        except Exception as e:
            error_msg = f"Information extraction failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")

        return state

    async def generate_memo_node(state: MemoState) -> MemoState:
        """Generate final memo sections"""
        print(f"[{state['job_id']}] Generating memo sections...")

        try:
            # Use template structure (for MVP, using default template)
            template = state.get("template_structure", DEFAULT_TEMPLATE)

            memo_result = await memo_generator.generate_complete_memo(
                state["extracted_data"], template
            )

            state["memo_sections"] = memo_result["sections"]
            state["confidence_scores"] = memo_result["confidence_scores"]
            state["flagged_items"] = memo_result["flagged_items"]
            state["final_memo"] = memo_result["final_memo"]
            state["processing_stage"] = "memo_generated"

            print(f"  ✓ Generated memo with {len(memo_result['sections'])} sections")
            print(f"  ⚠ {len(memo_result['flagged_items'])} items flagged for review")

        except Exception as e:
            error_msg = f"Memo generation failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")

        return state

    # Build the graph
    workflow = StateGraph(MemoState)

    # Add nodes
    workflow.add_node("parse_documents", parse_documents_node)
    workflow.add_node("analyze_financial_files", analyze_financial_files_node)
    workflow.add_node("extract_information", extract_information_node)
    workflow.add_node("generate_memo", generate_memo_node)

    # Define edges
    workflow.add_edge(START, "parse_documents")
    workflow.add_edge("parse_documents", "analyze_financial_files")
    workflow.add_edge("analyze_financial_files", "extract_information")
    workflow.add_edge("extract_information", "generate_memo")
    workflow.add_edge("generate_memo", END)

    # Compile and return
    return workflow.compile()


async def run_memo_pipeline(
    job_id: str, documents: list, template_structure: dict = None
) -> dict:
    """Execute the complete memo generation pipeline"""

    # Use provided template structure or fall back to default
    template = template_structure if template_structure else DEFAULT_TEMPLATE

    # Initialize state
    initial_state: MemoState = {
        "job_id": job_id,
        "uploaded_documents": documents,
        "template_structure": template,
        "parsed_chunks": [],
        "financial_analyses": [],
        "extracted_data": {},
        "memo_sections": {},
        "confidence_scores": {},
        "flagged_items": [],
        "final_memo": "",
        "processing_stage": "initialized",
        "error_messages": [],
    }

    # Create and run pipeline
    pipeline = create_memo_pipeline()

    try:
        final_state = await pipeline.ainvoke(initial_state)

        return {
            "success": len(final_state["error_messages"]) == 0,
            "memo_content": final_state["final_memo"],
            "confidence_scores": final_state["confidence_scores"],
            "flagged_items": final_state["flagged_items"],
            "error_messages": final_state["error_messages"],
            "processing_stage": final_state["processing_stage"],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "memo_content": "",
            "confidence_scores": {},
            "flagged_items": [],
            "processing_stage": "failed",
        }
