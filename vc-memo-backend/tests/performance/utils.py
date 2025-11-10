"""
Helper functions for performance analysis notebook.
Provides data transformation and visualization utilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import matplotlib.pyplot as plt
import seaborn as sns
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None


def load_performance_data(history_file: str = "tests/performance/history.json") -> Dict[str, pd.DataFrame]:
    """
    Load performance history and convert to DataFrames
    
    Returns:
        Dictionary with keys:
        - 'runs': Run-level DataFrame
        - 'plans': Plan-level DataFrame  
        - 'types': Extraction-type-level DataFrame
    """
    history_path = Path(history_file)
    
    if not history_path.exists():
        return {
            'runs': pd.DataFrame(),
            'plans': pd.DataFrame(),
            'types': pd.DataFrame()
        }
    
    with open(history_path, 'r') as f:
        history = json.load(f)
    
    if not history:
        return {
            'runs': pd.DataFrame(),
            'plans': pd.DataFrame(),
            'types': pd.DataFrame()
        }
    
    # Prepare run-level data
    runs_data = []
    plans_data = []
    types_data = []
    
    for run in history:
        run_id = run['run_id']
        timestamp = pd.to_datetime(run['timestamp'])
        notes = run.get('notes', '')
        
        # Run-level row
        runs_data.append({
            'run_id': run_id,
            'timestamp': timestamp,
            'notes': notes,
            'test_name': run.get('test_name', 'extraction_comparison')
        })
        
        # Plan-level rows
        for plan_name, plan_result in run.get('results', {}).items():
            plans_data.append({
                'run_id': run_id,
                'timestamp': timestamp,
                'notes': notes,
                'plan_name': plan_name,
                'average_confidence': plan_result.get('average_confidence', 0.0),
                'validation_errors': plan_result.get('validation_errors', 0),
                'total_cost': plan_result.get('total_cost', 0.0),
                'processing_time': plan_result.get('processing_time', 0.0),
                'total_tokens': plan_result.get('total_tokens', 0),
                'input_tokens': plan_result.get('input_tokens', 0),
                'output_tokens': plan_result.get('output_tokens', 0),
                'cache_hits': plan_result.get('cache_hits', 0),
            })
            
            # Extraction-type-level rows
            confidence_by_type = plan_result.get('confidence_by_type', {})
            for extract_type, confidence in confidence_by_type.items():
                types_data.append({
                    'run_id': run_id,
                    'timestamp': timestamp,
                    'plan_name': plan_name,
                    'extract_type': extract_type,
                    'confidence': confidence
                })
    
    runs_df = pd.DataFrame(runs_data)
    plans_df = pd.DataFrame(plans_data)
    types_df = pd.DataFrame(types_data)
    
    # Add computed columns
    if not runs_df.empty:
        runs_df['date'] = runs_df['timestamp'].dt.date
        runs_df['days_since_first'] = (runs_df['timestamp'] - runs_df['timestamp'].min()).dt.days
    
    if not plans_df.empty:
        plans_df['date'] = plans_df['timestamp'].dt.date
        plans_df['cost_per_confidence'] = plans_df.apply(
            lambda x: x['total_cost'] / x['average_confidence'] if x['average_confidence'] > 0 else np.inf,
            axis=1
        )
    
    return {
        'runs': runs_df,
        'plans': plans_df,
        'types': types_df
    }


def prepare_run_dataframe(history: List[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare run-level DataFrame (one row per run)"""
    data = load_performance_data()
    return data['runs']


def prepare_plan_dataframe(history: List[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare plan-level DataFrame (one row per run-plan combination)"""
    data = load_performance_data()
    return data['plans']


def prepare_type_dataframe(history: List[Dict[str, Any]]) -> pd.DataFrame:
    """Prepare extraction-type-level DataFrame (one row per run-plan-type)"""
    data = load_performance_data()
    return data['types']


def detect_regressions(plans_df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """
    Detect performance regressions between consecutive runs
    
    Args:
        plans_df: Plan-level DataFrame
        threshold: Minimum confidence drop to flag as regression
    
    Returns:
        DataFrame with regressions identified
    """
    if plans_df.empty:
        return pd.DataFrame()
    
    regressions = []
    
    for plan_name in plans_df['plan_name'].unique():
        plan_data = plans_df[plans_df['plan_name'] == plan_name].sort_values('timestamp')
        
        for i in range(1, len(plan_data)):
            prev = plan_data.iloc[i-1]
            curr = plan_data.iloc[i]
            
            confidence_drop = prev['average_confidence'] - curr['average_confidence']
            
            if confidence_drop >= threshold:
                regressions.append({
                    'plan_name': plan_name,
                    'run_id': curr['run_id'],
                    'timestamp': curr['timestamp'],
                    'previous_confidence': prev['average_confidence'],
                    'current_confidence': curr['average_confidence'],
                    'confidence_drop': confidence_drop,
                    'notes': curr.get('notes', '')
                })
    
    return pd.DataFrame(regressions)


def calculate_improvements(plans_df: pd.DataFrame, baseline_plan: str = "Baseline") -> pd.DataFrame:
    """
    Calculate improvements compared to baseline
    
    Args:
        plans_df: Plan-level DataFrame
        baseline_plan: Name of baseline plan for comparison
    
    Returns:
        DataFrame with improvement metrics
    """
    if plans_df.empty:
        return pd.DataFrame()
    
    improvements = []
    
    for run_id in plans_df['run_id'].unique():
        run_data = plans_df[plans_df['run_id'] == run_id]
        baseline = run_data[run_data['plan_name'] == baseline_plan]
        
        if baseline.empty:
            continue
        
        baseline_conf = baseline.iloc[0]['average_confidence']
        baseline_cost = baseline.iloc[0]['total_cost']
        
        for _, plan_row in run_data.iterrows():
            if plan_row['plan_name'] == baseline_plan:
                continue
            
            improvements.append({
                'run_id': run_id,
                'timestamp': plan_row['timestamp'],
                'plan_name': plan_row['plan_name'],
                'confidence_improvement': plan_row['average_confidence'] - baseline_conf,
                'confidence_improvement_pct': (
                    (plan_row['average_confidence'] - baseline_conf) / baseline_conf * 100
                    if baseline_conf > 0 else 0
                ),
                'cost_difference': plan_row['total_cost'] - baseline_cost,
                'cost_difference_pct': (
                    (plan_row['total_cost'] - baseline_cost) / baseline_cost * 100
                    if baseline_cost > 0 else 0
                )
            })
    
    return pd.DataFrame(improvements)


def generate_insights(plans_df: pd.DataFrame, types_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate automated insights from performance data
    
    Returns:
        Dictionary with insights
    """
    if plans_df.empty:
        return {
            'best_plan': None,
            'worst_plan': None,
            'most_cost_efficient': None,
            'fastest_plan': None,
            'most_consistent': None,
            'trends': []
        }
    
    insights = {}
    
    # Best overall plan (highest average confidence)
    avg_by_plan = plans_df.groupby('plan_name')['average_confidence'].mean()
    insights['best_plan'] = avg_by_plan.idxmax() if not avg_by_plan.empty else None
    insights['worst_plan'] = avg_by_plan.idxmin() if not avg_by_plan.empty else None
    
    # Most cost-efficient (best confidence/cost ratio)
    plans_df['efficiency'] = plans_df['average_confidence'] / (plans_df['total_cost'] + 0.0001)
    avg_efficiency = plans_df.groupby('plan_name')['efficiency'].mean()
    insights['most_cost_efficient'] = avg_efficiency.idxmax() if not avg_efficiency.empty else None
    
    # Fastest plan
    avg_time = plans_df.groupby('plan_name')['processing_time'].mean()
    insights['fastest_plan'] = avg_time.idxmin() if not avg_time.empty else None
    
    # Most consistent (lowest std dev in confidence)
    std_conf = plans_df.groupby('plan_name')['average_confidence'].std()
    insights['most_consistent'] = std_conf.idxmin() if not std_conf.empty else None
    
    # Trends
    insights['trends'] = []
    for plan_name in plans_df['plan_name'].unique():
        plan_data = plans_df[plans_df['plan_name'] == plan_name].sort_values('timestamp')
        if len(plan_data) >= 2:
            first_conf = plan_data.iloc[0]['average_confidence']
            last_conf = plan_data.iloc[-1]['average_confidence']
            change = last_conf - first_conf
            insights['trends'].append({
                'plan': plan_name,
                'change': change,
                'trend': 'improving' if change > 0.01 else ('declining' if change < -0.01 else 'stable')
            })
    
    return insights


def plot_confidence_trends(
    plans_df: pd.DataFrame,
    ax: Optional[plt.Axes] = None,
    show_moving_avg: bool = True,
    window: int = 2
) -> plt.Axes:
    """
    Plot confidence score trends over time for all plans
    
    Args:
        plans_df: Plan-level DataFrame
        ax: Matplotlib axes (creates new if None)
        show_moving_avg: Whether to show moving average
        window: Moving average window size
    
    Returns:
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 8))
    
    for plan_name in sorted(plans_df['plan_name'].unique()):
        plan_data = plans_df[plans_df['plan_name'] == plan_name].sort_values('timestamp')
        
        if not plan_data.empty:
            ax.plot(plan_data['timestamp'], plan_data['average_confidence'], 
                   marker='o', label=plan_name, linewidth=2, markersize=6, alpha=0.7)
            
            if show_moving_avg and len(plan_data) >= window:
                plan_data = plan_data.copy()
                plan_data['ma'] = plan_data['average_confidence'].rolling(window=window, center=True).mean()
                ax.plot(plan_data['timestamp'], plan_data['ma'], 
                       linestyle='--', alpha=0.5, linewidth=1)
    
    ax.axhline(y=0.8, color='r', linestyle='--', linewidth=2, label='Target (0.8)', alpha=0.7)
    ax.set_title('Confidence Score Trends Over Time', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Timestamp', fontsize=12)
    ax.set_ylabel('Average Confidence', fontsize=12)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    return ax


def plot_cost_vs_confidence(
    plans_df: pd.DataFrame,
    ax: Optional[plt.Axes] = None,
    highlight_efficient: bool = True,
    top_n: int = 5
) -> plt.Axes:
    """
    Plot cost vs confidence scatter with Pareto frontier
    
    Args:
        plans_df: Plan-level DataFrame
        ax: Matplotlib axes (creates new if None)
        highlight_efficient: Whether to highlight most efficient points
        top_n: Number of efficient points to highlight
    
    Returns:
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    
    # Color map for plans
    plan_colors = {plan: plt.cm.tab10(i) for i, plan in enumerate(sorted(plans_df['plan_name'].unique()))}
    
    # Scatter plot
    for plan_name in sorted(plans_df['plan_name'].unique()):
        plan_data = plans_df[plans_df['plan_name'] == plan_name]
        ax.scatter(plan_data['total_cost'], plan_data['average_confidence'], 
                  label=plan_name, alpha=0.6, s=100, color=plan_colors[plan_name])
    
    # Target lines
    ax.axhline(y=0.8, color='r', linestyle='--', linewidth=2, label='Confidence Target (0.8)', alpha=0.7)
    ax.axvline(x=0.10, color='orange', linestyle='--', linewidth=2, label='Cost Target ($0.10)', alpha=0.7)
    
    # Highlight Pareto frontier
    if highlight_efficient:
        plans_df = plans_df.copy()
        plans_df['efficiency'] = plans_df['average_confidence'] / (plans_df['total_cost'] + 0.0001)
        top_efficient = plans_df.nlargest(top_n, 'efficiency')
        ax.scatter(top_efficient['total_cost'], top_efficient['average_confidence'], 
                  s=200, marker='*', color='gold', edgecolors='black', linewidth=2, 
                  label=f'Top {top_n} Efficient', zorder=5)
    
    ax.set_title('Quality vs Cost Analysis', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Total Cost ($)', fontsize=12)
    ax.set_ylabel('Average Confidence', fontsize=12)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_heatmap(
    types_df: pd.DataFrame,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    Plot heatmap of confidence scores (plans × extraction types)
    
    Args:
        types_df: Extraction-type-level DataFrame
        ax: Matplotlib axes (creates new if None)
    
    Returns:
        Matplotlib axes
    """
    if types_df.empty:
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        return ax
    
    pivot_data = types_df.pivot_table(
        values='confidence', 
        index='plan_name', 
        columns='extract_type', 
        aggfunc='mean'
    )
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='YlOrRd', 
                vmin=0, vmax=1, ax=ax, cbar_kws={'label': 'Confidence Score'})
    ax.set_title('Confidence Heatmap (Plans × Extraction Types)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Extraction Type')
    ax.set_ylabel('Plan')
    
    return ax


def perform_statistical_tests(plans_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform statistical tests on plan performance
    
    Args:
        plans_df: Plan-level DataFrame
    
    Returns:
        Dictionary with test results
    """
    results = {}
    
    if not SCIPY_AVAILABLE:
        return {"error": "scipy not available for statistical tests"}
    
    if plans_df.empty or len(plans_df['plan_name'].unique()) < 2:
        return {"error": "Need at least 2 plans for statistical tests"}
    
    # T-test between each pair of plans
    plan_names = sorted(plans_df['plan_name'].unique())
    t_tests = {}
    
    for i, plan1 in enumerate(plan_names):
        for plan2 in plan_names[i+1:]:
            data1 = plans_df[plans_df['plan_name'] == plan1]['average_confidence'].values
            data2 = plans_df[plans_df['plan_name'] == plan2]['average_confidence'].values
            
            if len(data1) > 1 and len(data2) > 1:
                t_stat, p_value = stats.ttest_ind(data1, data2)
                t_tests[f"{plan1} vs {plan2}"] = {
                    "t_statistic": float(t_stat),
                    "p_value": float(p_value),
                    "significant": p_value < 0.05
                }
    
    results['t_tests'] = t_tests
    
    # ANOVA if more than 2 plans
    if len(plan_names) > 2:
        groups = [plans_df[plans_df['plan_name'] == plan]['average_confidence'].values 
                 for plan in plan_names]
        groups = [g for g in groups if len(g) > 0]  # Filter empty groups
        
        if len(groups) > 2:
            f_stat, p_value = stats.f_oneway(*groups)
            results['anova'] = {
                "f_statistic": float(f_stat),
                "p_value": float(p_value),
                "significant": p_value < 0.05
            }
    
    # Correlation tests
    numeric_cols = ['average_confidence', 'total_cost', 'processing_time']
    available_cols = [col for col in numeric_cols if col in plans_df.columns]
    
    if len(available_cols) >= 2:
        correlations = {}
        for i, col1 in enumerate(available_cols):
            for col2 in available_cols[i+1:]:
                if len(plans_df[col1].dropna()) > 2 and len(plans_df[col2].dropna()) > 2:
                    corr, p_value = stats.pearsonr(
                        plans_df[col1].dropna(), 
                        plans_df[col2].dropna()
                    )
                    correlations[f"{col1} vs {col2}"] = {
                        "correlation": float(corr),
                        "p_value": float(p_value),
                        "significant": p_value < 0.05
                    }
        results['correlations'] = correlations
    
    return results


def predict_trends(plans_df: pd.DataFrame, plan_name: str, days_ahead: int = 7) -> Dict[str, Any]:
    """
    Simple linear regression to predict future confidence scores
    
    Args:
        plans_df: Plan-level DataFrame
        plan_name: Name of plan to predict
        days_ahead: Number of days to predict ahead
    
    Returns:
        Dictionary with predictions
    """
    plan_data = plans_df[plans_df['plan_name'] == plan_name].sort_values('timestamp')
    
    if len(plan_data) < 2:
        return {"error": "Need at least 2 data points for prediction"}
    
    # Convert timestamps to numeric (days since first)
    plan_data = plan_data.copy()
    plan_data['days'] = (plan_data['timestamp'] - plan_data['timestamp'].min()).dt.days
    
    # Simple linear regression
    x = plan_data['days'].values
    y = plan_data['average_confidence'].values
    
    # Calculate slope and intercept
    n = len(x)
    slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
    intercept = np.mean(y) - slope * np.mean(x)
    
    # Predict future
    last_day = plan_data['days'].max()
    future_day = last_day + days_ahead
    predicted_confidence = intercept + slope * future_day
    
    # Calculate R²
    y_pred = intercept + slope * x
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        "plan_name": plan_name,
        "current_confidence": float(plan_data['average_confidence'].iloc[-1]),
        "predicted_confidence": float(predicted_confidence),
        "days_ahead": days_ahead,
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "trend": "improving" if slope > 0 else "declining" if slope < 0 else "stable"
    }

