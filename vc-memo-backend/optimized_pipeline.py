from langgraph.graph import StateGraph, START, END
from models import MemoState, DEFAULT_TEMPLATE, ExtractedData
from optimized_document_parser import OptimizedDocumentParser
from optimized_extractors import OptimizedExtractionCoordinator
from memo_generator import MemoGenerator
from financial_analyzer import FinancialAnalyzer
from summary_cache import SummaryCache
from typing import Dict, Any
import asyncio
import time


def create_optimized_memo_pipeline():
    """Create optimized LangGraph pipeline with direct extraction (no summarization)"""
    
    # Initialize components
    document_parser = OptimizedDocumentParser()
    extraction_coordinator = OptimizedExtractionCoordinator()
    memo_generator = MemoGenerator()
    financial_analyzer = FinancialAnalyzer()
    cache = SummaryCache()
    
    # Define node functions
    async def parse_and_chunk_documents_node(state: MemoState) -> MemoState:
        """Parse documents and create smart chunks"""
        start_time = time.time()
        print(f"[{state['job_id']}] Parsing and chunking {len(state['uploaded_documents'])} documents...")
        
        try:
            # Use optimized parser to get smart chunks
            chunks = await document_parser.parse_documents(state["uploaded_documents"])
            state["parsed_chunks"] = chunks  # Now these are DocumentChunk objects
            state["processing_stage"] = "documents_chunked"
            
            elapsed = time.time() - start_time
            print(f"  ✓ Generated {len(chunks)} optimized chunks in {elapsed:.1f}s")
            
            # Store chunk statistics for monitoring
            if not hasattr(state, 'statistics'):
                state['statistics'] = {}
            state['statistics']['chunk_count'] = len(chunks)
            state['statistics']['parsing_time'] = elapsed
            
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
                    financial_files.append({
                        "filename": filename,
                        "content": doc["content"],
                        "file_type": file_type,
                    })
            
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
        """Run direct extraction with caching (no summarization layers)"""
        start_time = time.time()
        print(f"[{state['job_id']}] Running optimized extraction...")
        
        try:
            # Run direct extraction from chunks (no summarization)
            extracted_data = await extraction_coordinator.extract_all(
                state["parsed_chunks"]
            )
            
            # Merge financial analysis results
            if state.get("financial_analyses"):
                _merge_financial_analyses(extracted_data, state["financial_analyses"])
            
            state["extracted_data"] = extracted_data
            state["processing_stage"] = "information_extracted"
            
            elapsed = time.time() - start_time
            
            # Get cache statistics
            cache_stats = await cache.get_cache_stats()
            cache_hits = cache_stats.get('recent_cache_hits', 0)
            
            print(f"  ✓ Extraction completed in {elapsed:.1f}s")
            print(f"  📊 Cache hits: {cache_hits}")
            
            # Store statistics
            if not hasattr(state, 'statistics'):
                state['statistics'] = {}
            state['statistics'].update({
                'extraction_time': elapsed,
                'cache_hits': cache_hits,
            })
            
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")
            import traceback
            traceback.print_exc()
            
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
            print(f"  ✓ Generated memo with {len(memo_result['sections'])} sections in {elapsed:.1f}s")
            print(f"  ⚠ {len(memo_result['flagged_items'])} items flagged for review")
            
            # Final statistics
            if hasattr(state, 'statistics'):
                state['statistics']['memo_generation_time'] = elapsed
                state['statistics']['total_time'] = sum([
                    state['statistics'].get('parsing_time', 0),
                    state['statistics'].get('extraction_time', 0),
                    state['statistics'].get('memo_generation_time', 0)
                ])
                
                print(f"\n📊 Pipeline Statistics:")
                print(f"  Total processing time: {state['statistics']['total_time']:.1f}s")
                print(f"  Chunks processed: {state['statistics'].get('chunk_count', 0)}")
                print(f"  Cache efficiency: {state['statistics'].get('cache_hits', 0)} hits")
            
        except Exception as e:
            error_msg = f"Memo generation failed: {str(e)}"
            state["error_messages"].append(error_msg)
            print(f"  ✗ {error_msg}")
            
        return state
    
    # Build the graph
    workflow = StateGraph(MemoState)
    
    # Add nodes
    workflow.add_node("parse_and_chunk_documents", parse_and_chunk_documents_node)
    workflow.add_node("analyze_financial_files", analyze_financial_files_node)
    workflow.add_node("extract_information", extract_information_node)
    workflow.add_node("generate_memo", generate_memo_node)
    
    # Define edges
    workflow.add_edge(START, "parse_and_chunk_documents")
    workflow.add_edge("parse_and_chunk_documents", "analyze_financial_files")
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
            "files_analyzed": [a.get("filename") for a in financial_analyses]
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
                
                if "calculated_runway_months" in metrics and not progress_dict.get("runway_months"):
                    runway_val = metrics["calculated_runway_months"].get("value")
                    if runway_val:
                        progress_dict["runway_months"] = int(runway_val)
                
                if "mom_growth_rate" in metrics and not progress_dict.get("growth_rate_mom"):
                    progress_dict["growth_rate_mom"] = f"{metrics['mom_growth_rate']:.1f}%"
                
                if "yoy_growth_rate" in metrics and not progress_dict.get("growth_rate_yoy"):
                    progress_dict["growth_rate_yoy"] = f"{metrics['yoy_growth_rate']:.1f}%"


async def run_optimized_memo_pipeline(
    job_id: str, documents: list, template_structure: dict = None
) -> dict:
    """Execute the optimized memo generation pipeline"""
    
    print(f"\n🚀 Starting OPTIMIZED pipeline for job {job_id}")
    print(f"📄 Processing {len(documents)} documents")
    
    # Use provided template or default
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
        "statistics": {}  # Track performance metrics
    }
    
    # Create and run pipeline
    pipeline = create_optimized_memo_pipeline()
    
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
        if hasattr(final_state, 'statistics'):
            response["performance"] = {
                "total_time_seconds": final_state['statistics'].get('total_time', 0),
                "chunks_processed": final_state['statistics'].get('chunk_count', 0),
                "cache_hits": final_state['statistics'].get('cache_hits', 0)
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
