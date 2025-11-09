#!/usr/bin/env python3
"""
Script to create comprehensive mock data for Nexus AI
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
    title = doc.add_heading('Nexus AI', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph('Series A Investment Opportunity')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_page_break()
    
    # Company Overview
    doc.add_heading('Company Overview', 1)
    doc.add_paragraph('The company name is Nexus AI.')
    doc.add_paragraph('Nexus AI is an AI-powered supply chain optimization platform that helps enterprises reduce costs by 40% through real-time optimization and predictive analytics.')
    doc.add_paragraph('Mission: Optimize global supply chains with AI to reduce waste, improve efficiency, and enable sustainable operations.')
    doc.add_paragraph('Business Model: SaaS subscription + professional services')
    doc.add_paragraph('Products:')
    doc.add_paragraph('  • Nexus Optimizer: Real-time supply chain optimization engine', style='List Bullet')
    doc.add_paragraph('  • Nexus Predict: AI-powered demand forecasting', style='List Bullet')
    doc.add_paragraph('  • Nexus Connect: Integration platform for ERP systems', style='List Bullet')
    doc.add_paragraph('Value Proposition: Reduce supply chain costs by 40% with AI-powered optimization')
    doc.add_paragraph('Go-to-Market: Enterprise sales + strategic partnerships with SAP, Oracle')
    doc.add_paragraph('The funding stage is Series A.')
    doc.add_paragraph('Funding Stage: Series A')
    
    doc.add_page_break()
    
    # Market Opportunity
    doc.add_heading('Market Opportunity', 1)
    doc.add_paragraph('Total Addressable Market (TAM): $45 billion globally')
    doc.add_paragraph('Serviceable Available Market (SAM): $8.5 billion in North America enterprise market')
    doc.add_paragraph('Serviceable Obtainable Market (SOM): $420 million addressable in next 3 years')
    doc.add_paragraph('Market Growth Rate: 18% CAGR over next 5 years')
    doc.add_paragraph('Target Segments:')
    doc.add_paragraph('  • Fortune 500 manufacturing companies', style='List Bullet')
    doc.add_paragraph('  • Large retail chains', style='List Bullet')
    doc.add_paragraph('  • E-commerce platforms', style='List Bullet')
    
    doc.add_page_break()
    
    # Competitive Landscape
    doc.add_heading('Competitive Landscape', 1)
    doc.add_paragraph('Competitors: SAP, Oracle, Blue Yonder, Kinaxis')
    doc.add_paragraph('Competitive Advantages:')
    doc.add_paragraph('  • AI-first architecture enabling real-time optimization', style='List Bullet')
    doc.add_paragraph('  • 40% average cost reduction vs. traditional solutions', style='List Bullet')
    doc.add_paragraph('  • Faster implementation (3 months vs. 12+ months)', style='List Bullet')
    doc.add_paragraph('  • Superior predictive accuracy (92% vs. industry average 78%)', style='List Bullet')
    
    doc.add_page_break()
    
    # Traction & Metrics
    doc.add_heading('Traction & Metrics', 1)
    doc.add_paragraph('Annual Recurring Revenue (ARR): $2.4 million in 2024, projected $4.8 million in 2025')
    doc.add_paragraph('Monthly Recurring Revenue (MRR): $200,000')
    doc.add_paragraph('Growth Rate Month-over-Month: 15%')
    doc.add_paragraph('Growth Rate Year-over-Year: 120%')
    doc.add_paragraph('Burn Rate: $180,000 per month')
    doc.add_paragraph('Runway: 18 months')
    doc.add_paragraph('Churn Rate: 3% (industry-leading)')
    doc.add_paragraph('Customer Count: 45 enterprise customers')
    doc.add_paragraph('Customer Acquisition Cost (CAC): $12,000')
    doc.add_paragraph('Lifetime Value (LTV): $180,000')
    doc.add_paragraph('LTV:CAC Ratio: 15:1')
    
    doc.add_page_break()
    
    # Financial Overview
    doc.add_heading('Financial Overview', 1)
    doc.add_paragraph('Previous Funding: $2.5 million Seed round at $8 million pre-money valuation')
    doc.add_paragraph('The total funding raised to date is $2.5 million.')
    doc.add_paragraph('Total Funding Raised: $2.5 million')
    doc.add_paragraph('The last valuation was $8 million in the Seed round completed on June 15, 2023.')
    doc.add_paragraph('Last Valuation: $8 million (Seed round, June 2023)')
    doc.add_paragraph('Current Round: Series A')
    doc.add_paragraph('The funding stage is Series A.')
    doc.add_paragraph('The investment ask is $8 million.')
    doc.add_paragraph('Investment Ask: $8 million')
    doc.add_paragraph('The current round size is $8 million.')
    doc.add_paragraph('Current Round Size: $8 million')
    doc.add_paragraph('Post-Money Valuation: $32 million')
    doc.add_paragraph('Use of Funds:')
    doc.add_paragraph('  • 40% Sales and Marketing (expand sales team, marketing campaigns)', style='List Bullet')
    doc.add_paragraph('  • 35% Product Development (enhance AI models, new features)', style='List Bullet')
    doc.add_paragraph('  • 25% Operations and Runway Buffer (infrastructure, working capital)', style='List Bullet')
    
    doc.add_page_break()
    
    # Team
    doc.add_heading('Team', 1)
    doc.add_paragraph('The founders are Sarah Chen and Michael Rodriguez.')
    doc.add_paragraph('Founders:')
    doc.add_paragraph('  • Sarah Chen, CEO - Former VP at Amazon Supply Chain, 15 years of experience in supply chain optimization. Led team of 200+ engineers. Previous exit: Sold logistics startup to Oracle for $50 million.')
    doc.add_paragraph('  • Michael Rodriguez, CTO - Former Google AI researcher, PhD in Computer Science from Stanford. Published 30+ papers on optimization algorithms. Expert in machine learning and distributed systems.')
    doc.add_paragraph('The team has combined 40+ years of relevant experience in supply chain optimization and AI/ML.')
    doc.add_paragraph('Key Employees:')
    doc.add_paragraph('  • James Park, VP of Sales - Former Director at Salesforce, 10 years enterprise sales experience', style='List Bullet')
    doc.add_paragraph('  • Lisa Wang, VP of Engineering - Former Engineering Manager at Microsoft, 12 years building enterprise software', style='List Bullet')
    doc.add_paragraph('  • David Kim, Head of Product - Former Product Lead at Palantir, 8 years in enterprise AI products', style='List Bullet')
    doc.add_paragraph('Advisors:')
    doc.add_paragraph('  • Robert Thompson, Former CEO of FedEx Supply Chain', style='List Bullet')
    doc.add_paragraph('  • Jennifer Martinez, Partner at Andreessen Horowitz (a16z)', style='List Bullet')
    doc.add_paragraph('Board Members: Sarah Chen, Michael Rodriguez, Lead investor from Seed round')
    doc.add_paragraph('Past Exits: Sarah Chen sold previous logistics startup to Oracle for $50 million in 2019')
    doc.add_paragraph('Relevant Experience: Combined 40+ years in supply chain optimization and AI/ML')
    
    # Save
    doc.save(os.path.join(output_dir, 'Nexus AI Investor Deck.docx'))
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
        ['Founders (Sarah + Michael)', '6,000,000', '25.0%', '$0'],
        ['Seed Investors', '2,000,000', '8.3%', '$2,500,000'],
        ['Employee Pool', '2,000,000', '8.3%', '$0'],
        ['Series A (New)', '8,000,000', '33.3%', '$8,000,000'],
        ['Reserved for Future', '5,000,000', '20.8%', '$0'],
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
        ['ARR', '$2,400,000', '$4,800,000', '$9,600,000'],
        ['MRR', '$200,000', '$400,000', '$800,000'],
        ['Growth Rate MoM', '15%', '12%', '10%'],
        ['Growth Rate YoY', '120%', '100%', '100%'],
        ['Burn Rate (Monthly)', '$180,000', '$220,000', '$250,000'],
        ['Runway (Months)', '18', '24', '30'],
        ['Churn Rate', '3%', '2.5%', '2%'],
        ['Customer Count', '45', '90', '180'],
        ['CAC', '$12,000', '$10,000', '$8,000'],
        ['LTV', '$180,000', '$200,000', '$220,000'],
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
        ['Seed', '2023-06-15', '$2,500,000', '$8,000,000', '$10,500,000'],
        ['Series A', '2024-11-01', '$8,000,000', '$24,000,000', '$32,000,000'],
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
        ['Sales and Marketing', '40%', '$3,200,000'],
        ['Product Development', '35%', '$2,800,000'],
        ['Operations and Runway', '25%', '$2,000,000'],
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
        ['Company Name', 'Nexus AI'],
        ['Funding Stage', 'Series A'],
        ['Investment Ask', '$8 million'],
        ['Current Round Size', '$8 million'],
        ['Total Funding Raised', '$2.5 million'],
        ['Last Valuation', '$8 million (Seed round, June 2023)'],
    ]
    
    for i, row in enumerate(summary_data, start=2):
        for j, value in enumerate(row, start=1):
            ws5.cell(row=i, column=j, value=value)
    
    wb.save(os.path.join(output_dir, 'Nexus AI Financials.xlsx'))
    print("✓ Created Financials Spreadsheet")

def create_email_chains():
    """Create email chains with investor conversations"""
    doc = Document()
    
    doc.add_heading('Email Chain 1 - Initial Investor Outreach', 1)
    
    doc.add_paragraph('From: Sarah Chen <sarah@nexusai.com>')
    doc.add_paragraph('To: investor@vc-firm.com')
    doc.add_paragraph('Date: October 15, 2024')
    doc.add_paragraph('Subject: Series A Opportunity - Nexus AI')
    
    doc.add_paragraph('Hi [Investor Name],')
    doc.add_paragraph('')
    doc.add_paragraph('I wanted to reach out about our Series A round for Nexus AI. The company name is Nexus AI. The funding stage is Series A. We\'re raising $8 million at a $32 million post-money valuation. The investment ask is $8 million. The current round size is $8 million.')
    doc.add_paragraph('')
    doc.add_paragraph('Quick highlights:')
    doc.add_paragraph('  • ARR: $2.4M, growing 15% MoM')
    doc.add_paragraph('  • MRR: $200K')
    doc.add_paragraph('  • 45 enterprise customers, 3% churn')
    doc.add_paragraph('  • Burn rate: $180K/month, 18 months runway')
    doc.add_paragraph('  • Unit economics: CAC $12K, LTV $180K (15:1 ratio)')
    doc.add_paragraph('')
    doc.add_paragraph('The total funding raised to date is $2.5 million. We\'ve raised $2.5M in Seed from [Seed Investor]. The last valuation was $8 million in June 2023. Use of funds: 40% sales/marketing, 35% product, 25% ops.')
    doc.add_paragraph('')
    doc.add_paragraph('Would love to discuss further!')
    doc.add_paragraph('Sarah')
    
    doc.add_page_break()
    
    doc.add_heading('Email Chain 2 - Due Diligence Q&A', 1)
    
    doc.add_paragraph('From: investor@vc-firm.com')
    doc.add_paragraph('To: Sarah Chen <sarah@nexusai.com>')
    doc.add_paragraph('Date: October 20, 2024')
    doc.add_paragraph('Subject: Re: Series A - Market Questions')
    
    doc.add_paragraph('Hi Sarah,')
    doc.add_paragraph('')
    doc.add_paragraph('Can you provide more details on the market opportunity?')
    doc.add_paragraph('')
    doc.add_paragraph('From: Sarah Chen <sarah@nexusai.com>')
    doc.add_paragraph('To: investor@vc-firm.com')
    doc.add_paragraph('Date: October 20, 2024')
    doc.add_paragraph('Subject: Re: Series A - Market Questions')
    
    doc.add_paragraph('Hi [Investor],')
    doc.add_paragraph('')
    doc.add_paragraph('Market details:')
    doc.add_paragraph('  • TAM: $45B globally')
    doc.add_paragraph('  • SAM: $8.5B in North America enterprise')
    doc.add_paragraph('  • SOM: $420M addressable in 3 years')
    doc.add_paragraph('  • Market growth: 18% CAGR')
    doc.add_paragraph('')
    doc.add_paragraph('Competitors: SAP, Oracle, Blue Yonder, Kinaxis')
    doc.add_paragraph('Our advantages: AI-first, 40% cost reduction, faster implementation')
    doc.add_paragraph('')
    doc.add_paragraph('Best,')
    doc.add_paragraph('Sarah')
    
    doc.add_page_break()
    
    doc.add_heading('Email Chain 3 - Team Introduction', 1)
    
    doc.add_paragraph('From: Sarah Chen <sarah@nexusai.com>')
    doc.add_paragraph('To: investor@vc-firm.com')
    doc.add_paragraph('Date: October 25, 2024')
    doc.add_paragraph('Subject: Team Background - Nexus AI')
    
    doc.add_paragraph('Hi [Investor],')
    doc.add_paragraph('')
    doc.add_paragraph('As requested, here\'s our team background:')
    doc.add_paragraph('')
    doc.add_paragraph('The founders are Sarah Chen and Michael Rodriguez.')
    doc.add_paragraph('Founders:')
    doc.add_paragraph('  • Me (Sarah Chen, CEO): Former VP at Amazon Supply Chain, 15 years experience. Previous exit: sold logistics startup to Oracle for $50M in 2019.')
    doc.add_paragraph('  • Michael Rodriguez (CTO): Ex-Google AI researcher, PhD Stanford, 30+ published papers on optimization.')
    doc.add_paragraph('The team has combined 40+ years of relevant experience in supply chain optimization and AI/ML.')
    doc.add_paragraph('')
    doc.add_paragraph('Key team:')
    doc.add_paragraph('  • James Park, VP Sales (ex-Salesforce Director)')
    doc.add_paragraph('  • Lisa Wang, VP Engineering (ex-Microsoft Engineering Manager)')
    doc.add_paragraph('  • David Kim, Head of Product (ex-Palantir Product Lead)')
    doc.add_paragraph('')
    doc.add_paragraph('Advisors: Robert Thompson (former FedEx Supply Chain CEO), Jennifer Martinez (a16z Partner)')
    doc.add_paragraph('')
    doc.add_paragraph('The team has combined 40+ years of relevant experience in supply chain optimization and AI/ML.')
    doc.add_paragraph('')
    doc.add_paragraph('Best,')
    doc.add_paragraph('Sarah')
    
    doc.save(os.path.join(output_dir, 'Email Chains.docx'))
    print("✓ Created Email Chains")

def create_diligence_document():
    """Create comprehensive diligence document"""
    doc = Document()
    
    doc.add_heading('Nexus AI - Due Diligence Package', 0)
    doc.add_paragraph('Prepared for: [VC Firm]')
    doc.add_paragraph('Date: November 2024')
    doc.add_paragraph('Series A Round: $8M at $32M post-money valuation')
    
    doc.add_page_break()
    
    # Company Information
    doc.add_heading('Company Information', 1)
    doc.add_paragraph('The company name is Nexus AI.')
    doc.add_paragraph('Company Name: Nexus AI')
    doc.add_paragraph('Mission: Optimize global supply chains with AI to reduce waste, improve efficiency, and enable sustainable operations.')
    doc.add_paragraph('Business Model: SaaS subscription + professional services')
    doc.add_paragraph('Products:')
    doc.add_paragraph('  • Nexus Optimizer: Real-time supply chain optimization engine', style='List Bullet')
    doc.add_paragraph('  • Nexus Predict: AI-powered demand forecasting', style='List Bullet')
    doc.add_paragraph('  • Nexus Connect: Integration platform for ERP systems', style='List Bullet')
    doc.add_paragraph('Value Proposition: Reduce supply chain costs by 40% with AI-powered optimization')
    doc.add_paragraph('Go-to-Market Strategy: Enterprise sales + strategic partnerships with SAP and Oracle')
    doc.add_paragraph('The funding stage is Series A.')
    doc.add_paragraph('Funding Stage: Series A')
    doc.add_paragraph('Current Round Details: Raising $8 million Series A at $32 million post-money valuation')
    
    doc.add_page_break()
    
    # Market Analysis
    doc.add_heading('Market Analysis', 1)
    doc.add_paragraph('Total Addressable Market (TAM): $45 billion globally for supply chain optimization software')
    doc.add_paragraph('Serviceable Available Market (SAM): $8.5 billion in North America enterprise market')
    doc.add_paragraph('Serviceable Obtainable Market (SOM): $420 million addressable market in next 3 years')
    doc.add_paragraph('Market Growth Rate: 18% CAGR over next 5 years')
    doc.add_paragraph('Target Segments: Fortune 500 manufacturing companies, large retail chains, e-commerce platforms')
    
    doc.add_heading('Competitive Analysis', 2)
    doc.add_paragraph('Primary Competitors: SAP, Oracle, Blue Yonder, Kinaxis')
    doc.add_paragraph('Competitive Advantages:')
    doc.add_paragraph('  • AI-first architecture enabling real-time optimization', style='List Bullet')
    doc.add_paragraph('  • 40% average cost reduction vs. traditional solutions', style='List Bullet')
    doc.add_paragraph('  • Faster implementation (3 months vs. 12+ months for competitors)', style='List Bullet')
    doc.add_paragraph('  • Superior predictive accuracy (92% vs. industry average 78%)', style='List Bullet')
    
    doc.add_page_break()
    
    # Financial Details
    doc.add_heading('Financial Details', 1)
    doc.add_paragraph('Previous Funding Rounds:')
    doc.add_paragraph('  • Seed Round: $2.5 million raised in June 2023 at $8 million pre-money valuation', style='List Bullet')
    doc.add_paragraph('The total funding raised to date is $2.5 million.')
    doc.add_paragraph('Total Funding Raised: $2.5 million')
    doc.add_paragraph('The last valuation was $8 million in the Seed round completed on June 15, 2023.')
    doc.add_paragraph('Last Valuation: $8 million (Seed round, June 2023)')
    doc.add_paragraph('Current Round: Series A')
    doc.add_paragraph('The funding stage is Series A.')
    doc.add_paragraph('The investment ask is $8 million.')
    doc.add_paragraph('Investment Ask: $8 million')
    doc.add_paragraph('The current round size is $8 million.')
    doc.add_paragraph('Current Round Size: $8 million')
    doc.add_paragraph('Pre-Money Valuation: $24 million')
    doc.add_paragraph('Post-Money Valuation: $32 million')
    doc.add_paragraph('Use of Funds:')
    doc.add_paragraph('  • 40% ($3.2M) Sales and Marketing: Expand sales team, marketing campaigns, customer acquisition', style='List Bullet')
    doc.add_paragraph('  • 35% ($2.8M) Product Development: Enhance AI models, develop new features, platform improvements', style='List Bullet')
    doc.add_paragraph('  • 25% ($2.0M) Operations and Runway Buffer: Infrastructure scaling, working capital, operational expenses', style='List Bullet')
    
    doc.add_page_break()
    
    # Growth Metrics
    doc.add_heading('Growth Metrics', 1)
    doc.add_paragraph('Annual Recurring Revenue (ARR):')
    doc.add_paragraph('  • 2024: $2.4 million', style='List Bullet')
    doc.add_paragraph('  • 2025 (Projected): $4.8 million', style='List Bullet')
    doc.add_paragraph('  • 2026 (Projected): $9.6 million', style='List Bullet')
    doc.add_paragraph('Monthly Recurring Revenue (MRR): $200,000')
    doc.add_paragraph('Growth Rate Month-over-Month: 15%')
    doc.add_paragraph('Growth Rate Year-over-Year: 120%')
    doc.add_paragraph('Burn Rate: $180,000 per month')
    doc.add_paragraph('Runway: 18 months')
    doc.add_paragraph('Churn Rate: 3% (industry-leading, benchmark is 5-7%)')
    doc.add_paragraph('Customer Count: 45 enterprise customers')
    doc.add_paragraph('Customer Acquisition Cost (CAC): $12,000')
    doc.add_paragraph('Lifetime Value (LTV): $180,000')
    doc.add_paragraph('LTV:CAC Ratio: 15:1 (excellent, benchmark is 3:1)')
    
    doc.add_page_break()
    
    # Team Information
    doc.add_heading('Team Information', 1)
    
    doc.add_heading('Founders', 2)
    doc.add_paragraph('The founders are Sarah Chen and Michael Rodriguez.')
    doc.add_paragraph('Sarah Chen, CEO')
    doc.add_paragraph('  • Background: Former VP at Amazon Supply Chain, led team of 200+ engineers')
    doc.add_paragraph('  • Experience: 15 years in supply chain optimization')
    doc.add_paragraph('  • Past Exit: Sold logistics startup to Oracle for $50 million in 2019')
    doc.add_paragraph('  • Education: MBA from Wharton, BS Engineering from MIT')
    
    doc.add_paragraph('Michael Rodriguez, CTO')
    doc.add_paragraph('  • Background: Former Google AI researcher, expert in machine learning and distributed systems')
    doc.add_paragraph('  • Experience: 12 years in AI/ML research and development')
    doc.add_paragraph('  • Education: PhD in Computer Science from Stanford, published 30+ papers on optimization algorithms')
    
    doc.add_heading('Key Employees', 2)
    doc.add_paragraph('James Park, VP of Sales')
    doc.add_paragraph('  • Background: Former Director at Salesforce')
    doc.add_paragraph('  • Experience: 10 years in enterprise sales')
    
    doc.add_paragraph('Lisa Wang, VP of Engineering')
    doc.add_paragraph('  • Background: Former Engineering Manager at Microsoft')
    doc.add_paragraph('  • Experience: 12 years building enterprise software')
    
    doc.add_paragraph('David Kim, Head of Product')
    doc.add_paragraph('  • Background: Former Product Lead at Palantir')
    doc.add_paragraph('  • Experience: 8 years in enterprise AI products')
    
    doc.add_heading('Advisors', 2)
    doc.add_paragraph('Robert Thompson: Former CEO of FedEx Supply Chain')
    doc.add_paragraph('Jennifer Martinez: Partner at Andreessen Horowitz (a16z)')
    
    doc.add_heading('Board Members', 2)
    doc.add_paragraph('Sarah Chen (CEO), Michael Rodriguez (CTO), Lead investor from Seed round')
    
    doc.add_heading('Past Exits', 2)
    doc.add_paragraph('Sarah Chen sold previous logistics startup to Oracle for $50 million in 2019')
    
    doc.add_heading('Relevant Experience', 2)
    doc.add_paragraph('The team has combined 40+ years of relevant experience in supply chain optimization and AI/ML.')
    doc.add_paragraph('Relevant Experience: Combined 40+ years of experience in supply chain optimization and AI/ML')
    
    doc.save(os.path.join(output_dir, 'Nexus AI Diligence.docx'))
    print("✓ Created Diligence Document")

if __name__ == '__main__':
    print("Creating comprehensive mock data for Nexus AI...")
    print("=" * 60)
    create_investor_deck()
    create_financials_spreadsheet()
    create_email_chains()
    create_diligence_document()
    print("=" * 60)
    print("✓ All mock data created successfully!")
    print(f"Location: {output_dir}")



