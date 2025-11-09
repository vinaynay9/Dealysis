"""
Test script to compare all extraction plans.
Can be run from command line: python -m tests.test_all_extraction_plans
"""

import sys
import os
import asyncio
import json
import time
import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import config first to ensure .env is loaded (load_dotenv() is called at module level)
import app.core.config  # This will trigger load_dotenv()

from app.services.document.parser import LangChainDocumentParser
from app.services.extraction.semantic_router import SemanticRouter
from app.services.extraction import ExtractionCoordinator, OptimizedExtractor
from app.services.extraction.strategies.plan_a import ExtractorPlanA
from app.services.extraction.strategies.plan_b import ExtractorPlanB
from app.services.extraction.strategies.plan_c import ExtractorPlanC
from app.services.extraction.strategies.plan_d import ExtractorPlanD


def load_test_documents(company_name: str) -> List[Dict[str, Any]]:
    """Load test documents for a company"""
    # Convert company name to directory format (e.g., "Nexus AI" -> "nexus-ai")
    dir_name = company_name.lower().replace(" ", "-")
    
    # Try multiple path resolution strategies
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent
    base_path = project_root / "mock-data" / dir_name
    
    if not base_path.exists():
        # Try from current working directory
        cwd_path = Path.cwd() / "mock-data" / dir_name
        if cwd_path.exists():
            base_path = cwd_path
        else:
            # Try relative to script location
            alt_path = script_dir / ".." / ".." / "mock-data" / dir_name
            alt_path = alt_path.resolve()
            if alt_path.exists():
                base_path = alt_path
            else:
                print(f"⚠️  Warning: Could not find documents directory for {company_name}")
                print(f"   Tried: {base_path}")
                print(f"   Tried: {cwd_path}")
                print(f"   Tried: {alt_path}")
                return []
    
    print(f"📁 Loading documents from: {base_path}")
    documents = []
    docx_files = list(base_path.glob("*.docx"))
    xlsx_files = list(base_path.glob("*.xlsx"))
    print(f"   Found {len(docx_files)} .docx files and {len(xlsx_files)} .xlsx files")
    
    for file_path in docx_files:
        with open(file_path, "rb") as f:
            content = f.read()
            documents.append({
                "filename": file_path.name,
                "content": content,
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            })
    
    for file_path in xlsx_files:
        with open(file_path, "rb") as f:
            content = f.read()
            documents.append({
                "filename": file_path.name,
                "content": content,
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            })
    
    return documents


async def run_extraction_plan(
    plan_name: str,
    extractor,
    routed_chunks: Dict[str, List],
    extraction_types: List[str]
) -> Dict[str, Any]:
    """Run extraction using a specific plan"""
    print(f"\n{'='*70}")
    print(f"Testing {plan_name}")
    print(f"{'='*70}")
    
    start_time = time.time()
    results = {}
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_cache_hits = 0
    validation_errors = []
    
    # Track breakdown by extraction type
    token_breakdown_by_type = {}
    model_usage_breakdown = {}  # model -> {"cost": 0.0, "input_tokens": 0, "output_tokens": 0, "calls": 0}
    
    for extract_type in extraction_types:
        chunks = routed_chunks.get(extract_type, [])
        if not chunks:
            continue
        
        try:
            extracted_data = await extractor.extract(chunks, extract_type)
            results[extract_type] = extracted_data
            
            # Track comprehensive stats
            if hasattr(extracted_data, "_extraction_stats"):
                stats = extracted_data._extraction_stats
                cost = stats.get("cost", 0.0)
                input_tokens = stats.get("input_tokens", 0)
                output_tokens = stats.get("output_tokens", 0)
                tokens = stats.get("total_tokens", input_tokens + output_tokens)
                cache_hits = stats.get("cache_hits", 0)
                model = stats.get("model", "unknown")
                
                # Aggregate totals
                total_cost += cost
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                total_tokens += tokens
                total_cache_hits += cache_hits
                
                # Track by extraction type
                token_breakdown_by_type[extract_type] = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": tokens,
                    "cost": cost,
                    "model": model,
                    "cache_hits": cache_hits,
                }
                
                # Track model usage
                if model not in model_usage_breakdown:
                    model_usage_breakdown[model] = {
                        "cost": 0.0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "calls": 0,
                    }
                model_usage_breakdown[model]["cost"] += cost
                model_usage_breakdown[model]["input_tokens"] += input_tokens
                model_usage_breakdown[model]["output_tokens"] += output_tokens
                model_usage_breakdown[model]["calls"] += 1
            
            # Check for validation errors
            if hasattr(extracted_data, "uncertainty_flags"):
                for flag in extracted_data.uncertainty_flags:
                    if "validation" in flag.lower() or "error" in flag.lower():
                        validation_errors.append(f"{extract_type}: {flag}")
        
        except Exception as e:
            print(f"  ✗ {extract_type} extraction failed: {e}")
            import traceback
            traceback.print_exc()
            validation_errors.append(f"{extract_type}: {str(e)}")
    
    elapsed = time.time() - start_time
    
    # Extract confidence scores
    confidence_scores = {}
    for extract_type, data in results.items():
        if hasattr(data, "confidence"):
            confidence_scores[extract_type] = data.confidence
    
    return {
        "plan_name": plan_name,
        "results": results,
        "confidence_scores": confidence_scores,
        "validation_errors": validation_errors,
        "total_cost": total_cost,
        "processing_time": elapsed,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "token_breakdown": token_breakdown_by_type,
        "model_usage": model_usage_breakdown,
        "cache_hits": total_cache_hits,
    }


async def run_full_pipeline_test(
    company_name: str,
    plan_name: str,
    extractor_class,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Run full pipeline test with a specific extractor plan"""
    
    # Load documents
    documents = load_test_documents(company_name)
    print(f"\nLoaded {len(documents)} documents for {company_name}")
    
    # Parse and chunk
    parser = LangChainDocumentParser()
    chunks = await parser.parse_documents(documents)
    print(f"Generated {len(chunks)} chunks")
    
    # Route chunks
    router = SemanticRouter()
    routed_chunks = await router.route_chunks(chunks)
    
    # Create extractor with use_cache parameter
    extractor = extractor_class(use_cache=use_cache)
    
    # Run extractions
    extraction_types = ["progress", "financial", "market", "company", "team"]
    result = await run_extraction_plan(plan_name, extractor, routed_chunks, extraction_types)
    
    return result


def serialize_extraction_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Convert extraction results to JSON-serializable format"""
    serialized = {}
    for plan_name, result in results.items():
        serialized[plan_name] = {
            "plan_name": result.get("plan_name", plan_name),
            "confidence_scores": result.get("confidence_scores", {}),
            "validation_errors": result.get("validation_errors", []),
            "total_cost": result.get("total_cost", 0.0),
            "processing_time": result.get("processing_time", 0.0),
            "total_input_tokens": result.get("total_input_tokens", 0),
            "total_output_tokens": result.get("total_output_tokens", 0),
            "total_tokens": result.get("total_tokens", 0),
            "token_breakdown": result.get("token_breakdown", {}),
            "model_usage": result.get("model_usage", {}),
            "cache_hits": result.get("cache_hits", 0),
            # Serialize extracted data (convert Pydantic models to dicts)
            "extracted_data": {}
        }
        
        # Serialize extracted data
        for extract_type, data in result.get("results", {}).items():
            if hasattr(data, "model_dump"):
                serialized[plan_name]["extracted_data"][extract_type] = data.model_dump()
            elif hasattr(data, "dict"):
                serialized[plan_name]["extracted_data"][extract_type] = data.dict()
            else:
                serialized[plan_name]["extracted_data"][extract_type] = str(data)
    
    return serialized


def generate_comparison_outputs(
    results: Dict[str, Any],
    best_plan: tuple,
    output_dir: Path,
    summary_text: str
):
    """Generate all detailed comparison output files"""
    
    # 1. Save complete JSON results
    json_file = output_dir / "results.json"
    serialized_results = serialize_extraction_results(results)
    json_file.write_text(json.dumps(serialized_results, indent=2, default=str), encoding="utf-8")
    
    # 2. Save per-plan JSON files
    for plan_name, result in results.items():
        plan_file = output_dir / f"plan_{plan_name.lower().replace(' ', '_')}_results.json"
        plan_data = {
            "plan_name": plan_name,
            "confidence_scores": result.get("confidence_scores", {}),
            "validation_errors": result.get("validation_errors", []),
            "total_cost": result.get("total_cost", 0.0),
            "processing_time": result.get("processing_time", 0.0),
            "total_input_tokens": result.get("total_input_tokens", 0),
            "total_output_tokens": result.get("total_output_tokens", 0),
            "total_tokens": result.get("total_tokens", 0),
            "token_breakdown": result.get("token_breakdown", {}),
            "model_usage": result.get("model_usage", {}),
            "cache_hits": result.get("cache_hits", 0),
            "extracted_data": {}
        }
        
        # Serialize extracted data for this plan
        for extract_type, data in result.get("results", {}).items():
            if hasattr(data, "model_dump"):
                plan_data["extracted_data"][extract_type] = data.model_dump()
            elif hasattr(data, "dict"):
                plan_data["extracted_data"][extract_type] = data.dict()
            else:
                plan_data["extracted_data"][extract_type] = str(data)
        
        plan_file.write_text(json.dumps(plan_data, indent=2, default=str), encoding="utf-8")
    
    # 3. Generate CSV comparison file
    csv_file = output_dir / "comparison.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Plan", "Cost ($)", "Input Tokens", "Output Tokens", "Total Tokens",
            "Time (s)", "Avg Confidence", "Validation Errors", "Cache Hits"
        ])
        
        for plan_name, result in results.items():
            confidence_scores = result.get("confidence_scores", {})
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
            
            writer.writerow([
                plan_name,
                f"{result.get('total_cost', 0.0):.4f}",
                result.get("total_input_tokens", 0),
                result.get("total_output_tokens", 0),
                result.get("total_tokens", 0),
                f"{result.get('processing_time', 0.0):.2f}",
                f"{avg_confidence:.2f}",
                len(result.get("validation_errors", [])),
                result.get("cache_hits", 0)
            ])
    
    # 4. Generate detailed markdown comparison report
    md_file = output_dir / "detailed_comparison.md"
    md_content = generate_detailed_markdown_report(results, best_plan, summary_text)
    md_file.write_text(md_content, encoding="utf-8")
    
    # 5. Generate best strategy recommendation
    strategy_file = output_dir / "best_strategy.md"
    strategy_content = generate_best_strategy_recommendation(results, best_plan)
    strategy_file.write_text(strategy_content, encoding="utf-8")


def generate_detailed_markdown_report(
    results: Dict[str, Any],
    best_plan: tuple,
    summary_text: str
) -> str:
    """Generate comprehensive markdown comparison report"""
    lines = []
    
    lines.append("# Extraction Plan Comparison Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    if best_plan:
        plan_name, result, avg_conf, errors, cost = best_plan
        lines.append(f"**Recommended Plan:** {plan_name}")
        lines.append("")
        lines.append(f"- **Average Confidence:** {avg_conf:.2f}")
        lines.append(f"- **Validation Errors:** {errors}")
        lines.append(f"- **Cost:** ${cost:.4f}")
        lines.append(f"- **Processing Time:** {result['processing_time']:.2f}s")
        lines.append("")
        if avg_conf >= 0.8:
            lines.append("✅ **This plan meets the 0.8 confidence target**")
        else:
            lines.append("⚠️ **Confidence below 0.8 target. Consider improvements.**")
    else:
        lines.append("No plans completed successfully.")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Side-by-Side Comparison Table
    lines.append("## Side-by-Side Comparison")
    lines.append("")
    lines.append("| Plan | Cost ($) | Input Tokens | Output Tokens | Time (s) | Avg Confidence | Errors |")
    lines.append("|------|----------|--------------|---------------|----------|----------------|--------|")
    
    for plan_name, result in results.items():
        confidence_scores = result.get("confidence_scores", {})
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
        
        lines.append(
            f"| {plan_name} | ${result.get('total_cost', 0.0):.4f} | "
            f"{result.get('total_input_tokens', 0):,} | {result.get('total_output_tokens', 0):,} | "
            f"{result.get('processing_time', 0.0):.2f} | {avg_confidence:.2f} | "
            f"{len(result.get('validation_errors', []))} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Per-Plan Detailed Breakdowns
    lines.append("## Per-Plan Detailed Breakdowns")
    lines.append("")
    
    for plan_name, result in results.items():
        lines.append(f"### {plan_name}")
        lines.append("")
        
        # Cost Summary
        lines.append("#### Cost Summary")
        lines.append(f"- **Total Cost:** ${result.get('total_cost', 0.0):.4f}")
        model_usage = result.get("model_usage", {})
        if model_usage:
            lines.append("- **Cost by Model:**")
            for model, stats in sorted(model_usage.items()):
                cost = stats.get("cost", 0.0)
                calls = stats.get("calls", 0)
                lines.append(f"  - {model}: ${cost:.4f} ({calls} calls)")
        lines.append("")
        
        # Token Summary
        lines.append("#### Token Summary")
        total_input = result.get("total_input_tokens", 0)
        total_output = result.get("total_output_tokens", 0)
        total_tokens = result.get("total_tokens", total_input + total_output)
        lines.append(f"- **Total Tokens:** {total_tokens:,} (Input: {total_input:,} | Output: {total_output:,})")
        
        token_breakdown = result.get("token_breakdown", {})
        if token_breakdown:
            lines.append("- **Tokens by Extraction Type:**")
            for extract_type in ["progress", "financial", "market", "company", "team"]:
                if extract_type in token_breakdown:
                    breakdown = token_breakdown[extract_type]
                    tokens = breakdown.get("total_tokens", 0)
                    cost = breakdown.get("cost", 0.0)
                    lines.append(f"  - {extract_type}: {tokens:,} tokens (${cost:.4f})")
        lines.append("")
        
        # Performance
        lines.append("#### Performance")
        lines.append(f"- **Processing Time:** {result.get('processing_time', 0.0):.2f}s")
        lines.append(f"- **Cache Hits:** {result.get('cache_hits', 0)}")
        lines.append("")
        
        # Quality Metrics
        lines.append("#### Quality Metrics")
        confidence_scores = result.get("confidence_scores", {})
        if confidence_scores:
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
            lines.append(f"- **Average Confidence:** {avg_confidence:.2f}")
            lines.append("- **Confidence by Type:**")
            for extract_type, conf in confidence_scores.items():
                lines.append(f"  - {extract_type}: {conf:.2f}")
        else:
            lines.append("- **Average Confidence:** N/A")
        
        validation_errors = result.get("validation_errors", [])
        lines.append(f"- **Validation Errors:** {len(validation_errors)}")
        if validation_errors:
            lines.append("  - Error Details:")
            for error in validation_errors[:10]:  # Limit to first 10 errors
                lines.append(f"    - {error}")
            if len(validation_errors) > 10:
                lines.append(f"    - ... and {len(validation_errors) - 10} more errors")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Quality Analysis
    lines.append("## Quality Analysis")
    lines.append("")
    lines.append("### Confidence Scores by Extraction Type")
    lines.append("")
    lines.append("| Plan | Progress | Financial | Market | Company | Team | Average |")
    lines.append("|------|----------|-----------|--------|---------|------|---------|")
    
    for plan_name, result in results.items():
        confidence_scores = result.get("confidence_scores", {})
        progress_conf = confidence_scores.get("progress", 0.0)
        financial_conf = confidence_scores.get("financial", 0.0)
        market_conf = confidence_scores.get("market", 0.0)
        company_conf = confidence_scores.get("company", 0.0)
        team_conf = confidence_scores.get("team", 0.0)
        avg_conf = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
        
        lines.append(
            f"| {plan_name} | {progress_conf:.2f} | {financial_conf:.2f} | "
            f"{market_conf:.2f} | {company_conf:.2f} | {team_conf:.2f} | {avg_conf:.2f} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Cost Efficiency Analysis
    lines.append("## Cost Efficiency Analysis")
    lines.append("")
    if results:
        costs = [r.get("total_cost", 0.0) for r in results.values()]
        min_cost = min(costs)
        max_cost = max(costs)
        
        lines.append(f"- **Cheapest Plan:** {min([(name, r) for name, r in results.items()], key=lambda x: x[1].get('total_cost', float('inf')))[0]} (${min_cost:.4f})")
        lines.append(f"- **Most Expensive Plan:** {max([(name, r) for name, r in results.items()], key=lambda x: x[1].get('total_cost', 0))[0]} (${max_cost:.4f})")
        if max_cost > 0:
            lines.append(f"- **Cost Ratio:** {max_cost / min_cost:.2f}x")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    if best_plan:
        plan_name, result, avg_conf, errors, cost = best_plan
        lines.append(f"### Best Overall Plan: {plan_name}")
        lines.append("")
        lines.append(f"This plan was selected based on a composite score considering:")
        lines.append(f"- Average confidence: {avg_conf:.2f}")
        lines.append(f"- Validation errors: {errors}")
        lines.append(f"- Cost: ${cost:.4f}")
        lines.append("")
        
        if avg_conf >= 0.8:
            lines.append("✅ **Quality Target Met:** This plan achieves the 0.8 confidence target.")
        else:
            lines.append("⚠️ **Quality Target Not Met:** Consider improvements to reach 0.8 confidence.")
        lines.append("")
        
        if errors == 0:
            lines.append("✅ **No Validation Errors:** All extracted data passed validation.")
        else:
            lines.append(f"⚠️ **Validation Errors Present:** {errors} errors need attention.")
        lines.append("")
    
    lines.append("### Use Case Recommendations")
    lines.append("")
    lines.append("- **Quality-Focused:** Use the plan with highest confidence and zero errors")
    lines.append("- **Cost-Optimized:** Use the plan with lowest cost that meets quality thresholds")
    lines.append("- **Balanced:** Use the plan with best quality-to-cost ratio")
    lines.append("")
    
    return "\n".join(lines)


def generate_best_strategy_recommendation(
    results: Dict[str, Any],
    best_plan: tuple
) -> str:
    """Generate best strategy recommendation with detailed rationale"""
    lines = []
    
    lines.append("# Best Strategy Recommendation")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    if not best_plan:
        lines.append("## ⚠️ No Plans Completed Successfully")
        lines.append("")
        lines.append("Unable to provide a recommendation. Please review errors and retry.")
        return "\n".join(lines)
    
    plan_name, result, avg_conf, errors, cost = best_plan
    lines.append(f"## Recommended Plan: **{plan_name}**")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Key Metrics
    lines.append("## Key Metrics")
    lines.append("")
    lines.append(f"- **Average Confidence Score:** {avg_conf:.2f}")
    lines.append(f"- **Validation Errors:** {errors}")
    lines.append(f"- **Total Cost:** ${cost:.4f}")
    lines.append(f"- **Processing Time:** {result['processing_time']:.2f}s")
    lines.append(f"- **Total Tokens:** {result.get('total_tokens', 0):,}")
    lines.append("")
    
    # Quality Analysis
    lines.append("## Quality-Focused Analysis")
    lines.append("")
    confidence_scores = result.get("confidence_scores", {})
    if confidence_scores:
        lines.append("### Confidence Scores by Extraction Type:")
        lines.append("")
        for extract_type, conf in confidence_scores.items():
            status = "✅" if conf >= 0.8 else "⚠️"
            lines.append(f"- {status} **{extract_type}:** {conf:.2f}")
        lines.append("")
    
    if avg_conf >= 0.8:
        lines.append("✅ **Quality Target Achieved:** This plan meets the 0.8 confidence target.")
    else:
        lines.append("⚠️ **Quality Target Not Met:** Confidence is below 0.8. Consider:")
        lines.append("  - Enhancing prompts for better extraction")
        lines.append("  - Using a more powerful model for critical extractions")
        lines.append("  - Improving data validation and post-processing")
    lines.append("")
    
    if errors == 0:
        lines.append("✅ **Data Validation:** All extracted data passed validation checks.")
    else:
        lines.append(f"⚠️ **Data Validation Issues:** {errors} validation errors detected.")
        lines.append("  - Review validation error details in detailed_comparison.md")
        lines.append("  - Consider improving data type handling in extraction logic")
    lines.append("")
    
    # Cost-Benefit Analysis
    lines.append("## Cost-Benefit Analysis")
    lines.append("")
    
    # Compare with other plans
    other_plans = [(name, r) for name, r in results.items() if name != plan_name]
    if other_plans:
        costs = [r.get("total_cost", 0.0) for _, r in other_plans]
        avg_other_cost = sum(costs) / len(costs) if costs else cost
        
        lines.append(f"- **This Plan Cost:** ${cost:.4f}")
        lines.append(f"- **Average Other Plans Cost:** ${avg_other_cost:.4f}")
        if avg_other_cost > 0:
            savings = ((avg_other_cost - cost) / avg_other_cost) * 100
            if savings > 0:
                lines.append(f"- **Cost Savings:** {savings:.1f}% compared to average")
            else:
                lines.append(f"- **Cost Premium:** {abs(savings):.1f}% compared to average")
        lines.append("")
    
    # Quality vs Cost Trade-off
    lines.append("### Quality vs Cost Trade-off")
    lines.append("")
    quality_cost_ratio = avg_conf / cost if cost > 0 else 0
    lines.append(f"- **Quality-to-Cost Ratio:** {quality_cost_ratio:.2f} (higher is better)")
    lines.append("")
    
    # Use Case Recommendations
    lines.append("## Use Case Recommendations")
    lines.append("")
    lines.append("### When to Use This Plan:")
    lines.append("")
    
    if avg_conf >= 0.8 and errors == 0:
        lines.append("✅ **Recommended for production use** when:")
        lines.append("  - High accuracy is critical")
        lines.append("  - Data quality cannot be compromised")
        lines.append("  - Cost is acceptable for quality level")
    else:
        lines.append("⚠️ **Consider alternatives** if:")
        if avg_conf < 0.8:
            lines.append("  - Higher confidence scores are required")
        if errors > 0:
            lines.append("  - Zero validation errors are mandatory")
    lines.append("")
    
    # Alternative Plans
    lines.append("### Alternative Plans to Consider:")
    lines.append("")
    for name, r in results.items():
        if name == plan_name:
            continue
        
        alt_conf_scores = r.get("confidence_scores", {})
        alt_avg_conf = sum(alt_conf_scores.values()) / len(alt_conf_scores) if alt_conf_scores else 0.0
        alt_errors = len(r.get("validation_errors", []))
        alt_cost = r.get("total_cost", 0.0)
        
        lines.append(f"#### {name}")
        lines.append(f"- Confidence: {alt_avg_conf:.2f}")
        lines.append(f"- Errors: {alt_errors}")
        lines.append(f"- Cost: ${alt_cost:.4f}")
        
        if alt_avg_conf > avg_conf:
            lines.append("  - ⬆️ Higher confidence than recommended plan")
        if alt_cost < cost:
            lines.append("  - ⬇️ Lower cost than recommended plan")
        lines.append("")
    
    # Implementation Notes
    lines.append("## Implementation Notes")
    lines.append("")
    lines.append("To use this plan in production:")
    lines.append("")
    
    # Generate appropriate import based on plan name
    if plan_name == "Baseline":
        import_code = "from app.services.extraction import OptimizedExtractor\n\nextractor = OptimizedExtractor(use_cache=True)"
    elif plan_name.startswith("Plan "):
        plan_letter = plan_name.split()[-1].lower()
        class_name = f"ExtractorPlan{plan_letter.upper()}"
        import_code = f"from app.services.extraction.strategies.plan_{plan_letter} import {class_name}\n\n{class_name}(use_cache=True)"
    else:
        import_code = f"# Import and usage for {plan_name} - see detailed_comparison.md for implementation details"
    
    lines.append("```python")
    lines.append(import_code)
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)


def print_comprehensive_summary(results: Dict[str, Any]) -> str:
    """Print comprehensive summary of all plans with detailed metrics"""
    summary_lines = []
    
    summary_lines.append("=" * 70)
    summary_lines.append("COMPREHENSIVE SUMMARY - ALL PLANS")
    summary_lines.append("=" * 70)
    summary_lines.append("")
    
    for plan_name, result in results.items():
        summary_lines.append(f"Plan: {plan_name}")
        summary_lines.append("├─ Cost Summary")
        summary_lines.append(f"│  ├─ Total Cost: ${result['total_cost']:.4f}")
        
        # Cost by model
        model_usage = result.get("model_usage", {})
        if model_usage:
            summary_lines.append("│  ├─ Cost by Model:")
            for model, stats in sorted(model_usage.items()):
                cost = stats.get("cost", 0.0)
                calls = stats.get("calls", 0)
                summary_lines.append(f"│  │  ├─ {model}: ${cost:.4f} ({calls} calls)")
        
        # Token summary
        summary_lines.append("├─ Token Summary")
        total_input = result.get("total_input_tokens", 0)
        total_output = result.get("total_output_tokens", 0)
        total_tokens = result.get("total_tokens", total_input + total_output)
        summary_lines.append(f"│  ├─ Total Tokens: {total_tokens:,} (Input: {total_input:,} | Output: {total_output:,})")
        
        # Tokens by extraction type
        token_breakdown = result.get("token_breakdown", {})
        if token_breakdown:
            summary_lines.append("│  ├─ Tokens by Extraction Type:")
            for extract_type in ["progress", "financial", "market", "company", "team"]:
                if extract_type in token_breakdown:
                    breakdown = token_breakdown[extract_type]
                    tokens = breakdown.get("total_tokens", 0)
                    cost = breakdown.get("cost", 0.0)
                    summary_lines.append(f"│  │  ├─ {extract_type}: {tokens:,} tokens (${cost:.4f})")
        
        # Performance
        summary_lines.append("├─ Performance")
        summary_lines.append(f"│  ├─ Processing Time: {result['processing_time']:.2f}s")
        cache_hits = result.get("cache_hits", 0)
        summary_lines.append(f"│  └─ Cache Hits: {cache_hits}")
        
        # Quality metrics
        summary_lines.append("└─ Quality Metrics")
        confidence_scores = result.get("confidence_scores", {})
        if confidence_scores:
            avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
            summary_lines.append(f"   ├─ Average Confidence: {avg_confidence:.2f}")
        else:
            summary_lines.append("   ├─ Average Confidence: N/A")
        summary_lines.append(f"   └─ Validation Errors: {len(result.get('validation_errors', []))}")
        
        summary_lines.append("")
    
    # Comparison table
    summary_lines.append("=" * 70)
    summary_lines.append("COMPARISON TABLE")
    summary_lines.append("=" * 70)
    summary_lines.append(f"{'Plan':<12} | {'Cost':<10} | {'Tokens (I/O)':<20} | {'Time':<8} | {'Confidence':<12} | {'Errors':<8}")
    summary_lines.append("-" * 70)
    
    for plan_name, result in results.items():
        cost = result.get("total_cost", 0.0)
        input_tokens = result.get("total_input_tokens", 0)
        output_tokens = result.get("total_output_tokens", 0)
        time_val = result.get("processing_time", 0.0)
        confidence_scores = result.get("confidence_scores", {})
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
        errors = len(result.get("validation_errors", []))
        
        tokens_str = f"{input_tokens:,} / {output_tokens:,}"
        summary_lines.append(
            f"{plan_name:<12} | ${cost:<9.4f} | {tokens_str:<20} | {time_val:<7.2f}s | {avg_confidence:<11.2f} | {errors:<8}"
        )
    
    summary_text = "\n".join(summary_lines)
    print(summary_text)
    return summary_text


async def main(use_cache: bool = True):
    """Run all extraction plans and compare results"""
    cache_status = "ENABLED" if use_cache else "DISABLED"
    print("="*70)
    print("EXTRACTION PLAN COMPARISON TEST")
    print("="*70)
    print(f"\nCache: {cache_status}")
    print("\nTesting on Nexus AI mock data (perfect data, should get >0.8 confidence)")
    
    results = {}
    
    # Baseline
    print("\n" + "="*70)
    print("BASELINE (Current Implementation)")
    print("="*70)
    baseline_extractor = OptimizedExtractor(use_cache=use_cache)
    documents = load_test_documents("Nexus AI")
    parser = LangChainDocumentParser()
    chunks = await parser.parse_documents(documents)
    router = SemanticRouter()
    routed_chunks = await router.route_chunks(chunks)
    results["Baseline"] = await run_extraction_plan("Baseline", baseline_extractor, routed_chunks, 
                                                    ["progress", "financial", "market", "company", "team"])
    
    # Plan A
    print("\n" + "="*70)
    print("PLAN A (Structured Outputs)")
    print("="*70)
    try:
        results["Plan A"] = await run_full_pipeline_test("Nexus AI", "Plan A", ExtractorPlanA, use_cache=use_cache)
    except Exception as e:
        print(f"Plan A failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Plan B
    print("\n" + "="*70)
    print("PLAN B (Enhanced Prompts + Validation)")
    print("="*70)
    try:
        results["Plan B"] = await run_full_pipeline_test("Nexus AI", "Plan B", ExtractorPlanB, use_cache=use_cache)
    except Exception as e:
        print(f"Plan B failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Plan C
    print("\n" + "="*70)
    print("PLAN C (Hybrid: GPT-4o + Claude)")
    print("="*70)
    try:
        results["Plan C"] = await run_full_pipeline_test("Nexus AI", "Plan C", ExtractorPlanC, use_cache=use_cache)
    except Exception as e:
        print(f"Plan C failed (may need CLAUDE_API_KEY): {e}")
    
    # Plan D
    print("\n" + "="*70)
    print("PLAN D (Cost-Optimized with Retry)")
    print("="*70)
    try:
        results["Plan D"] = await run_full_pipeline_test("Nexus AI", "Plan D", ExtractorPlanD, use_cache=use_cache)
    except Exception as e:
        print(f"Plan D failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Print comprehensive summary
    summary_text = print_comprehensive_summary(results)
    
    # Find best plan
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)
    
    best_plan = None
    best_score = 0.0
    
    for plan_name, result in results.items():
        confidence_scores = result["confidence_scores"]
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
        error_count = len(result["validation_errors"])
        
        # Score: confidence - (errors * 0.1)
        score = avg_confidence - (error_count * 0.1)
        
        if score > best_score:
            best_score = score
            best_plan = (plan_name, result, avg_confidence, error_count, result['total_cost'])
    
    if best_plan:
        plan_name, result, avg_conf, errors, cost = best_plan
        print(f"\n✅ Best Plan: {plan_name}")
        print(f"   Average Confidence: {avg_conf:.2f}")
        print(f"   Validation Errors: {errors}")
        print(f"   Cost: ${cost:.4f}")
        print(f"   Time: {result['processing_time']:.2f}s")
        
        if avg_conf >= 0.8:
            print(f"\n   🎉 This plan meets the 0.8 confidence target!")
        else:
            print(f"\n   ⚠️  Confidence below 0.8 target. Consider improvements.")
    
    # Generate detailed comparison outputs
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_dir = Path("runtime/outputs/comparison") / f"comparison_{timestamp}"
        comparison_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate all comparison outputs
        generate_comparison_outputs(results, best_plan, comparison_dir, summary_text)
        
        # Also save legacy summary for backward compatibility
        outputs_dir = Path("runtime/outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)
        summary_file = outputs_dir / f"extraction_summary_{timestamp}.txt"
        
        # Add recommendation to summary text
        full_summary = summary_text
        if best_plan:
            plan_name, result, avg_conf, errors, cost = best_plan
            full_summary += f"\n\n{'='*70}\n"
            full_summary += f"RECOMMENDATION\n"
            full_summary += f"{'='*70}\n"
            full_summary += f"\n✅ Best Plan: {plan_name}\n"
            full_summary += f"   Average Confidence: {avg_conf:.2f}\n"
            full_summary += f"   Validation Errors: {errors}\n"
            full_summary += f"   Cost: ${cost:.4f}\n"
            full_summary += f"   Time: {result['processing_time']:.2f}s\n"
            if avg_conf >= 0.8:
                full_summary += f"\n   🎉 This plan meets the 0.8 confidence target!\n"
            else:
                full_summary += f"\n   ⚠️  Confidence below 0.8 target. Consider improvements.\n"
        
        summary_file.write_text(full_summary, encoding="utf-8")
        print(f"\n{'='*70}")
        print(f"✅ Legacy summary saved to: {summary_file.absolute()}")
        print(f"✅ Detailed comparison outputs saved to: {comparison_dir.absolute()}")
        print(f"{'='*70}")
        
        # Record in performance tracker
        try:
            from tests.performance.tracker import PerformanceTracker
            tracker = PerformanceTracker()
            run_id = tracker.record_run(
                results=results,
                test_name="extraction_comparison",
                notes=f"Cache: {cache_status}. Fixed Plan C bugs."
            )
            print(f"✅ Performance metrics recorded (run_id: {run_id})")
            
            # Generate and print performance report
            report = tracker.generate_report()
            print(f"\n{report}")
        except Exception as e:
            print(f"\n⚠️  Failed to record performance metrics: {e}")
            import traceback
            traceback.print_exc()
    except Exception as e:
        print(f"\n⚠️  Failed to save outputs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test all extraction plans and compare results")
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable cache for all extractions (fresh test run)"
    )
    args = parser.parse_args()
    
    use_cache = not args.no_cache
    asyncio.run(main(use_cache=use_cache))

