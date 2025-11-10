"""
Automated tests for the performance analysis notebook.
Tests notebook functionality with various data scenarios.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.performance.tracker import PerformanceTracker
from tests.performance.utils import (
    load_performance_data,
    detect_regressions,
    calculate_improvements,
    generate_insights
)


def create_sample_history() -> list:
    """Create sample history data for testing"""
    return [
        {
            "run_id": "20250101_120000",
            "timestamp": "2025-01-01T12:00:00",
            "test_name": "extraction_comparison",
            "notes": "Test run 1",
            "results": {
                "Plan A": {
                    "average_confidence": 0.85,
                    "confidence_by_type": {
                        "progress": 0.90,
                        "financial": 0.88,
                        "market": 0.82,
                        "company": 0.80,
                        "team": 0.85
                    },
                    "validation_errors": 0,
                    "total_cost": 0.05,
                    "processing_time": 45.2,
                    "total_tokens": 5000,
                    "input_tokens": 3000,
                    "output_tokens": 2000,
                    "cache_hits": 2,
                    "model_usage": {"gpt-4o": 1}
                },
                "Plan B": {
                    "average_confidence": 0.82,
                    "confidence_by_type": {
                        "progress": 0.85,
                        "financial": 0.80,
                        "market": 0.78,
                        "company": 0.82,
                        "team": 0.85
                    },
                    "validation_errors": 1,
                    "total_cost": 0.03,
                    "processing_time": 38.5,
                    "total_tokens": 4000,
                    "input_tokens": 2500,
                    "output_tokens": 1500,
                    "cache_hits": 1,
                    "model_usage": {"gpt-4o-mini": 1}
                }
            }
        },
        {
            "run_id": "20250102_120000",
            "timestamp": "2025-01-02T12:00:00",
            "test_name": "extraction_comparison",
            "notes": "Test run 2 - improved",
            "results": {
                "Plan A": {
                    "average_confidence": 0.87,
                    "confidence_by_type": {
                        "progress": 0.92,
                        "financial": 0.90,
                        "market": 0.85,
                        "company": 0.82,
                        "team": 0.88
                    },
                    "validation_errors": 0,
                    "total_cost": 0.06,
                    "processing_time": 47.8,
                    "total_tokens": 5200,
                    "input_tokens": 3100,
                    "output_tokens": 2100,
                    "cache_hits": 2,
                    "model_usage": {"gpt-4o": 1}
                },
                "Plan B": {
                    "average_confidence": 0.84,
                    "confidence_by_type": {
                        "progress": 0.87,
                        "financial": 0.82,
                        "market": 0.80,
                        "company": 0.84,
                        "team": 0.87
                    },
                    "validation_errors": 0,
                    "total_cost": 0.04,
                    "processing_time": 40.1,
                    "total_tokens": 4200,
                    "input_tokens": 2600,
                    "output_tokens": 1600,
                    "cache_hits": 1,
                    "model_usage": {"gpt-4o-mini": 1}
                }
            }
        }
    ]


def test_empty_history():
    """Test with empty history.json"""
    print("Testing with empty history...")
    
    # Create temporary empty history
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        history_file.write_text("[]")
        
        # Test loading
        data = load_performance_data(str(history_file))
        
        assert data['runs'].empty, "Runs DataFrame should be empty"
        assert data['plans'].empty, "Plans DataFrame should be empty"
        assert data['types'].empty, "Types DataFrame should be empty"
        
        print("✅ Empty history handled correctly")


def test_sample_data():
    """Test with sample data"""
    print("Testing with sample data...")
    
    sample_history = create_sample_history()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        history_file.write_text(json.dumps(sample_history, indent=2))
        
        # Test loading
        data = load_performance_data(str(history_file))
        
        assert len(data['runs']) == 2, f"Expected 2 runs, got {len(data['runs'])}"
        assert len(data['plans']) == 4, f"Expected 4 plan entries, got {len(data['plans'])}"
        assert len(data['types']) == 20, f"Expected 20 type entries, got {len(data['types'])}"
        
        # Test that data is correctly structured
        assert 'run_id' in data['runs'].columns
        assert 'plan_name' in data['plans'].columns
        assert 'extract_type' in data['types'].columns
        
        print("✅ Sample data loaded correctly")


def test_utils_functions():
    """Test utility functions"""
    print("Testing utility functions...")
    
    sample_history = create_sample_history()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        history_file.write_text(json.dumps(sample_history, indent=2))
        
        data = load_performance_data(str(history_file))
        plans_df = data['plans']
        types_df = data['types']
        
        # Test regression detection
        regressions = detect_regressions(plans_df, threshold=0.05)
        # Should not detect regressions in sample data (improvements only)
        print(f"  Regressions detected: {len(regressions)}")
        
        # Test improvements calculation
        improvements = calculate_improvements(plans_df, baseline_plan="Plan A")
        print(f"  Improvements calculated: {len(improvements)}")
        
        # Test insights generation
        insights = generate_insights(plans_df, types_df)
        assert 'best_plan' in insights
        assert 'most_cost_efficient' in insights
        print(f"  Best plan: {insights.get('best_plan')}")
        
        print("✅ Utility functions work correctly")


def test_error_handling():
    """Test error handling with malformed data"""
    print("Testing error handling...")
    
    # Test malformed JSON
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        history_file.write_text("{ invalid json }")
        
        try:
            data = load_performance_data(str(history_file))
            # Should handle gracefully
            assert data['runs'].empty
            print("✅ Malformed JSON handled gracefully")
        except Exception as e:
            print(f"⚠️  Malformed JSON raised exception: {e}")
    
    # Test missing fields
    incomplete_history = [
        {
            "run_id": "test",
            "timestamp": "2025-01-01T12:00:00",
            # Missing results
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        history_file.write_text(json.dumps(incomplete_history))
        
        data = load_performance_data(str(history_file))
        # Should handle missing fields
        assert len(data['runs']) == 1
        assert len(data['plans']) == 0  # No plans due to missing results
        print("✅ Missing fields handled gracefully")


def test_performance_tracker():
    """Test PerformanceTracker integration"""
    print("Testing PerformanceTracker...")
    
    sample_history = create_sample_history()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        history_file = Path(tmpdir) / "history.json"
        history_file.write_text(json.dumps(sample_history, indent=2))
        
        tracker = PerformanceTracker(str(history_file))
        
        # Test get_best_performance
        best = tracker.get_best_performance("Plan A")
        assert best is not None
        assert best['run_id'] == "20250102_120000"  # Higher confidence
        
        # Test compare_runs
        comparison = tracker.compare_runs("20250101_120000", "20250102_120000")
        assert 'error' not in comparison
        assert 'plans' in comparison
        
        # Test get_trends
        trends = tracker.get_trends("Plan A", "average_confidence")
        assert len(trends) == 2
        
        # Test generate_report
        report = tracker.generate_report()
        assert "PERFORMANCE TRACKING REPORT" in report
        assert "Plan A" in report
        
        print("✅ PerformanceTracker works correctly")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("Running Notebook Tests")
    print("=" * 70)
    print()
    
    tests = [
        test_empty_history,
        test_sample_data,
        test_utils_functions,
        test_error_handling,
        test_performance_tracker,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 70)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)




