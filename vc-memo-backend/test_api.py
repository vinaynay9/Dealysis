import asyncio
import aiohttp
import json
import time
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta


async def test_memo_generation():
    """Test the memo generation API with all features including Excel/CSV financial files"""

    base_url = "http://localhost:8000"

    print("VC Memo API Test Script")
    print("=" * 50)

    # Create sample template memo file
    template_content = """
# Investment Memo: Example Company

## 1. EXECUTIVE SUMMARY

This section provides a high-level overview of the investment opportunity, including company background, stage, investment ask, and key investment thesis points.

The executive summary should be concise and compelling, highlighting the most important aspects that would influence an investment decision.

## 2. COMPANY DESCRIPTION

This section covers the company's mission, business model, core products and services, and value proposition to customers.

Detail the company's approach to solving customer problems and how it creates value in the market.

## 3. MARKET ANALYSIS

Analyze the total addressable market (TAM), serviceable addressable market (SAM), and serviceable obtainable market (SOM).

Discuss market growth trends, target customer segments, competitive landscape, and the company's positioning within the market.

## 4. BUSINESS METRICS & TRACTION

Present key operational and financial metrics including revenue (ARR/MRR), growth rates, customer metrics, unit economics, and any other relevant traction indicators.

Highlight momentum and progress towards key milestones.

## 5. FINANCIAL OVERVIEW

Cover funding history, current financial position, cap table structure, and valuation details.

Include information about previous rounds, current investors, and financial runway.

## 6. MANAGEMENT TEAM

Provide background on founders and key team members, including relevant experience, past successes, and domain expertise.

Highlight why this team is well-positioned to execute on the opportunity.

## 7. INVESTMENT THESIS & RISK ASSESSMENT

Articulate the key reasons to invest, including competitive advantages, market timing, and growth potential.

Identify and analyze key risks, including market risks, execution risks, competitive risks, and mitigation strategies.

## 8. RECOMMENDATION

Provide a clear investment recommendation (invest/pass/defer) with supporting rationale based on the analysis above.
"""
    with open("sample_template_memo.txt", "w") as f:
        f.write(template_content)
    print("✓ Created sample template memo file")

    # Create sample pitch deck content
    pitch_content = """
    TechStartup Inc - Series A Pitch Deck
    
    Company Overview:
    TechStartup Inc is a B2B SaaS platform that automates workflow management for enterprises.
    Our mission is to increase productivity by 50% through AI-powered automation.
    
    Business Model:
    - Subscription-based SaaS model
    - Tiered pricing: Starter ($99/mo), Professional ($299/mo), Enterprise (custom)
    - Annual contracts with quarterly billing
    
    Products:
    1. WorkflowAI - Core automation platform
    2. Analytics Dashboard - Real-time insights
    3. Integration Hub - 50+ native integrations
    
    Market Opportunity:
    - Total Addressable Market (TAM): $12.5 billion
    - Serviceable Addressable Market (SAM): $3.2 billion
    - Serviceable Obtainable Market (SOM): $180 million
    - Market growing at 25% CAGR
    
    Target Segments:
    - Mid-market enterprises (500-5000 employees)
    - Technology and financial services sectors
    - Companies with complex workflows
    
    Competitive Landscape:
    - Main competitors: AutomateNow, WorkflowPro, ProcessMaster
    - Our advantages: 
      * 70% faster implementation
      * No-code platform
      * Superior AI capabilities
      * Better pricing model
    """
    with open("sample_pitch.txt", "w") as f:
        f.write(pitch_content)
    print("✓ Created sample pitch file")

    # Create sample financials content
    financials_content = """
    TechStartup Inc - Financial Overview
    
    Revenue Metrics:
    - Annual Recurring Revenue (ARR): $4.2 million
    - Monthly Recurring Revenue (MRR): $350,000
    - Month-over-Month Growth: 15%
    - Year-over-Year Growth: 180%
    - Customer Count: 127 enterprise customers
    
    Unit Economics:
    - Customer Acquisition Cost (CAC): $12,000
    - Customer Lifetime Value (LTV): $84,000
    - LTV/CAC Ratio: 7.0
    - Monthly Churn Rate: 1.5%
    - Net Revenue Retention: 125%
    
    Financial Position:
    - Monthly Burn Rate: $450,000
    - Current Runway: 18 months
    - Cash in Bank: $8.1 million
    
    Funding History:
    - Seed Round: $2M (2021, 15% dilution)
    - Pre-Series A: $5M (2022, 12% dilution)
    - Total Raised: $7M
    
    Current Round:
    - Seeking: $15M Series A
    - Pre-money Valuation: $60M
    - Use of Funds:
      * 40% Sales & Marketing
      * 35% Product Development
      * 15% Operations
      * 10% Reserve
    
    Cap Table:
    - Founders: 52%
    - Employees: 15%
    - Seed Investors: 18%
    - Pre-Series A Investors: 15%
    """
    with open("sample_financials.txt", "w") as f:
        f.write(financials_content)
    print("✓ Created sample financials text file")

    # Create sample team content
    team_content = """
    TechStartup Inc - Management Team
    
    Founders:
    
    John Smith - CEO & Co-founder
    - Previously VP Engineering at MegaCorp (acquired for $500M)
    - 15 years experience in enterprise software
    - MS Computer Science, Stanford University
    - Led product team that built $100M ARR product line
    
    Sarah Johnson - CTO & Co-founder
    - Previously Principal Engineer at TechGiant
    - Expert in distributed systems and AI/ML
    - PhD Computer Science, MIT
    - Published 12 papers on workflow automation
    - 2 patents in process optimization
    
    Key Employees:
    - Mike Chen - VP Sales (ex-Salesforce, built team from 0 to $50M ARR)
    - Lisa Park - VP Marketing (ex-HubSpot, grew pipeline 300% YoY)
    - David Brown - VP Engineering (ex-Google, managed 100+ engineers)
    - Amy Wilson - CFO (ex-Deloitte, took 2 companies through Series B)
    
    Board & Advisors:
    - Tom Anderson - Board Member (Partner at TopTier Ventures)
    - Jennifer Lee - Board Observer (Principal at MegaFund)
    - Robert Taylor - Advisor (Former CEO of WorkflowGiant, $2B exit)
    - Maria Garcia - Advisor (CPO at Fortune 500 company)
    
    Team Highlights:
    - Combined 3 successful exits totaling $1.2B
    - Deep domain expertise in workflow automation
    - Strong network in target customer segments
    - Previously worked together at 2 companies
    """
    with open("sample_team.txt", "w") as f:
        f.write(team_content)
    print("✓ Created sample team file")

    # Create sample Excel financial file with time series data
    start_date = datetime(2023, 1, 1)
    months = []
    dates = []
    mrr_values = []
    arr_values = []
    customer_count = []
    cac_values = []
    churn_rate = []
    cash_balance = []
    burn_rate = []

    # Generate 12 months of data with growth trends
    for i in range(12):
        month_date = start_date + timedelta(days=30 * i)
        dates.append(month_date.strftime("%Y-%m-%d"))
        months.append(month_date.strftime("%B %Y"))

        # MRR growing at ~15% MoM
        mrr = 200000 * (1.15**i)
        mrr_values.append(round(mrr, 2))

        # ARR = MRR * 12
        arr_values.append(round(mrr * 12, 2))

        # Customer count growing
        customer_count.append(50 + i * 8)

        # CAC slightly decreasing over time (scale efficiency)
        cac_values.append(round(15000 - (i * 200), 2))

        # Churn rate improving
        churn_rate.append(round(2.5 - (i * 0.1), 2))

        # Cash balance decreasing due to burn
        initial_cash = 8000000
        monthly_burn = 450000 + (i * 10000)  # Slight increase in burn
        cash_balance.append(round(initial_cash - (monthly_burn * i), 2))
        burn_rate.append(round(monthly_burn, 2))

    # Create DataFrame for financial metrics
    financial_df = pd.DataFrame(
        {
            "Month": months,
            "Date": dates,
            "MRR": mrr_values,
            "ARR": arr_values,
            "Customer Count": customer_count,
            "CAC": cac_values,
            "Churn Rate (%)": churn_rate,
            "Cash Balance": cash_balance,
            "Monthly Burn Rate": burn_rate,
        }
    )

    # Create P&L DataFrame
    pl_data = {
        "Month": months[:6],  # Last 6 months
        "Revenue": [mrr * 12 / 12 for mrr in mrr_values[:6]],  # Monthly revenue
        "COGS": [rev * 0.15 for rev in [mrr * 12 / 12 for mrr in mrr_values[:6]]],
        "Gross Profit": [],
        "Sales & Marketing": [
            rev * 0.40 for rev in [mrr * 12 / 12 for mrr in mrr_values[:6]]
        ],
        "Product Development": [
            rev * 0.35 for rev in [mrr * 12 / 12 for mrr in mrr_values[:6]]
        ],
        "Operations": [rev * 0.15 for rev in [mrr * 12 / 12 for mrr in mrr_values[:6]]],
        "EBITDA": [],
        "Net Income": [],
    }

    # Calculate derived fields
    for i in range(6):
        pl_data["Gross Profit"].append(pl_data["Revenue"][i] - pl_data["COGS"][i])
        pl_data["EBITDA"].append(
            pl_data["Gross Profit"][i]
            - pl_data["Sales & Marketing"][i]
            - pl_data["Product Development"][i]
            - pl_data["Operations"][i]
        )
        pl_data["Net Income"].append(pl_data["EBITDA"][i])

    pl_df = pd.DataFrame(pl_data)

    # Save to Excel with multiple sheets
    with pd.ExcelWriter("sample_financials.xlsx", engine="openpyxl") as writer:
        financial_df.to_excel(writer, sheet_name="Financial Metrics", index=False)
        pl_df.to_excel(writer, sheet_name="P&L Statement", index=False)
    print("✓ Created sample Excel financial file (sample_financials.xlsx)")

    # Create CSV file with unit economics
    unit_economics_data = {
        "Metric": [
            "Customer Acquisition Cost (CAC)",
            "Customer Lifetime Value (LTV)",
            "LTV/CAC Ratio",
            "Payback Period (months)",
            "Monthly Churn Rate (%)",
            "Annual Churn Rate (%)",
            "Net Revenue Retention (%)",
            "Gross Margin (%)",
            "CAC Payback Period (months)",
        ],
        "Value": [
            12000,
            84000,
            7.0,
            3.5,
            1.5,
            18.0,
            125.0,
            85.0,
            3.5,
        ],
        "Benchmark": [
            "< $15,000",
            "> $50,000",
            "> 3.0",
            "< 6 months",
            "< 2%",
            "< 20%",
            "> 100%",
            "> 70%",
            "< 12 months",
        ],
        "Status": [
            "Good",
            "Excellent",
            "Excellent",
            "Excellent",
            "Good",
            "Good",
            "Excellent",
            "Excellent",
            "Excellent",
        ],
    }
    unit_economics_df = pd.DataFrame(unit_economics_data)
    unit_economics_df.to_csv("sample_unit_economics.csv", index=False)
    print("✓ Created sample CSV file (sample_unit_economics.csv)")

    # Now test the API
    async with aiohttp.ClientSession() as session:
        # 1. Upload files with template and Excel/CSV
        print("\n" + "=" * 50)
        print("TESTING MEMO GENERATION WITH ALL FILE TYPES")
        print("=" * 50)
        print("1. Uploading documents (including Excel/CSV financial files)...")

        data = aiohttp.FormData()
        data.add_field("company_name", "TechStartup Inc")
        data.add_field("funding_stage", "Series A")

        # Add text files
        for filename in [
            "sample_pitch.txt",
            "sample_financials.txt",
            "sample_team.txt",
        ]:
            with open(filename, "rb") as f:
                data.add_field(
                    "files", f.read(), filename=filename, content_type="text/plain"
                )

        # Add Excel file
        with open("sample_financials.xlsx", "rb") as f:
            data.add_field(
                "files",
                f.read(),
                filename="sample_financials.xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # Add CSV file
        with open("sample_unit_economics.csv", "rb") as f:
            data.add_field(
                "files",
                f.read(),
                filename="sample_unit_economics.csv",
                content_type="text/csv",
            )

        # Add template file
        with open("sample_template_memo.txt", "rb") as f:
            data.add_field(
                "template_file",
                f.read(),
                filename="sample_template_memo.txt",
                content_type="text/plain",
            )

        async with session.post(f"{base_url}/upload-and-process", data=data) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print(f"Error uploading files: HTTP {resp.status} - {error_text}")
                return

            result = await resp.json()
            if "job_id" not in result:
                print(f"Unexpected upload response: {result}")
                return

            print(f"Upload response: {json.dumps(result, indent=2)}")
            job_id = result["job_id"]

        # 2. Poll for status
        print(f"\n2. Polling job status for job_id: {job_id}")

        status = "processing"
        attempts = 0
        max_attempts = 60  # 5 minutes timeout

        while status == "processing" and attempts < max_attempts:
            await asyncio.sleep(5)  # Wait 5 seconds between polls

            async with session.get(f"{base_url}/status/{job_id}") as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"Error checking status: HTTP {resp.status} - {error_text}")
                    status = "failed"
                    break

                status_result = await resp.json()
                if "status" not in status_result:
                    print(f"Unexpected response format: {status_result}")
                    status = "failed"
                    break

                status = status_result["status"]
                progress = status_result.get("progress", "")
                print(f"Status: {status} - {progress}")

            attempts += 1

        # 3. Get the memo
        if status == "completed":
            print(f"\n3. Retrieving completed memo...")

            try:
                async with session.get(f"{base_url}/memo/{job_id}") as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(
                            f"Error retrieving memo: HTTP {resp.status} - {error_text}"
                        )
                    else:
                        memo_result = await resp.json()

                        print("\n" + "=" * 70)
                        print("GENERATED MEMO")
                        print("=" * 70)
                        if "memo_content" in memo_result:
                            print(memo_result["memo_content"])
                        else:
                            print("Memo content not found in response")
                            print(f"Response: {json.dumps(memo_result, indent=2)}")

                        if "confidence_scores" in memo_result:
                            print("\n" + "=" * 70)
                            print("CONFIDENCE SCORES")
                            print("=" * 70)
                            for section, score in memo_result[
                                "confidence_scores"
                            ].items():
                                print(f"{section}: {score:.2f}")

                        if "flagged_items" in memo_result:
                            print("\n" + "=" * 70)
                            print(
                                f"FLAGGED ITEMS ({len(memo_result['flagged_items'])})"
                            )
                            print("=" * 70)
                            for item in memo_result["flagged_items"]:
                                print(f"- {item['section']}: {item['reason']}")
                                if item.get("missing_data"):
                                    print(
                                        f"  Missing: {', '.join(item['missing_data'])}"
                                    )
            except Exception as e:
                print(f"Exception while retrieving memo: {e}")

        elif status == "failed":
            print(f"\n3. Job failed!")
            try:
                async with session.get(f"{base_url}/status/{job_id}") as resp:
                    if resp.status == 200:
                        error_result = await resp.json()
                        error_msg = error_result.get("error", "Unknown error")
                        if isinstance(error_msg, list):
                            error_msg = "; ".join(str(e) for e in error_msg)
                        print(f"Error: {error_msg}")
                    else:
                        error_text = await resp.text()
                        print(
                            f"Error retrieving status: HTTP {resp.status} - {error_text}"
                        )
            except Exception as e:
                print(f"Exception while checking error status: {e}")

        else:
            print(f"\n3. Job timed out (status: {status})")


async def test_health_check():
    """Test the health endpoint"""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/health") as resp:
            result = await resp.json()
            print(f"Health check: {result}")


if __name__ == "__main__":
    asyncio.run(test_memo_generation())
