"""
Performance benchmarks and targets for extraction plans.
Defines quality thresholds and cost targets.
"""

from typing import Dict, Any


# Performance targets
PERFORMANCE_TARGETS = {
    "confidence_threshold": 0.8,  # Minimum acceptable confidence score
    "target_confidence": 0.85,    # Target confidence score
    "max_validation_errors": 0,   # Maximum acceptable validation errors
    "max_cost_per_memo": 0.10,     # Maximum cost per memo (in USD)
    "max_processing_time": 60.0,   # Maximum processing time in seconds
}

# Cost targets by plan
COST_TARGETS = {
    "Baseline": 0.001,   # Very cheap (uses Ollama)
    "Plan A": 0.10,      # Higher cost acceptable for quality
    "Plan B": 0.005,     # Moderate cost
    "Plan C": 0.05,      # Moderate cost (Claude + GPT-4o)
    "Plan D": 0.01,      # Low cost (GPT-4o-mini with retry)
}

# Quality targets by extraction type
QUALITY_TARGETS = {
    "progress": 0.85,    # High confidence needed for financial metrics
    "financial": 0.85,   # High confidence needed for financial data
    "market": 0.80,      # Moderate confidence acceptable
    "company": 0.80,     # Moderate confidence acceptable
    "team": 0.80,        # Moderate confidence acceptable
}


def evaluate_performance(plan_result: Dict[str, Any], plan_name: str) -> Dict[str, Any]:
    """
    Evaluate plan performance against benchmarks
    
    Args:
        plan_result: Result dictionary from test run
        plan_name: Name of the plan being evaluated
    
    Returns:
        Dictionary with evaluation results
    """
    confidence_scores = plan_result.get("confidence_scores", {})
    avg_confidence = (
        sum(confidence_scores.values()) / len(confidence_scores)
        if confidence_scores else 0.0
    )
    
    validation_errors = len(plan_result.get("validation_errors", []))
    cost = plan_result.get("total_cost", 0.0)
    processing_time = plan_result.get("processing_time", 0.0)
    
    evaluation = {
        "plan_name": plan_name,
        "meets_confidence_threshold": avg_confidence >= PERFORMANCE_TARGETS["confidence_threshold"],
        "meets_target_confidence": avg_confidence >= PERFORMANCE_TARGETS["target_confidence"],
        "meets_error_threshold": validation_errors <= PERFORMANCE_TARGETS["max_validation_errors"],
        "meets_cost_target": cost <= COST_TARGETS.get(plan_name, PERFORMANCE_TARGETS["max_cost_per_memo"]),
        "meets_time_target": processing_time <= PERFORMANCE_TARGETS["max_processing_time"],
        "confidence_score": avg_confidence,
        "validation_errors": validation_errors,
        "cost": cost,
        "processing_time": processing_time,
        "overall_passing": False,
    }
    
    # Overall passing if all critical metrics pass
    evaluation["overall_passing"] = (
        evaluation["meets_confidence_threshold"] and
        evaluation["meets_error_threshold"] and
        evaluation["meets_cost_target"] and
        evaluation["meets_time_target"]
    )
    
    return evaluation


def compare_to_baseline(current_result: Dict[str, Any], baseline_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare current result to baseline
    
    Args:
        current_result: Current plan result
        baseline_result: Baseline plan result
    
    Returns:
        Comparison dictionary
    """
    current_conf = (
        sum(current_result.get("confidence_scores", {}).values()) /
        len(current_result.get("confidence_scores", {}))
        if current_result.get("confidence_scores") else 0.0
    )
    
    baseline_conf = (
        sum(baseline_result.get("confidence_scores", {}).values()) /
        len(baseline_result.get("confidence_scores", {}))
        if baseline_result.get("confidence_scores") else 0.0
    )
    
    return {
        "confidence_improvement": current_conf - baseline_conf,
        "cost_difference": current_result.get("total_cost", 0.0) - baseline_result.get("total_cost", 0.0),
        "time_difference": current_result.get("processing_time", 0.0) - baseline_result.get("processing_time", 0.0),
        "errors_difference": (
            len(current_result.get("validation_errors", [])) -
            len(baseline_result.get("validation_errors", []))
        ),
    }

