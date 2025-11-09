# Performance Tracking and Continuous Improvement

## Overview

This document describes the performance tracking system for the extraction model, enabling ML-style continuous improvement through systematic testing, measurement, and optimization.

## System Components

### 1. Performance Tracker (`tests/performance/tracker.py`)

Tracks historical test results and enables:
- Recording test run metrics
- Comparing runs over time
- Identifying trends and improvements
- Finding best performance per plan

### 2. Benchmarks (`tests/performance/benchmarks.py`)

Defines performance targets:
- **Confidence Threshold**: 0.8 (minimum acceptable)
- **Target Confidence**: 0.85 (goal)
- **Max Validation Errors**: 0
- **Cost Targets**: Vary by plan (see benchmarks.py)
- **Processing Time**: < 60 seconds

### 3. History Storage (`tests/performance/history.json`)

Stores all test run results with:
- Timestamp
- Plan performance metrics
- Confidence scores by extraction type
- Cost and token usage
- Notes about the run

## Improvement Workflow

### Step 1: Identify Issues

From test results, identify:
- Low confidence scores (< 0.8)
- Validation errors
- High costs
- Slow processing times

### Step 2: Hypothesize Solutions

Consider:
- **Prompt improvements**: More explicit instructions, examples
- **Model selection**: Different models for different extraction types
- **Validation enhancements**: Better post-processing, type coercion
- **Cost optimizations**: Caching, model routing, batch processing

### Step 3: Implement Changes

Make targeted improvements to:
- Extraction prompts
- Model selection logic
- Validation/fixing logic
- Cost optimization strategies

### Step 4: Test and Compare

1. Run full test suite: `python -m tests.comparison.test_all_extraction_plans --no-cache`
2. Record results in tracker
3. Compare to previous runs
4. Evaluate against benchmarks

### Step 5: Document Learnings

Record in this document:
- What changes were made
- What improved
- What didn't work
- Key insights

## Usage

### Recording a Test Run

```python
from tests.performance.tracker import PerformanceTracker

tracker = PerformanceTracker()
run_id = tracker.record_run(
    results=test_results,
    test_name="extraction_comparison",
    notes="Fixed Plan C async/await bugs"
)
```

### Comparing Runs

```python
comparison = tracker.compare_runs(run_id_1, run_id_2)
print(comparison)
```

### Getting Trends

```python
trends = tracker.get_trends("Plan A", "average_confidence")
for trend in trends:
    print(f"{trend['timestamp']}: {trend['value']:.2f}")
```

### Generating Report

```python
report = tracker.generate_report()
print(report)
```

## Performance History

### Key Improvements

*Track significant improvements here as they occur*

#### 2025-11-09: Fixed Plan C Extraction Bugs
- **Issue**: Plan C had 0.19 confidence (only team extractions working)
- **Root Cause**: Async/await bug and message role mapping issue
- **Fix**: Wrapped API calls in async functions, fixed role mapping
- **Result**: All extraction types now work correctly

## Best Practices

1. **Always run with `--no-cache`** for performance testing to get accurate metrics
2. **Record notes** about what changed between runs
3. **Compare to baseline** to ensure improvements don't regress
4. **Track costs** to avoid unexpected API spending
5. **Monitor trends** to catch gradual regressions

## Success Criteria

A plan is considered successful if it:
- ✅ Meets confidence threshold (≥ 0.8)
- ✅ Has zero validation errors
- ✅ Stays within cost target
- ✅ Completes within time limit (< 60s)

## Future Enhancements

- [ ] Automated regression testing
- [ ] Cost alerting system
- [ ] Performance dashboard/visualization
- [ ] A/B testing framework
- [ ] Automated optimization suggestions

