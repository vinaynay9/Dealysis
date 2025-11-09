import pandas as pd
import io
from typing import Dict, Any, List, Optional
import re
from datetime import datetime


class FinancialAnalyzer:
    """Perform VC-style financial analysis on Excel/CSV files"""

    def __init__(self):
        self.common_metrics = {
            "revenue": ["revenue", "sales", "income", "arr", "mrr", "top line"],
            "costs": ["cost", "expense", "burn", "cogs", "opex"],
            "customers": ["customers", "users", "accounts", "subscribers"],
            "cac": ["cac", "customer acquisition cost", "acquisition cost"],
            "ltv": ["ltv", "lifetime value", "lifetime revenue"],
            "churn": ["churn", "churn rate", "attrition"],
            "runway": ["runway", "months of cash", "cash runway"],
            "cash": ["cash", "cash balance", "bank balance", "liquidity"],
        }

    async def analyze_financial_file(
        self, content: bytes, filename: str, file_type: str
    ) -> Dict[str, Any]:
        """Analyze a financial Excel/CSV file and extract VC-relevant metrics"""

        try:
            # Parse the file
            if file_type in ["xlsx", "xls"]:
                df_dict = pd.read_excel(
                    io.BytesIO(content), sheet_name=None, engine="openpyxl"
                )
            elif file_type == "csv":
                df_dict = {"main": pd.read_csv(io.BytesIO(content))}
            else:
                return {"error": f"Unsupported file type: {file_type}"}

            analysis_results = {
                "filename": filename,
                "file_type": file_type,
                "sheets_analyzed": [],
                "metrics": {},
                "trends": {},
                "insights": [],
                "red_flags": [],
            }

            # Analyze each sheet
            for sheet_name, df in df_dict.items():
                if df.empty:
                    continue

                sheet_analysis = self._analyze_sheet(df, sheet_name)
                analysis_results["sheets_analyzed"].append(sheet_name)
                analysis_results["metrics"].update(sheet_analysis["metrics"])
                analysis_results["trends"].update(sheet_analysis["trends"])
                analysis_results["insights"].extend(sheet_analysis["insights"])
                analysis_results["red_flags"].extend(sheet_analysis["red_flags"])

            # Generate summary analysis
            analysis_results["summary"] = self._generate_summary(analysis_results)

            return analysis_results

        except Exception as e:
            return {"error": f"Error analyzing file {filename}: {str(e)}"}

    def _analyze_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Analyze a single sheet/DataFrame for financial metrics"""

        metrics = {}
        trends = {}
        insights = []
        red_flags = []

        # Normalize column names (lowercase, remove special chars)
        df.columns = df.columns.str.lower().str.strip()
        df.columns = [re.sub(r"[^a-z0-9\s]", "", col) for col in df.columns]

        # Detect time-based columns (for trend analysis)
        time_cols = self._detect_time_columns(df)
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        # Extract metrics by pattern matching
        for metric_type, patterns in self.common_metrics.items():
            for col in df.columns:
                if any(pattern in col for pattern in patterns):
                    values = df[col].dropna()
                    if len(values) > 0:
                        metrics[f"{metric_type}_{col}"] = {
                            "values": values.tolist(),
                            "latest": (
                                float(values.iloc[-1])
                                if pd.api.types.is_numeric_dtype(values)
                                else str(values.iloc[-1])
                            ),
                            "mean": (
                                float(values.mean())
                                if pd.api.types.is_numeric_dtype(values)
                                else None
                            ),
                            "min": (
                                float(values.min())
                                if pd.api.types.is_numeric_dtype(values)
                                else None
                            ),
                            "max": (
                                float(values.max())
                                if pd.api.types.is_numeric_dtype(values)
                                else None
                            ),
                        }

        # Trend analysis for time series data
        if time_cols and numeric_cols:
            for time_col in time_cols[:1]:  # Use first time column
                for num_col in numeric_cols[:5]:  # Analyze top 5 numeric columns
                    trend = self._calculate_trend(df, time_col, num_col)
                    if trend:
                        trends[f"{num_col}_trend"] = trend

        # Detect P&L structure
        pl_metrics = self._detect_pl_structure(df)
        if pl_metrics:
            metrics.update(pl_metrics)
            insights.append(f"Detected P&L structure in sheet '{sheet_name}'")

        # Detect balance sheet structure
        bs_metrics = self._detect_balance_sheet_structure(df)
        if bs_metrics:
            metrics.update(bs_metrics)
            insights.append(f"Detected balance sheet structure in sheet '{sheet_name}'")

        # Calculate derived VC metrics
        derived_metrics = self._calculate_vc_metrics(df, metrics)
        metrics.update(derived_metrics)

        # Identify red flags
        red_flags.extend(self._identify_red_flags(df, metrics))

        return {
            "metrics": metrics,
            "trends": trends,
            "insights": insights,
            "red_flags": red_flags,
        }

    def _detect_time_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect columns that represent time periods"""
        time_cols = []
        for col in df.columns:
            # Check if column name suggests time
            if any(
                keyword in col
                for keyword in ["date", "month", "year", "quarter", "period", "time"]
            ):
                time_cols.append(col)
            # Check if column contains date-like values
            elif df[col].dtype == "object":
                try:
                    # Suppress the format inference warning - we're just testing if it's a date
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        pd.to_datetime(df[col].head(5), errors="raise", format="mixed")
                    time_cols.append(col)
                except:
                    pass
        return time_cols

    def _calculate_trend(
        self, df: pd.DataFrame, time_col: str, value_col: str
    ) -> Optional[Dict[str, Any]]:
        """Calculate trend for a time series"""
        try:
            # Sort by time
            df_sorted = df.sort_values(time_col).copy()
            values = df_sorted[value_col].dropna()

            if len(values) < 2:
                return None

            # Calculate growth rates
            growth_rates = values.pct_change().dropna() * 100
            avg_growth = float(growth_rates.mean())
            latest_growth = (
                float(growth_rates.iloc[-1]) if len(growth_rates) > 0 else None
            )

            # Determine trend direction
            if avg_growth > 5:
                direction = "strongly_increasing"
            elif avg_growth > 0:
                direction = "increasing"
            elif avg_growth < -5:
                direction = "strongly_decreasing"
            elif avg_growth < 0:
                direction = "decreasing"
            else:
                direction = "stable"

            return {
                "direction": direction,
                "average_growth_rate": round(avg_growth, 2),
                "latest_growth_rate": (
                    round(latest_growth, 2) if latest_growth else None
                ),
                "data_points": len(values),
                "latest_value": float(values.iloc[-1]),
                "first_value": float(values.iloc[0]),
            }
        except Exception as e:
            return None

    def _detect_pl_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect Profit & Loss statement structure"""
        pl_keywords = {
            "revenue": ["revenue", "sales", "income", "top line"],
            "cogs": ["cogs", "cost of goods", "cost of sales"],
            "gross_profit": ["gross profit", "gross margin"],
            "operating_expenses": [
                "operating expenses",
                "opex",
                "sg&a",
                "sales and marketing",
            ],
            "ebitda": ["ebitda", "operating income", "operating profit"],
            "net_income": ["net income", "net profit", "bottom line"],
        }

        pl_metrics = {}
        for metric_name, keywords in pl_keywords.items():
            for col in df.columns:
                if any(keyword in col for keyword in keywords):
                    values = df[col].dropna()
                    if len(values) > 0 and pd.api.types.is_numeric_dtype(values):
                        pl_metrics[metric_name] = {
                            "column": col,
                            "latest": float(values.iloc[-1]),
                            "average": float(values.mean()),
                        }
                        break

        return pl_metrics

    def _detect_balance_sheet_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect Balance Sheet structure"""
        bs_keywords = {
            "cash": ["cash", "cash and equivalents", "bank"],
            "total_assets": ["total assets", "assets"],
            "total_liabilities": ["total liabilities", "liabilities"],
            "equity": ["equity", "shareholders equity", "net worth"],
        }

        bs_metrics = {}
        for metric_name, keywords in bs_keywords.items():
            for col in df.columns:
                if any(keyword in col for keyword in keywords):
                    values = df[col].dropna()
                    if len(values) > 0 and pd.api.types.is_numeric_dtype(values):
                        bs_metrics[metric_name] = {
                            "column": col,
                            "latest": float(values.iloc[-1]),
                        }
                        break

        return bs_metrics

    def _calculate_vc_metrics(
        self, df: pd.DataFrame, extracted_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate VC-specific metrics from extracted data"""

        vc_metrics = {}

        # Calculate ARR from MRR if available
        mrr_values = [
            v["latest"]
            for k, v in extracted_metrics.items()
            if "mrr" in k.lower() and isinstance(v.get("latest"), (int, float))
        ]
        if mrr_values:
            arr = mrr_values[0] * 12
            vc_metrics["calculated_arr"] = {
                "value": arr,
                "source": "mrr * 12",
                "note": "Annualized from MRR",
            }

        # Calculate growth rates
        revenue_values = [
            v["values"]
            for k, v in extracted_metrics.items()
            if "revenue" in k.lower() and isinstance(v.get("values"), list)
        ]
        if revenue_values and len(revenue_values[0]) >= 2:
            rev_series = revenue_values[0]
            try:
                rev_series_numeric = [
                    float(x) for x in rev_series if isinstance(x, (int, float))
                ]
                if len(rev_series_numeric) >= 2:
                    mom_growth = (
                        (rev_series_numeric[-1] - rev_series_numeric[-2])
                        / rev_series_numeric[-2]
                    ) * 100
                    if len(rev_series_numeric) >= 13:
                        yoy_growth = (
                            (rev_series_numeric[-1] - rev_series_numeric[-13])
                            / rev_series_numeric[-13]
                        ) * 100
                        vc_metrics["yoy_growth_rate"] = round(yoy_growth, 2)
                    vc_metrics["mom_growth_rate"] = round(mom_growth, 2)
            except:
                pass

        # Calculate burn rate if cash and expenses available
        cash_values = [
            v["latest"]
            for k, v in extracted_metrics.items()
            if "cash" in k.lower() and isinstance(v.get("latest"), (int, float))
        ]
        expense_values = [
            v["latest"]
            for k, v in extracted_metrics.items()
            if any(term in k.lower() for term in ["expense", "burn", "cost"])
            and isinstance(v.get("latest"), (int, float))
        ]

        if cash_values and expense_values:
            monthly_burn = (
                abs(expense_values[0]) if expense_values[0] < 0 else expense_values[0]
            )
            cash_balance = cash_values[0]
            if monthly_burn > 0:
                runway_months = cash_balance / monthly_burn
                vc_metrics["calculated_runway_months"] = {
                    "value": round(runway_months, 1),
                    "cash_balance": cash_balance,
                    "monthly_burn": monthly_burn,
                }

        # Calculate unit economics if CAC and LTV available
        cac_values = [
            v["latest"]
            for k, v in extracted_metrics.items()
            if "cac" in k.lower() and isinstance(v.get("latest"), (int, float))
        ]
        ltv_values = [
            v["latest"]
            for k, v in extracted_metrics.items()
            if "ltv" in k.lower() and isinstance(v.get("latest"), (int, float))
        ]

        if cac_values and ltv_values:
            ltv_cac_ratio = ltv_values[0] / cac_values[0] if cac_values[0] > 0 else None
            if ltv_cac_ratio:
                vc_metrics["ltv_cac_ratio"] = {
                    "value": round(ltv_cac_ratio, 2),
                    "ltv": ltv_values[0],
                    "cac": cac_values[0],
                    "assessment": (
                        "healthy" if ltv_cac_ratio >= 3 else "needs_improvement"
                    ),
                }

        return vc_metrics

    def _identify_red_flags(
        self, df: pd.DataFrame, metrics: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify potential red flags in financial data"""

        red_flags = []

        # Check for negative trends in revenue
        revenue_trends = {
            k: v
            for k, v in metrics.items()
            if "revenue" in k.lower() and "trend" in k.lower()
        }
        for metric_name, trend_data in revenue_trends.items():
            if trend_data.get("direction") in ["decreasing", "strongly_decreasing"]:
                red_flags.append(
                    {
                        "type": "revenue_decline",
                        "metric": metric_name,
                        "severity": (
                            "high"
                            if trend_data.get("direction") == "strongly_decreasing"
                            else "medium"
                        ),
                        "description": f"Revenue showing {trend_data.get('direction')} trend",
                    }
                )

        # Check for high burn rate relative to cash
        runway_data = {
            k: v
            for k, v in metrics.items()
            if "runway" in k.lower() or "calculated_runway" in k.lower()
        }
        for metric_name, runway_info in runway_data.items():
            if isinstance(runway_info, dict) and "value" in runway_info:
                runway_months = runway_info["value"]
                if runway_months < 6:
                    red_flags.append(
                        {
                            "type": "low_runway",
                            "metric": metric_name,
                            "severity": "high",
                            "description": f"Runway is only {runway_months:.1f} months - immediate funding needed",
                        }
                    )
                elif runway_months < 12:
                    red_flags.append(
                        {
                            "type": "low_runway",
                            "metric": metric_name,
                            "severity": "medium",
                            "description": f"Runway is {runway_months:.1f} months - should plan for next round",
                        }
                    )

        # Check for poor unit economics
        ltv_cac_ratios = {k: v for k, v in metrics.items() if "ltv_cac" in k.lower()}
        for metric_name, ratio_data in ltv_cac_ratios.items():
            if isinstance(ratio_data, dict) and "value" in ratio_data:
                ratio = ratio_data["value"]
                if ratio < 2:
                    red_flags.append(
                        {
                            "type": "poor_unit_economics",
                            "metric": metric_name,
                            "severity": "high",
                            "description": f"LTV/CAC ratio is {ratio:.2f} - unit economics are unsustainable",
                        }
                    )

        # Check for high churn
        churn_metrics = {k: v for k, v in metrics.items() if "churn" in k.lower()}
        for metric_name, churn_data in churn_metrics.items():
            if isinstance(churn_data, dict) and "latest" in churn_data:
                churn_rate = churn_data["latest"]
                if isinstance(churn_rate, (int, float)):
                    if churn_rate > 10:  # >10% monthly churn is high
                        red_flags.append(
                            {
                                "type": "high_churn",
                                "metric": metric_name,
                                "severity": "high",
                                "description": f"Churn rate is {churn_rate:.2f}% - customer retention is a concern",
                            }
                        )

        return red_flags

    def _generate_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the financial analysis"""

        summary_parts = []

        summary_parts.append(
            f"Financial Analysis Summary for {analysis_results['filename']}"
        )
        summary_parts.append("=" * 60)

        # Key metrics
        if analysis_results["metrics"]:
            summary_parts.append("\nKey Metrics Extracted:")
            for metric_name, metric_data in list(analysis_results["metrics"].items())[
                :10
            ]:
                if isinstance(metric_data, dict) and "latest" in metric_data:
                    summary_parts.append(f"  - {metric_name}: {metric_data['latest']}")

        # Trends
        if analysis_results["trends"]:
            summary_parts.append("\nTrend Analysis:")
            for trend_name, trend_data in list(analysis_results["trends"].items())[:5]:
                if isinstance(trend_data, dict):
                    direction = trend_data.get("direction", "unknown")
                    growth = trend_data.get("average_growth_rate", 0)
                    summary_parts.append(
                        f"  - {trend_name}: {direction} ({growth:.2f}% avg growth)"
                    )

        # Insights
        if analysis_results["insights"]:
            summary_parts.append("\nInsights:")
            for insight in analysis_results["insights"][:5]:
                summary_parts.append(f"  - {insight}")

        # Red flags
        if analysis_results["red_flags"]:
            summary_parts.append("\n⚠️  Red Flags Identified:")
            for flag in analysis_results["red_flags"][:5]:
                severity = flag.get("severity", "unknown")
                description = flag.get("description", "")
                summary_parts.append(f"  [{severity.upper()}] {description}")

        return "\n".join(summary_parts)

    def format_analysis_for_llm(self, analysis_results: Dict[str, Any]) -> str:
        """Format analysis results for LLM consumption"""

        formatted = []

        formatted.append(
            f"FINANCIAL ANALYSIS REPORT: {analysis_results.get('filename', 'Unknown')}"
        )
        formatted.append("=" * 70)

        # Metrics section
        if analysis_results.get("metrics"):
            formatted.append("\nKEY METRICS:")
            for metric_name, metric_data in analysis_results["metrics"].items():
                if isinstance(metric_data, dict):
                    latest = metric_data.get("latest", "N/A")
                    formatted.append(f"  • {metric_name}: {latest}")

        # Trends section
        if analysis_results.get("trends"):
            formatted.append("\nTREND ANALYSIS:")
            for trend_name, trend_data in analysis_results["trends"].items():
                if isinstance(trend_data, dict):
                    direction = trend_data.get("direction", "unknown")
                    growth = trend_data.get("average_growth_rate", 0)
                    formatted.append(
                        f"  • {trend_name}: {direction} (avg growth: {growth:.2f}%)"
                    )

        # Summary section
        if analysis_results.get("summary"):
            formatted.append("\nSUMMARY:")
            formatted.append(analysis_results["summary"])

        return "\n".join(formatted)
