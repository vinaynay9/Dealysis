#!/usr/bin/env python3
"""
Script to create comprehensive mock data for Zinnia
All documents will include ALL required fields for testing high confidence scores
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
import os

# Create output directory
output_dir = os.path.dirname(os.path.abspath(__file__))

def create_investor_deck():
    """Create comprehensive investor deck with all required information"""
    doc = Document()
    
    # Title
    title = doc.add_heading('Zinnia', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph('Seed Investment Opportunity')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_page_break()
    
    # Company Overview
    doc.add_heading('Company Overview', 1)
    doc.add_paragraph('The company name is Zinnia.')
    doc.add_paragraph('Zinnia is a fintech platform that provides automated financial planning and investment management for small businesses.')
    doc.add_paragraph('Mission: Empower small businesses with AI-driven financial planning and investment management to achieve sustainable growth.')
    doc.add_paragraph('Business Model: SaaS subscription with transaction fees')
    doc.add_paragraph('Products:')
    doc.add_paragraph('  • Zinnia Planner: Automated financial planning and budgeting tool', style='List Bullet')
    doc.add_paragraph('  • Zinnia Invest: AI-powered investment portfolio management', style='List Bullet')
    doc.add_paragraph('  • Zinnia Insights: Real-time financial analytics and reporting', style='List Bullet')
    doc.add_paragraph('Value Proposition: Help small businesses optimize cash flow and grow wealth through intelligent financial management')
    doc.add_paragraph('Go-to-Market: Direct sales to SMBs + partnerships with accounting software providers')
    doc.add_paragraph('The funding stage is Seed.')
    doc.add_paragraph('Funding Stage: Seed')
    
    doc.add_page_break()
    
    # Market Opportunity
    doc.add_heading('Market Opportunity', 1)
    doc.add_paragraph('Total Addressable Market (TAM): $12 billion globally for SMB financial planning software')
    doc.add_paragraph('Serviceable Available Market (SAM): $2.1 billion in North America SMB market')
    doc.add_paragraph('Serviceable Obtainable Market (SOM): $85 million addressable in next 3 years')
    doc.add_paragraph('Market Growth Rate: 22% CAGR over next 5 years')
    doc.add_paragraph('Target Segments:')
    doc.add_paragraph('  • Small businesses with 10-50 employees', style='List Bullet')
    doc.add_paragraph('  • Professional services firms', style='List Bullet')
    doc.add_paragraph('  • E-commerce businesses', style='List Bullet')
    
    doc.add_page_break()
    
    # Competitive Landscape
    doc.add_heading('Competitive Landscape', 1)
    doc.add_paragraph('Competitors: QuickBooks, Xero, FreshBooks, Mint')
    doc.add_paragraph('Competitive Advantages:')
    doc.add_paragraph('  • AI-first approach with predictive financial modeling', style='List Bullet')
    doc.add_paragraph('  • Integrated investment management (unique in SMB space)', style='List Bullet')
    doc.add_paragraph('  • Lower cost (50% cheaper than enterprise solutions)', style='List Bullet')
    doc.add_paragraph('  • Faster onboarding (2 weeks vs. 2+ months for competitors)', style='List Bullet')
    
    doc.add_page_break()
    
    # Traction & Metrics
    doc.add_heading('Traction & Metrics', 1)
    doc.add_paragraph('Annual Recurring Revenue (ARR): $850,000 in 2024, projected $1.8 million in 2025')
    doc.add_paragraph('Monthly Recurring Revenue (MRR): $70,833')
    doc.add_paragraph('Growth Rate Month-over-Month: 12%')
    doc.add_paragraph('Growth Rate Year-over-Year: 95%')
    doc.add_paragraph('Burn Rate: $45,000 per month')
    doc.add_paragraph('Runway: 16 months')
    doc.add_paragraph('Churn Rate: 4.5% (below industry average of 6%)')
    doc.add_paragraph('Customer Count: 320 small business customers')
    doc.add_paragraph('Customer Acquisition Cost (CAC): $2,500')
    doc.add_paragraph('Lifetime Value (LTV): $42,000')
    doc.add_paragraph('LTV:CAC Ratio: 16.8:1')
    
    doc.add_page_break()
    
    # Financial Overview
    doc.add_heading('Financial Overview', 1)
    doc.add_paragraph('Previous Funding: Pre-seed round of $500,000 at $3 million pre-money valuation')
    doc.add_paragraph('The total funding raised to date is $500,000.')
    doc.add_paragraph('Total Funding Raised: $500,000')
    doc.add_paragraph('The last valuation was $3 million in the pre-seed round completed on March 10, 2024.')
    doc.add_paragraph('Last Valuation: $3 million (pre-seed round, March 2024)')
    doc.add_paragraph('Current Round: Seed')
    doc.add_paragraph('The funding stage is Seed.')
    doc.add_paragraph('The investment ask is $750,000.')
    doc.add_paragraph('Investment Ask: $750,000')
    doc.add_paragraph('The current round size is $750,000.')
    doc.add_paragraph('Current Round Size: $750,000')
    doc.add_paragraph('Post-Money Valuation: $6 million')
    doc.add_paragraph('Use of Funds:')
    doc.add_paragraph('  • 45% Sales and Marketing (expand sales team, customer acquisition)', style='List Bullet')
    doc.add_paragraph('  • 30% Product Development (enhance AI models, new features)', style='List Bullet')
    doc.add_paragraph('  • 25% Operations and Runway Buffer (infrastructure, working capital)', style='List Bullet')
    
    doc.add_page_break()
    
    # Team
    doc.add_heading('Team', 1)
    doc.add_paragraph('The founders are Alex Thompson and Maria Garcia.')
    doc.add_paragraph('Founders:')
    doc.add_paragraph('  • Alex Thompson, CEO - Former VP of Product at Stripe, 12 years of experience in fintech. Led product team of 50+ engineers. Previous exit: Sold payment processing startup to Square for $25 million.')
    doc.add_paragraph('  • Maria Garcia, CTO - Former Senior Engineer at Plaid, PhD in Computer Science from UC Berkeley. Published 20+ papers on financial algorithms. Expert in financial data systems and machine learning.')
    doc.add_paragraph('The team has combined 25+ years of relevant experience in fintech and financial software.')
    doc.add_paragraph('Key Employees:')
    doc.add_paragraph('  • David Lee, VP of Sales - Former Sales Director at Intuit, 8 years in SMB sales', style='List Bullet')
    doc.add_paragraph('  • Jennifer Park, VP of Engineering - Former Engineering Manager at Square, 10 years building fintech products', style='List Bullet')
    doc.add_paragraph('  • Robert Chen, Head of Product - Former Product Manager at Mint, 7 years in financial planning products', style='List Bullet')
    doc.add_paragraph('Advisors:')
    doc.add_paragraph('  • James Wilson, Former CFO of Intuit', style='List Bullet')
    doc.add_paragraph('  • Patricia Brown, Partner at Sequoia Capital', style='List Bullet')
    doc.add_paragraph('Board Members: Alex Thompson, Maria Garcia, Lead investor from pre-seed round')
    doc.add_paragraph('Past Exits: Alex Thompson sold previous payment processing startup to Square for $25 million in 2021')
    doc.add_paragraph('Relevant Experience: Combined 25+ years in fintech and financial software')
    
    # Save
    doc.save(os.path.join(output_dir, 'Zinnia Investor Deck.docx'))
    print("✓ Created Investor Deck")

def create_financials_spreadsheet():
    """Create comprehensive financial spreadsheet"""
    wb = Workbook()
    
    # Cap Table Sheet
    ws1 = wb.active
    ws1.title = "Cap Table"
    ws1['A1'] = 'Shareholder'
    ws1['B1'] = 'Shares'
    ws1['C1'] = 'Ownership %'
    ws1['D1'] = 'Investment'
    
    headers = ['A1', 'B1', 'C1', 'D1']
    for cell in headers:
        ws1[cell].font = Font(bold=True)
        ws1[cell].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws1[cell].font = Font(bold=True, color="FFFFFF")
    
    cap_table_data = [
        ['Founders (Alex + Maria)', '4,000,000', '50.0%', '$0'],
        ['Pre-seed Investors', '500,000', '6.25%', '$500,000'],
        ['Employee Pool', '1,000,000', '12.5%', '$0'],
        ['Seed (New)', '2,500,000', '31.25%', '$750,000'],
    ]
    
    for i, row in enumerate(cap_table_data, start=2):
        for j, value in enumerate(row, start=1):
            ws1.cell(row=i, column=j, value=value)
    
    # Financial Projections Sheet
    ws2 = wb.create_sheet("Financial Projections")
    ws2['A1'] = 'Metric'
    ws2['B1'] = '2024'
    ws2['C1'] = '2025 (Projected)'
    ws2['D1'] = '2026 (Projected)'
    
    for cell in ['A1', 'B1', 'C1', 'D1']:
        ws2[cell].font = Font(bold=True)
        ws2[cell].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws2[cell].font = Font(bold=True, color="FFFFFF")
    
    projections = [
        ['ARR', '$850,000', '$1,800,000', '$3,600,000'],
        ['MRR', '$70,833', '$150,000', '$300,000'],
        ['Growth Rate MoM', '12%', '10%', '8%'],
        ['Growth Rate YoY', '95%', '112%', '100%'],
        ['Burn Rate (Monthly)', '$45,000', '$55,000', '$65,000'],
        ['Runway (Months)', '16', '20', '24'],
        ['Churn Rate', '4.5%', '4.0%', '3.5%'],
        ['Customer Count', '320', '640', '1,280'],
        ['CAC', '$2,500', '$2,200', '$2,000'],
        ['LTV', '$42,000', '$45,000', '$48,000'],
    ]
    
    for i, row in enumerate(projections, start=2):
        for j, value in enumerate(row, start=1):
            ws2.cell(row=i, column=j, value=value)
    
    # Funding Rounds Sheet
    ws3 = wb.create_sheet("Funding Rounds")
    ws3['A1'] = 'Round'
    ws3['B1'] = 'Date'
    ws3['C1'] = 'Amount'
    ws3['D1'] = 'Pre-Money Valuation'
    ws3['E1'] = 'Post-Money Valuation'
    
    for cell in ['A1', 'B1', 'C1', 'D1', 'E1']:
        ws3[cell].font = Font(bold=True)
        ws3[cell].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws3[cell].font = Font(bold=True, color="FFFFFF")
    
    rounds = [
        ['Pre-seed', '2024-03-10', '$500,000', '$3,000,000', '$3,500,000'],
        ['Seed', '2024-11-01', '$750,000', '$5,250,000', '$6,000,000'],
    ]
    
    for i, row in enumerate(rounds, start=2):
        for j, value in enumerate(row, start=1):
            ws3.cell(row=i, column=j, value=value)
    
    # Use of Funds Sheet
    ws4 = wb.create_sheet("Use of Funds")
    ws4['A1'] = 'Category'
    ws4['B1'] = 'Percentage'
    ws4['C1'] = 'Amount'
    
    for cell in ['A1', 'B1', 'C1']:
        ws4[cell].font = Font(bold=True)
        ws4[cell].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws4[cell].font = Font(bold=True, color="FFFFFF")
    
    use_of_funds = [
        ['Sales and Marketing', '45%', '$337,500'],
        ['Product Development', '30%', '$225,000'],
        ['Operations and Runway', '25%', '$187,500'],
    ]
    
    for i, row in enumerate(use_of_funds, start=2):
        for j, value in enumerate(row, start=1):
            ws4.cell(row=i, column=j, value=value)
    
    # Company Summary Sheet with explicit statements
    ws5 = wb.create_sheet("Company Summary")
    ws5['A1'] = 'Field'
    ws5['B1'] = 'Value'
    
    for cell in ['A1', 'B1']:
        ws5[cell].font = Font(bold=True)
        ws5[cell].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws5[cell].font = Font(bold=True, color="FFFFFF")
    
    summary_data = [
        ['Company Name', 'Zinnia'],
        ['Funding Stage', 'Seed'],
        ['Investment Ask', '$750,000'],
        ['Current Round Size', '$750,000'],
        ['Total Funding Raised', '$500,000'],
        ['Last Valuation', '$3 million (pre-seed round, March 2024)'],
    ]
    
    for i, row in enumerate(summary_data, start=2):
        for j, value in enumerate(row, start=1):
            ws5.cell(row=i, column=j, value=value)
    
    wb.save(os.path.join(output_dir, 'Zinnia Financials.xlsx'))
    print("✓ Created Financials Spreadsheet")

def create_email_chains():
    """Create email chains with investor conversations"""
    doc = Document()
    
    doc.add_heading('Email Chain 1 - Initial Investor Outreach', 1)
    
    doc.add_paragraph('From: Alex Thompson <alex@zinnia.com>')
    doc.add_paragraph('To: investor@vc-firm.com')
    doc.add_paragraph('Date: September 20, 2024')
    doc.add_paragraph('Subject: Seed Opportunity - Zinnia')
    
    doc.add_paragraph('Hi [Investor Name],')
    doc.add_paragraph('')
    doc.add_paragraph('I wanted to reach out about our Seed round for Zinnia. The company name is Zinnia. The funding stage is Seed. We\'re raising $750,000 at a $6 million post-money valuation. The investment ask is $750,000. The current round size is $750,000.')
    doc.add_paragraph('')
    doc.add_paragraph('Quick highlights:')
    doc.add_paragraph('  • ARR: $850K, growing 12% MoM')
    doc.add_paragraph('  • MRR: $70,833')
    doc.add_paragraph('  • 320 small business customers, 4.5% churn')
    doc.add_paragraph('  • Burn rate: $45K/month, 16 months runway')
    doc.add_paragraph('  • Unit economics: CAC $2.5K, LTV $42K (16.8:1 ratio)')
    doc.add_paragraph('')
    doc.add_paragraph('The total funding raised to date is $500,000. We\'ve raised $500K in pre-seed from [Pre-seed Investor]. The last valuation was $3 million in March 2024. Use of funds: 45% sales/marketing, 30% product, 25% ops.')
    doc.add_paragraph('')
    doc.add_paragraph('Would love to discuss further!')
    doc.add_paragraph('Alex')
    
    doc.add_page_break()
    
    doc.add_heading('Email Chain 2 - Due Diligence Q&A', 1)
    
    doc.add_paragraph('From: investor@vc-firm.com')
    doc.add_paragraph('To: Alex Thompson <alex@zinnia.com>')
    doc.add_paragraph('Date: September 25, 2024')
    doc.add_paragraph('Subject: Re: Seed - Market Questions')
    
    doc.add_paragraph('Hi Alex,')
    doc.add_paragraph('')
    doc.add_paragraph('Can you provide more details on the market opportunity?')
    doc.add_paragraph('')
    doc.add_paragraph('From: Alex Thompson <alex@zinnia.com>')
    doc.add_paragraph('To: investor@vc-firm.com')
    doc.add_paragraph('Date: September 25, 2024')
    doc.add_paragraph('Subject: Re: Seed - Market Questions')
    
    doc.add_paragraph('Hi [Investor],')
    doc.add_paragraph('')
    doc.add_paragraph('Market details:')
    doc.add_paragraph('  • TAM: $12B globally')
    doc.add_paragraph('  • SAM: $2.1B in North America SMB')
    doc.add_paragraph('  • SOM: $85M addressable in 3 years')
    doc.add_paragraph('  • Market growth: 22% CAGR')
    doc.add_paragraph('')
    doc.add_paragraph('Competitors: QuickBooks, Xero, FreshBooks, Mint')
    doc.add_paragraph('Our advantages: AI-first, integrated investment management, 50% lower cost, faster onboarding')
    doc.add_paragraph('')
    doc.add_paragraph('Best,')
    doc.add_paragraph('Alex')
    
    doc.add_page_break()
    
    doc.add_heading('Email Chain 3 - Team Introduction', 1)
    
    doc.add_paragraph('From: Alex Thompson <alex@zinnia.com>')
    doc.add_paragraph('To: investor@vc-firm.com')
    doc.add_paragraph('Date: September 30, 2024')
    doc.add_paragraph('Subject: Team Background - Zinnia')
    
    doc.add_paragraph('Hi [Investor],')
    doc.add_paragraph('')
    doc.add_paragraph('As requested, here\'s our team background:')
    doc.add_paragraph('')
    doc.add_paragraph('The founders are Alex Thompson and Maria Garcia.')
    doc.add_paragraph('Founders:')
    doc.add_paragraph('  • Me (Alex Thompson, CEO): Former VP of Product at Stripe, 12 years experience. Previous exit: sold payment processing startup to Square for $25M in 2021.')
    doc.add_paragraph('  • Maria Garcia (CTO): Ex-Plaid Senior Engineer, PhD UC Berkeley, 20+ published papers on financial algorithms.')
    doc.add_paragraph('The team has combined 25+ years of relevant experience in fintech and financial software.')
    doc.add_paragraph('')
    doc.add_paragraph('Key team:')
    doc.add_paragraph('  • David Lee, VP Sales (ex-Intuit Sales Director)')
    doc.add_paragraph('  • Jennifer Park, VP Engineering (ex-Square Engineering Manager)')
    doc.add_paragraph('  • Robert Chen, Head of Product (ex-Mint Product Manager)')
    doc.add_paragraph('')
    doc.add_paragraph('Advisors: James Wilson (former Intuit CFO), Patricia Brown (Sequoia Partner)')
    doc.add_paragraph('')
    doc.add_paragraph('The team has combined 25+ years of relevant experience in fintech and financial software.')
    doc.add_paragraph('')
    doc.add_paragraph('Best,')
    doc.add_paragraph('Alex')
    
    doc.save(os.path.join(output_dir, 'Email Chains.docx'))
    print("✓ Created Email Chains")

def create_diligence_document():
    """Create comprehensive diligence document"""
    doc = Document()
    
    doc.add_heading('Zinnia - Due Diligence Package', 0)
    doc.add_paragraph('Prepared for: [VC Firm]')
    doc.add_paragraph('Date: November 2024')
    doc.add_paragraph('Seed Round: $750K at $6M post-money valuation')
    
    doc.add_page_break()
    
    # Company Information
    doc.add_heading('Company Information', 1)
    doc.add_paragraph('The company name is Zinnia.')
    doc.add_paragraph('Company Name: Zinnia')
    doc.add_paragraph('Mission: Empower small businesses with AI-driven financial planning and investment management to achieve sustainable growth.')
    doc.add_paragraph('Business Model: SaaS subscription with transaction fees')
    doc.add_paragraph('Products:')
    doc.add_paragraph('  • Zinnia Planner: Automated financial planning and budgeting tool', style='List Bullet')
    doc.add_paragraph('  • Zinnia Invest: AI-powered investment portfolio management', style='List Bullet')
    doc.add_paragraph('  • Zinnia Insights: Real-time financial analytics and reporting', style='List Bullet')
    doc.add_paragraph('Value Proposition: Help small businesses optimize cash flow and grow wealth through intelligent financial management')
    doc.add_paragraph('Go-to-Market Strategy: Direct sales to SMBs + partnerships with accounting software providers')
    doc.add_paragraph('The funding stage is Seed.')
    doc.add_paragraph('Funding Stage: Seed')
    doc.add_paragraph('Current Round Details: Raising $750,000 Seed round at $6 million post-money valuation')
    
    doc.add_page_break()
    
    # Market Analysis
    doc.add_heading('Market Analysis', 1)
    doc.add_paragraph('Total Addressable Market (TAM): $12 billion globally for SMB financial planning software')
    doc.add_paragraph('Serviceable Available Market (SAM): $2.1 billion in North America SMB market')
    doc.add_paragraph('Serviceable Obtainable Market (SOM): $85 million addressable market in next 3 years')
    doc.add_paragraph('Market Growth Rate: 22% CAGR over next 5 years')
    doc.add_paragraph('Target Segments: Small businesses with 10-50 employees, professional services firms, e-commerce businesses')
    
    doc.add_heading('Competitive Analysis', 2)
    doc.add_paragraph('Primary Competitors: QuickBooks, Xero, FreshBooks, Mint')
    doc.add_paragraph('Competitive Advantages:')
    doc.add_paragraph('  • AI-first approach with predictive financial modeling', style='List Bullet')
    doc.add_paragraph('  • Integrated investment management (unique in SMB space)', style='List Bullet')
    doc.add_paragraph('  • Lower cost (50% cheaper than enterprise solutions)', style='List Bullet')
    doc.add_paragraph('  • Faster onboarding (2 weeks vs. 2+ months for competitors)', style='List Bullet')
    
    doc.add_page_break()
    
    # Financial Details
    doc.add_heading('Financial Details', 1)
    doc.add_paragraph('Previous Funding Rounds:')
    doc.add_paragraph('  • Pre-seed Round: $500,000 raised in March 2024 at $3 million pre-money valuation', style='List Bullet')
    doc.add_paragraph('The total funding raised to date is $500,000.')
    doc.add_paragraph('Total Funding Raised: $500,000')
    doc.add_paragraph('The last valuation was $3 million in the pre-seed round completed on March 10, 2024.')
    doc.add_paragraph('Last Valuation: $3 million (pre-seed round, March 2024)')
    doc.add_paragraph('Current Round: Seed')
    doc.add_paragraph('The funding stage is Seed.')
    doc.add_paragraph('The investment ask is $750,000.')
    doc.add_paragraph('Investment Ask: $750,000')
    doc.add_paragraph('The current round size is $750,000.')
    doc.add_paragraph('Current Round Size: $750,000')
    doc.add_paragraph('Pre-Money Valuation: $5.25 million')
    doc.add_paragraph('Post-Money Valuation: $6 million')
    doc.add_paragraph('Use of Funds:')
    doc.add_paragraph('  • 45% ($337.5K) Sales and Marketing: Expand sales team, customer acquisition, marketing campaigns', style='List Bullet')
    doc.add_paragraph('  • 30% ($225K) Product Development: Enhance AI models, develop new features, platform improvements', style='List Bullet')
    doc.add_paragraph('  • 25% ($187.5K) Operations and Runway Buffer: Infrastructure scaling, working capital, operational expenses', style='List Bullet')
    
    doc.add_page_break()
    
    # Growth Metrics
    doc.add_heading('Growth Metrics', 1)
    doc.add_paragraph('Annual Recurring Revenue (ARR):')
    doc.add_paragraph('  • 2024: $850,000', style='List Bullet')
    doc.add_paragraph('  • 2025 (Projected): $1.8 million', style='List Bullet')
    doc.add_paragraph('  • 2026 (Projected): $3.6 million', style='List Bullet')
    doc.add_paragraph('Monthly Recurring Revenue (MRR): $70,833')
    doc.add_paragraph('Growth Rate Month-over-Month: 12%')
    doc.add_paragraph('Growth Rate Year-over-Year: 95%')
    doc.add_paragraph('Burn Rate: $45,000 per month')
    doc.add_paragraph('Runway: 16 months')
    doc.add_paragraph('Churn Rate: 4.5% (below industry average of 6%)')
    doc.add_paragraph('Customer Count: 320 small business customers')
    doc.add_paragraph('Customer Acquisition Cost (CAC): $2,500')
    doc.add_paragraph('Lifetime Value (LTV): $42,000')
    doc.add_paragraph('LTV:CAC Ratio: 16.8:1 (excellent, benchmark is 3:1)')
    
    doc.add_page_break()
    
    # Team Information
    doc.add_heading('Team Information', 1)
    
    doc.add_heading('Founders', 2)
    doc.add_paragraph('The founders are Alex Thompson and Maria Garcia.')
    doc.add_paragraph('Alex Thompson, CEO')
    doc.add_paragraph('  • Background: Former VP of Product at Stripe, led product team of 50+ engineers')
    doc.add_paragraph('  • Experience: 12 years in fintech')
    doc.add_paragraph('  • Past Exit: Sold payment processing startup to Square for $25 million in 2021')
    doc.add_paragraph('  • Education: MBA from Stanford, BS Computer Science from MIT')
    
    doc.add_paragraph('Maria Garcia, CTO')
    doc.add_paragraph('  • Background: Former Senior Engineer at Plaid, expert in financial data systems and machine learning')
    doc.add_paragraph('  • Experience: 10 years in fintech and financial software')
    doc.add_paragraph('  • Education: PhD in Computer Science from UC Berkeley, published 20+ papers on financial algorithms')
    
    doc.add_heading('Key Employees', 2)
    doc.add_paragraph('David Lee, VP of Sales')
    doc.add_paragraph('  • Background: Former Sales Director at Intuit')
    doc.add_paragraph('  • Experience: 8 years in SMB sales')
    
    doc.add_paragraph('Jennifer Park, VP of Engineering')
    doc.add_paragraph('  • Background: Former Engineering Manager at Square')
    doc.add_paragraph('  • Experience: 10 years building fintech products')
    
    doc.add_paragraph('Robert Chen, Head of Product')
    doc.add_paragraph('  • Background: Former Product Manager at Mint')
    doc.add_paragraph('  • Experience: 7 years in financial planning products')
    
    doc.add_heading('Advisors', 2)
    doc.add_paragraph('James Wilson: Former CFO of Intuit')
    doc.add_paragraph('Patricia Brown: Partner at Sequoia Capital')
    
    doc.add_heading('Board Members', 2)
    doc.add_paragraph('Alex Thompson (CEO), Maria Garcia (CTO), Lead investor from pre-seed round')
    
    doc.add_heading('Past Exits', 2)
    doc.add_paragraph('Alex Thompson sold previous payment processing startup to Square for $25 million in 2021')
    
    doc.add_heading('Relevant Experience', 2)
    doc.add_paragraph('The team has combined 25+ years of relevant experience in fintech and financial software.')
    doc.add_paragraph('Relevant Experience: Combined 25+ years in fintech and financial software')
    
    doc.save(os.path.join(output_dir, 'Zinnia Mock Diligence.docx'))
    print("✓ Created Diligence Document")

if __name__ == '__main__':
    print("Creating comprehensive mock data for Zinnia...")
    print("=" * 60)
    create_investor_deck()
    create_financials_spreadsheet()
    create_email_chains()
    create_diligence_document()
    print("=" * 60)
    print("✓ All mock data created successfully!")
    print(f"Location: {output_dir}")

