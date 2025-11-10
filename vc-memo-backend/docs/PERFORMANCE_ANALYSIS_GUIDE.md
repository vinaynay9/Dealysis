# Performance Analysis Notebook User Guide

## Overview

The Performance Analysis Notebook (`tests/performance/analysis.ipynb`) provides interactive analysis and visualization of extraction model performance over time. It enables you to track improvements, compare different extraction strategies, monitor costs, and evaluate performance against benchmarks.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Section-by-Section Guide](#section-by-section-guide)
4. [Common Use Cases](#common-use-cases)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Usage](#advanced-usage)
7. [API Reference](#api-reference)

## Getting Started

### Prerequisites

- **Jupyter Notebook** or **JupyterLab** installed
- **Python 3.8+** with the following packages:
  - `pandas`
  - `numpy`
  - `matplotlib`
  - `seaborn`
  - `jupyter`

### Installation

1. **Install dependencies** (if not already installed):
   ```bash
   pip install pandas numpy matplotlib seaborn jupyter
   ```

2. **Navigate to the project directory**:
   ```bash
   cd /path/to/vc-memo-backend
   ```

3. **Open the notebook**:
   ```bash
   jupyter notebook tests/performance/analysis.ipynb
   ```
   Or with JupyterLab:
   ```bash
   jupyter lab tests/performance/analysis.ipynb
   ```

### First Run

1. **Run all cells** to load and analyze data:
   - Click `Cell` → `Run All` in the menu
   - Or use keyboard shortcut: `Shift + Enter` on each cell

2. **Check the output**:
   - Section 1 will show how many test runs are loaded
   - If you see "No test runs recorded yet", you need to run tests first

3. **Generate test data** (if needed):
   ```bash
   python -m tests.comparison.test_all_extraction_plans --no-cache
   ```

## Basic Usage

### Running the Notebook

**Option 1: Run All Cells**
- Menu: `Cell` → `Run All`
- This executes all cells from top to bottom

**Option 2: Run Incrementally**
- Use `Shift + Enter` to run the current cell and move to the next
- Use `Ctrl + Enter` to run the current cell without moving

**Option 3: Run by Section**
- Run Section 1 (Setup) first
- Then run each section individually as needed

### Understanding the Output

The notebook is organized into 9 sections:

1. **Setup and Data Loading** - Loads and preprocesses data
2. **Overview Dashboard** - High-level summary statistics
3. **Trend Analysis** - Performance trends over time
4. **Plan Comparison** - Compare different extraction plans
5. **Run-by-Run Analysis** - Deep dive into specific test runs
6. **Statistical Analysis** - Advanced statistical insights
7. **Benchmark Evaluation** - Compare against performance targets
8. **Cost Analysis** - Financial tracking and optimization
9. **Export and Reporting** - Generate reports and export data

### Interpreting Visualizations

- **Confidence Scores**: Range from 0.0 to 1.0, higher is better
  - Target threshold: 0.8 (minimum acceptable)
  - Goal: 0.85 or higher

- **Cost**: Total cost in USD per memo generation
  - Target: Varies by plan (see benchmarks.py)

- **Processing Time**: Time in seconds to generate a memo
  - Target: < 60 seconds

- **Validation Errors**: Number of data validation errors
  - Target: 0 errors

## Section-by-Section Guide

### Section 1: Setup and Data Loading

**Purpose**: Initialize the environment and load performance data.

**What it does**:
- Imports required libraries
- Loads data from `history.json`
- Converts JSON data to pandas DataFrames for analysis
- Preprocesses data (adds computed columns, handles dates)

**What to look for**:
- Number of test runs loaded
- Date range of runs
- Plans tested
- Any error messages

**When to use**: Always run this section first.

### Section 2: Overview Dashboard

**Purpose**: Get a high-level summary of all performance data.

**What it shows**:
- Total number of test runs
- Date range
- Average confidence scores per plan
- Best performance per plan
- Quick visualizations (4 charts)

**Key Visualizations**:
1. Average confidence by plan (bar chart)
2. Average cost by plan (bar chart)
3. Cost vs confidence scatter plot
4. Test runs over time (line chart)

**When to use**: 
- After loading new data
- To get a quick overview
- To identify which plans are performing best

### Section 3: Trend Analysis

**Purpose**: Track performance changes over time.

**What it shows**:
- Confidence score trends (line plot with moving averages)
- Cost trends over time
- Cumulative cost tracking
- Processing time trends
- Validation error trends

**Key Insights**:
- Are plans improving or declining?
- Are costs increasing?
- Are there any sudden changes?

**When to use**:
- To track improvements over time
- To identify regressions
- To monitor cost trends

### Section 4: Plan Comparison

**Purpose**: Compare different extraction plans side-by-side.

**What it shows**:
- Latest run comparison (table)
- Best run comparison (table)
- Average performance comparison (table)
- Quality vs cost analysis (scatter plot with Pareto frontier)
- Extraction type breakdown (bar charts and heatmap)

**Key Visualizations**:
- Side-by-side comparison tables
- Quality vs cost scatter plot (identifies most efficient plans)
- Heatmap showing confidence by extraction type

**When to use**:
- To choose the best plan for production
- To understand trade-offs between quality and cost
- To see which plans excel at specific extraction types

### Section 5: Run-by-Run Analysis

**Purpose**: Deep dive into specific test runs.

**What it shows**:
- List of all available runs
- Detailed metrics for selected run
- Per-plan breakdown
- Per-extraction-type breakdown
- Comparison between two runs

**Key Features**:
- Run selector (change `selected_run_idx` to analyze different runs)
- Detailed breakdown by extraction type
- Visual comparison of two runs

**When to use**:
- To investigate a specific test run
- To compare before/after changes
- To understand why a run performed well or poorly

### Section 6: Statistical Analysis

**Purpose**: Advanced statistical insights and pattern detection.

**What it shows**:
- Performance distribution (histograms, box plots)
- Correlation matrix (relationships between metrics)
- Regression detection (identifies performance drops)
- Improvement tracking (vs baseline)
- Automated insights

**Key Insights**:
- Which plans are most consistent?
- Are there correlations between metrics?
- Have there been any regressions?
- What are the key trends?

**When to use**:
- For deep statistical analysis
- To detect regressions
- To understand relationships between metrics
- To generate automated insights

### Section 7: Benchmark Evaluation

**Purpose**: Compare performance against defined targets.

**What it shows**:
- Benchmark compliance table (which plans meet targets)
- Visual compliance indicators
- Progress toward targets (progress bars)
- Current vs target values

**Key Metrics Evaluated**:
- Confidence threshold (≥ 0.8)
- Target confidence (≥ 0.85)
- Validation errors (≤ 0)
- Cost targets (varies by plan)
- Processing time (≤ 60s)

**When to use**:
- To evaluate if plans meet requirements
- To track progress toward goals
- To identify which plans need improvement

### Section 8: Cost Analysis

**Purpose**: Financial tracking and cost optimization.

**What it shows**:
- Cost breakdown by plan (pie chart)
- Cumulative cost over time (stacked area chart)
- Cost efficiency metrics (confidence per dollar)
- Cost efficiency trends

**Key Metrics**:
- Total cost per plan
- Average cost per run
- Cost per confidence point
- Confidence per dollar (efficiency)

**When to use**:
- To monitor spending
- To identify cost optimization opportunities
- To compare cost efficiency between plans

### Section 9: Export and Reporting

**Purpose**: Generate reports and export data for sharing.

**What it does**:
- Generates markdown performance report
- Exports data to CSV files
- Saves charts as PNG images

**Outputs**:
- `performance_report_YYYYMMDD_HHMMSS.md` - Summary report
- `plans_data_YYYYMMDD_HHMMSS.csv` - Plans data
- `types_data_YYYYMMDD_HHMMSS.csv` - Types data
- `runs_data_YYYYMMDD_HHMMSS.csv` - Runs data
- `confidence_trends_YYYYMMDD_HHMMSS.png` - Chart image

**When to use**:
- After completing analysis
- To share results with team
- To archive performance data
- To include in documentation

## Common Use Cases

### Use Case 1: After a Test Run

**Scenario**: You just ran `test_all_extraction_plans` and want to analyze the results.

**Steps**:
1. Open the notebook
2. Run Section 1 (Setup) to load new data
3. Run Section 2 (Dashboard) to see summary
4. Check Section 4 (Comparison) to see which plan performed best
5. Run Section 9 (Export) to save the report

**What to look for**:
- Which plan has highest confidence?
- Are there any validation errors?
- Is cost within budget?
- How does it compare to previous runs?

### Use Case 2: Performance Investigation

**Scenario**: You noticed low confidence scores and want to investigate.

**Steps**:
1. Run Section 3 (Trends) to see if it's a regression
2. Run Section 5 (Run Analysis) to examine the specific run
3. Check Section 6 (Statistics) for regression detection
4. Look at Section 4 (Comparison) to see extraction type breakdown

**What to look for**:
- Is this a sudden drop or gradual decline?
- Which extraction types are failing?
- Are there validation errors?
- What changed between runs?

### Use Case 3: Cost Optimization

**Scenario**: You want to reduce costs while maintaining quality.

**Steps**:
1. Run Section 8 (Cost Analysis) to see cost breakdown
2. Check Section 4 (Comparison) for quality vs cost analysis
3. Look for plans with good confidence/cost ratio
4. Run Section 3 (Trends) to see cost trends

**What to look for**:
- Which plans are most cost-efficient?
- Are costs increasing over time?
- Can you maintain quality with lower-cost plans?
- What's the optimal quality/cost trade-off?

### Use Case 4: Performance Benchmarking

**Scenario**: You want to evaluate if plans meet performance targets.

**Steps**:
1. Run Section 7 (Benchmark Evaluation)
2. Check compliance table
3. Review progress toward targets
4. Identify which plans need improvement

**What to look for**:
- Which plans meet all benchmarks?
- What targets are being missed?
- How close are plans to goals?
- What improvements are needed?

## Troubleshooting

### Issue: "No test runs recorded yet"

**Cause**: No data in `history.json`

**Solution**:
1. Run the test suite to generate data:
   ```bash
   python -m tests.comparison.test_all_extraction_plans --no-cache
   ```
2. Verify `tests/performance/history.json` exists and has data

### Issue: Import Errors

**Cause**: Missing dependencies

**Solution**:
```bash
pip install pandas numpy matplotlib seaborn jupyter
```

### Issue: Empty DataFrames

**Cause**: Data structure mismatch or empty history

**Solution**:
1. Check `history.json` format
2. Verify it contains valid test run data
3. Check that runs have `results` field

### Issue: Charts Not Rendering

**Cause**: Matplotlib backend issue or missing display

**Solution**:
1. Add this to a cell before plotting:
   ```python
   %matplotlib inline
   ```
2. For JupyterLab, use:
   ```python
   %matplotlib widget
   ```

### Issue: Export Fails

**Cause**: Directory doesn't exist or permission issues

**Solution**:
1. Ensure `runtime/outputs/performance_reports/` directory exists
2. Check file permissions
3. Verify disk space

### Issue: Memory Errors with Large Datasets

**Cause**: Too much data loaded at once

**Solution**:
1. Filter data by date range
2. Analyze subsets of runs
3. Increase available memory

## Advanced Usage

### Customizing Analysis

**Filter by Date Range**:
```python
# After loading data, filter plans_df
start_date = pd.to_datetime('2025-01-01')
end_date = pd.to_datetime('2025-01-31')
filtered_plans = plans_df[
    (plans_df['timestamp'] >= start_date) & 
    (plans_df['timestamp'] <= end_date)
]
```

**Filter by Plan**:
```python
# Analyze only specific plans
selected_plans = plans_df[plans_df['plan_name'].isin(['Plan A', 'Plan B'])]
```

**Add Custom Metrics**:
```python
# Calculate custom efficiency metric
plans_df['custom_efficiency'] = (
    plans_df['average_confidence'] / 
    (plans_df['total_cost'] + plans_df['processing_time'] / 100)
)
```

### Modifying Visualizations

**Change Colors**:
```python
# Define custom color scheme
colors = {
    'Plan A': '#1f77b4',
    'Plan B': '#ff7f0e',
    'Plan C': '#2ca02c',
    'Plan D': '#d62728'
}
```

**Adjust Chart Size**:
```python
plt.rcParams['figure.figsize'] = (16, 10)  # Larger charts
```

**Save Custom Charts**:
```python
fig, ax = plt.subplots(figsize=(12, 8))
# ... create chart ...
plt.savefig('custom_chart.png', dpi=300, bbox_inches='tight')
```

### Adding Custom Analysis

**Create New Analysis Cell**:
```python
# Example: Calculate improvement rate
def calculate_improvement_rate(plans_df, plan_name):
    plan_data = plans_df[plans_df['plan_name'] == plan_name].sort_values('timestamp')
    if len(plan_data) < 2:
        return None
    
    first_conf = plan_data.iloc[0]['average_confidence']
    last_conf = plan_data.iloc[-1]['average_confidence']
    days = (plan_data.iloc[-1]['timestamp'] - plan_data.iloc[0]['timestamp']).days
    
    if days > 0:
        return (last_conf - first_conf) / days
    return None

# Use it
for plan in plans_df['plan_name'].unique():
    rate = calculate_improvement_rate(plans_df, plan)
    if rate:
        print(f"{plan}: {rate:.4f} confidence points per day")
```

## API Reference

### Helper Functions (`tests/performance/utils.py`)

#### `load_performance_data(history_file: str) -> Dict[str, pd.DataFrame]`

Loads performance history and converts to DataFrames.

**Parameters**:
- `history_file`: Path to history.json file (default: "tests/performance/history.json")

**Returns**:
- Dictionary with keys: `'runs'`, `'plans'`, `'types'`
- Each value is a pandas DataFrame

**Example**:
```python
from tests.performance.utils import load_performance_data

data = load_performance_data()
runs_df = data['runs']
plans_df = data['plans']
types_df = data['types']
```

#### `detect_regressions(plans_df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame`

Detects performance regressions between consecutive runs.

**Parameters**:
- `plans_df`: Plan-level DataFrame
- `threshold`: Minimum confidence drop to flag as regression (default: 0.05)

**Returns**:
- DataFrame with regressions identified

**Example**:
```python
regressions = detect_regressions(plans_df, threshold=0.05)
if not regressions.empty:
    print("Regressions detected:")
    print(regressions)
```

#### `calculate_improvements(plans_df: pd.DataFrame, baseline_plan: str = "Baseline") -> pd.DataFrame`

Calculates improvements compared to baseline.

**Parameters**:
- `plans_df`: Plan-level DataFrame
- `baseline_plan`: Name of baseline plan (default: "Baseline")

**Returns**:
- DataFrame with improvement metrics

**Example**:
```python
improvements = calculate_improvements(plans_df, baseline_plan="Baseline")
print(improvements.groupby('plan_name')['confidence_improvement'].mean())
```

#### `generate_insights(plans_df: pd.DataFrame, types_df: pd.DataFrame) -> Dict[str, Any]`

Generates automated insights from performance data.

**Parameters**:
- `plans_df`: Plan-level DataFrame
- `types_df`: Extraction-type-level DataFrame

**Returns**:
- Dictionary with insights (best_plan, worst_plan, trends, etc.)

**Example**:
```python
insights = generate_insights(plans_df, types_df)
print(f"Best plan: {insights['best_plan']}")
print(f"Most cost-efficient: {insights['most_cost_efficient']}")
```

### PerformanceTracker (`tests/performance/tracker.py`)

#### `PerformanceTracker(history_file: str = "tests/performance/history.json")`

Main class for tracking performance.

**Methods**:
- `record_run(results, test_name, notes)`: Record a test run
- `get_best_performance(plan_name)`: Get best performance for a plan
- `compare_runs(run_id_1, run_id_2)`: Compare two runs
- `get_trends(plan_name, metric)`: Get trend data
- `generate_report()`: Generate text report

**Example**:
```python
from tests.performance.tracker import PerformanceTracker

tracker = PerformanceTracker()
best = tracker.get_best_performance("Plan A")
print(f"Best confidence: {best['results']['Plan A']['average_confidence']}")
```

### Benchmarks (`tests/performance/benchmarks.py`)

#### `evaluate_performance(plan_result: Dict, plan_name: str) -> Dict`

Evaluates plan performance against benchmarks.

**Parameters**:
- `plan_result`: Result dictionary from test run
- `plan_name`: Name of the plan

**Returns**:
- Dictionary with evaluation results

**Example**:
```python
from tests.performance.benchmarks import evaluate_performance

evaluation = evaluate_performance(plan_result, "Plan A")
if evaluation['overall_passing']:
    print("Plan A meets all benchmarks!")
```

## Best Practices

1. **Always run Section 1 first** to load fresh data
2. **Use `--no-cache` flag** when running tests for accurate metrics
3. **Record notes** in test runs to track what changed
4. **Export reports regularly** to maintain history
5. **Compare to baseline** to ensure improvements don't regress
6. **Monitor costs** to avoid unexpected API spending
7. **Check trends** to catch gradual regressions early

## FAQ

**Q: How often should I run the analysis?**
A: After each test run, or at least weekly to track trends.

**Q: Can I analyze specific date ranges?**
A: Yes, filter the DataFrames by timestamp after loading.

**Q: How do I add new extraction types?**
A: The notebook automatically handles new types from the data.

**Q: Can I compare more than 2 runs?**
A: Yes, use the comparison functions with different run IDs.

**Q: How do I share results?**
A: Use Section 9 to export reports, CSV files, and chart images.

**Q: What if I have 100+ runs?**
A: The notebook handles large datasets, but may be slower. Consider filtering by date range.

## Additional Resources

- [Performance Tracking Documentation](PERFORMANCE_TRACKING.md)
- [Refactoring Plan](REFACTORING_PLAN.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review the API Reference
3. Check existing test runs in `history.json`
4. Review the code in `tests/performance/utils.py`




