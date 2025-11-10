"""
Configuration for performance analysis notebook.
Centralized settings for colors, thresholds, and chart styles.
"""

from typing import Dict, List

# Color scheme for plans
PLAN_COLORS: Dict[str, str] = {
    "Baseline": "#808080",  # Gray
    "Plan A": "#1f77b4",    # Blue
    "Plan B": "#ff7f0e",    # Orange
    "Plan C": "#2ca02c",    # Green
    "Plan D": "#d62728",    # Red
}

# Chart style configuration
CHART_CONFIG = {
    "figure_size": (12, 6),
    "figure_size_large": (16, 10),
    "dpi": 100,
    "font_size": 10,
    "style": "whitegrid",
    "palette": "Set2",
}

# Thresholds for analysis
ANALYSIS_THRESHOLDS = {
    "regression_threshold": 0.05,  # Minimum confidence drop to flag as regression
    "significant_correlation": 0.3,  # Minimum correlation to highlight
    "improvement_threshold": 0.01,  # Minimum change to consider significant
}

# Extraction types in order
EXTRACTION_TYPES: List[str] = [
    "progress",
    "financial",
    "market",
    "company",
    "team",
]

# Chart export settings
EXPORT_CONFIG = {
    "output_dir": "runtime/outputs/performance_reports",
    "dpi": 300,
    "format": "png",
    "bbox_inches": "tight",
}

# Date format for display
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Number formatting
NUMBER_FORMATS = {
    "confidence": "{:.2f}",
    "cost": "${:.4f}",
    "time": "{:.2f}s",
    "percentage": "{:.1f}%",
}




