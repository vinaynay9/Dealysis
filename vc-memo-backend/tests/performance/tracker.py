"""
Performance tracking system for extraction model improvements.
Tracks historical metrics to enable ML-style continuous improvement.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class PerformanceTracker:
    """Track and compare extraction performance metrics over time"""
    
    def __init__(self, history_file: str = "tests/performance/history.json"):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load historical test results"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_history(self):
        """Save historical test results"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
    
    def record_run(
        self,
        results: Dict[str, Any],
        test_name: str = "extraction_comparison",
        notes: Optional[str] = None
    ) -> str:
        """
        Record a test run with all metrics
        
        Args:
            results: Dictionary with plan results (from test_all_extraction_plans)
            test_name: Name/identifier for this test run
            notes: Optional notes about this run (e.g., "Fixed Plan C bugs")
        
        Returns:
            run_id: Unique identifier for this run
        """
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        run_data = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "notes": notes,
            "results": {}
        }
        
        # Extract metrics for each plan
        for plan_name, plan_result in results.items():
            confidence_scores = plan_result.get("confidence_scores", {})
            avg_confidence = (
                sum(confidence_scores.values()) / len(confidence_scores)
                if confidence_scores else 0.0
            )
            
            run_data["results"][plan_name] = {
                "average_confidence": avg_confidence,
                "confidence_by_type": confidence_scores,
                "validation_errors": len(plan_result.get("validation_errors", [])),
                "total_cost": plan_result.get("total_cost", 0.0),
                "processing_time": plan_result.get("processing_time", 0.0),
                "total_tokens": plan_result.get("total_tokens", 0),
                "input_tokens": plan_result.get("total_input_tokens", 0),
                "output_tokens": plan_result.get("total_output_tokens", 0),
                "cache_hits": plan_result.get("cache_hits", 0),
                "model_usage": plan_result.get("model_usage", {}),
            }
        
        self.history.append(run_data)
        self._save_history()
        
        return run_id
    
    def get_best_performance(self, plan_name: str) -> Optional[Dict[str, Any]]:
        """Get the best performance for a specific plan"""
        best = None
        best_score = 0.0
        
        for run in self.history:
            if plan_name in run["results"]:
                score = run["results"][plan_name]["average_confidence"]
                if score > best_score:
                    best_score = score
                    best = run
        
        return best
    
    def compare_runs(self, run_id_1: str, run_id_2: str) -> Dict[str, Any]:
        """Compare two test runs"""
        run1 = next((r for r in self.history if r["run_id"] == run_id_1), None)
        run2 = next((r for r in self.history if r["run_id"] == run_id_2), None)
        
        if not run1 or not run2:
            return {"error": "One or both runs not found"}
        
        comparison = {
            "run1": run1["run_id"],
            "run2": run2["run_id"],
            "timestamp1": run1["timestamp"],
            "timestamp2": run2["timestamp"],
            "plans": {}
        }
        
        # Compare each plan
        for plan_name in set(list(run1["results"].keys()) + list(run2["results"].keys())):
            if plan_name in run1["results"] and plan_name in run2["results"]:
                r1 = run1["results"][plan_name]
                r2 = run2["results"][plan_name]
                
                comparison["plans"][plan_name] = {
                    "confidence_change": r2["average_confidence"] - r1["average_confidence"],
                    "cost_change": r2["total_cost"] - r1["total_cost"],
                    "time_change": r2["processing_time"] - r1["processing_time"],
                    "errors_change": r2["validation_errors"] - r1["validation_errors"],
                }
        
        return comparison
    
    def get_trends(self, plan_name: str, metric: str = "average_confidence") -> List[Dict[str, Any]]:
        """Get trend data for a specific plan and metric"""
        trends = []
        
        for run in self.history:
            if plan_name in run["results"]:
                trends.append({
                    "run_id": run["run_id"],
                    "timestamp": run["timestamp"],
                    "value": run["results"][plan_name].get(metric, 0.0),
                    "notes": run.get("notes", "")
                })
        
        return sorted(trends, key=lambda x: x["timestamp"])
    
    def generate_report(self) -> str:
        """Generate a text report of performance trends"""
        lines = []
        lines.append("=" * 70)
        lines.append("PERFORMANCE TRACKING REPORT")
        lines.append("=" * 70)
        lines.append(f"\nTotal runs recorded: {len(self.history)}")
        lines.append("")
        
        if not self.history:
            lines.append("No test runs recorded yet.")
            return "\n".join(lines)
        
        # Get latest run
        latest = self.history[-1]
        lines.append(f"Latest run: {latest['run_id']} ({latest['timestamp']})")
        if latest.get("notes"):
            lines.append(f"Notes: {latest['notes']}")
        lines.append("")
        
        # Show best performance per plan
        lines.append("Best Performance by Plan:")
        lines.append("-" * 70)
        for plan_name in ["Baseline", "Plan A", "Plan B", "Plan C", "Plan D"]:
            best = self.get_best_performance(plan_name)
            if best:
                result = best["results"][plan_name]
                lines.append(
                    f"{plan_name:<12} | Confidence: {result['average_confidence']:.2f} | "
                    f"Cost: ${result['total_cost']:.4f} | Run: {best['run_id']}"
                )
        lines.append("")
        
        # Show trends
        lines.append("Confidence Score Trends:")
        lines.append("-" * 70)
        for plan_name in ["Plan A", "Plan B", "Plan C", "Plan D"]:
            trends = self.get_trends(plan_name, "average_confidence")
            if trends:
                latest_value = trends[-1]["value"]
                if len(trends) > 1:
                    previous_value = trends[-2]["value"]
                    change = latest_value - previous_value
                    change_str = f"({change:+.2f})" if change != 0 else "(no change)"
                else:
                    change_str = "(baseline)"
                
                lines.append(f"{plan_name:<12} | Latest: {latest_value:.2f} {change_str}")
        
        return "\n".join(lines)

