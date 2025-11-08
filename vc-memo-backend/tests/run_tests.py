"""
Test runner script to execute all tests
"""
import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all tests using pytest"""
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Change to project root
    os.chdir(project_root)
    
    print("=" * 70)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()
    
    # Test files to run
    test_files = [
        "tests/test_local_llm.py",
        "tests/test_extractors.py",
        "tests/test_fact_checking.py",
        "tests/test_confidence_scoring.py",
        "tests/test_context_enrichment.py",
        "tests/test_pipeline_integration.py",
        "tests/test_api_enhanced.py",
    ]
    
    # Run tests with verbose output
    cmd = [
        sys.executable,
        "-m", "pytest",
        "-v",
        "--tb=short",
        "--color=yes"
    ] + test_files
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=project_root)
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)

