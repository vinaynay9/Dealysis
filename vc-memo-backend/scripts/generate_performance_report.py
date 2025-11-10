"""
Automated script to generate performance reports from the analysis notebook.
Can be run from command line or scheduled (cron, etc.)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.performance.tracker import PerformanceTracker
from tests.performance.utils import (
    load_performance_data,
    generate_insights
)
from tests.performance.benchmarks import evaluate_performance


def generate_report(
    output_dir: str = "runtime/outputs/performance_reports",
    format: str = "markdown"
) -> str:
    """
    Generate performance report
    
    Args:
        output_dir: Directory to save report
        format: Report format ('markdown', 'json', or 'both')
    
    Returns:
        Path to generated report
    """
    # Load data
    data = load_performance_data()
    runs_df = data['runs']
    plans_df = data['plans']
    types_df = data['types']
    
    if plans_df.empty:
        print("⚠️  No performance data available. Run tests first.")
        return None
    
    # Generate markdown report
    if format in ['markdown', 'both']:
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_path / f"performance_report_{timestamp}.md"
        
        lines = []
        lines.append("# Performance Analysis Report")
        lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Summary
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append(f"- **Total Runs:** {len(runs_df)}")
        if not runs_df.empty:
            lines.append(f"- **Date Range:** {runs_df['timestamp'].min().date()} to {runs_df['timestamp'].max().date()}")
        lines.append(f"- **Plans Tested:** {plans_df['plan_name'].nunique()}")
        lines.append(f"- **Total Cost:** ${plans_df['total_cost'].sum():.4f}")
        lines.append("")
        
        # Best performance
        lines.append("## Best Performance by Plan")
        lines.append("")
        best_per_plan = plans_df.loc[plans_df.groupby('plan_name')['average_confidence'].idxmax()]
        for _, row in best_per_plan.iterrows():
            lines.append(f"- **{row['plan_name']}**: Confidence {row['average_confidence']:.2f}, "
                        f"Cost ${row['total_cost']:.4f}, Run {row['run_id']}")
        lines.append("")
        
        # Insights
        insights = generate_insights(plans_df, types_df)
        lines.append("## Key Insights")
        lines.append("")
        lines.append(f"- **Best Overall Plan:** {insights.get('best_plan', 'N/A')}")
        lines.append(f"- **Most Cost-Efficient:** {insights.get('most_cost_efficient', 'N/A')}")
        lines.append(f"- **Fastest Plan:** {insights.get('fastest_plan', 'N/A')}")
        lines.append("")
        
        # Trends
        if insights.get('trends'):
            lines.append("## Performance Trends")
            lines.append("")
            for trend in insights['trends']:
                lines.append(f"- **{trend['plan']}**: {trend['trend'].upper()} (change: {trend['change']:+.3f})")
            lines.append("")
        
        report_file.write_text("\n".join(lines), encoding="utf-8")
        report_path = str(report_file)
        print(f"✅ Markdown report generated: {report_path}")
    
    # Generate JSON report
    if format in ['json', 'both']:
        json_report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_runs": len(runs_df),
                "date_range": {
                    "start": runs_df['timestamp'].min().isoformat() if not runs_df.empty else None,
                    "end": runs_df['timestamp'].max().isoformat() if not runs_df.empty else None
                },
                "plans_tested": plans_df['plan_name'].nunique(),
                "total_cost": float(plans_df['total_cost'].sum()),
                "average_confidence": float(plans_df['average_confidence'].mean())
            },
            "best_performance": {},
            "insights": generate_insights(plans_df, types_df),
            "latest_run": {}
        }
        
        # Best performance per plan
        best_per_plan = plans_df.loc[plans_df.groupby('plan_name')['average_confidence'].idxmax()]
        for _, row in best_per_plan.iterrows():
            json_report["best_performance"][row['plan_name']] = {
                "confidence": float(row['average_confidence']),
                "cost": float(row['total_cost']),
                "run_id": row['run_id']
            }
        
        # Latest run
        if not runs_df.empty:
            latest_run_id = runs_df.iloc[-1]['run_id']
            latest_plans = plans_df[plans_df['run_id'] == latest_run_id]
            json_report["latest_run"] = {
                "run_id": latest_run_id,
                "timestamp": latest_plans['timestamp'].iloc[0].isoformat() if not latest_plans.empty else None,
                "plans": {}
            }
            for _, row in latest_plans.iterrows():
                json_report["latest_run"]["plans"][row['plan_name']] = {
                    "confidence": float(row['average_confidence']),
                    "cost": float(row['total_cost']),
                    "processing_time": float(row['processing_time']),
                    "validation_errors": int(row['validation_errors'])
                }
        
        # Save JSON report
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = output_path / f"performance_report_{timestamp}.json"
        
        with open(json_file, 'w') as f:
            json.dump(json_report, f, indent=2, default=str)
        
        print(f"✅ JSON report generated: {json_file}")
    
    return report_path if format in ['markdown', 'both'] else str(json_file)


def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate performance analysis report")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="runtime/outputs/performance_reports",
        help="Output directory for reports"
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=['markdown', 'json', 'both'],
        default='both',
        help="Report format"
    )
    
    args = parser.parse_args()
    
    report_path = generate_report(args.output_dir, args.format)
    
    if report_path:
        print(f"\n📄 Report(s) generated successfully!")
        print(f"   Location: {args.output_dir}")
    else:
        print("\n❌ Failed to generate report")
        sys.exit(1)


if __name__ == "__main__":
    main()

