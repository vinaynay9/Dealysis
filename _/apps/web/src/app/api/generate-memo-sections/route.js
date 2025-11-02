/**
 * POST /api/generate-memo-sections
 * 
 * Generates a single memo section using AI based on uploaded documents.
 * 
 * This uses a "micro-prompt" approach where each section is generated
 * independently for better quality and citation accuracy.
 * 
 * @param {Request} request - JSON body with:
 *   - templateAnalysis: Array of example memo analyses (optional)
 *   - contentAnalyses: Array of document analyses with company info
 *   - additionalContext: String with additional company context
 *   - referenceTexts: Array of {label, content} text references
 *   - referenceUrls: Array of {label, url} URL references
 *   - sectionToGenerate: One of 8 section keys (executive_summary, etc.)
 * 
 * @returns {Promise<Response>} JSON with generated section content
 * 
 * Valid sections:
 * - executive_summary, company_overview, market_opportunity
 * - product_technology, competitive_landscape, traction_financials
 * - team_leadership, risks_recommendation
 * 
 * Features:
 * - Automatic citation numbering [1], [2], etc.
 * - Flags missing data with [⚠️ Analyst Input Required]
 * - Only uses information from provided context (no external data)
 * - Max context length: 20,000 characters (truncated if longer)
 */
export async function POST(request) {
  try {
    const {
      templateAnalysis,
      contentAnalyses,
      additionalContext,
      referenceTexts,
      referenceUrls,
      sectionToGenerate,
    } = await request.json();

    // Define the memo sections in order
    const memoSections = [
      "executive_summary",
      "company_overview",
      "market_opportunity",
      "product_technology",
      "competitive_landscape",
      "traction_financials",
      "team_leadership",
      "risks_recommendation",
    ];

    if (!sectionToGenerate || !memoSections.includes(sectionToGenerate)) {
      return Response.json(
        {
          error:
            "Invalid section specified. Must be one of: " +
            memoSections.join(", "),
        },
        { status: 400 },
      );
    }

    // Create focused prompt for the specific section
    const sectionPrompts = {
      executive_summary: {
        title: "Executive Summary",
        prompt: `Create a comprehensive Executive Summary section following this EXACT structure:

## Executive Summary

### Overview
Write 2-3 detailed paragraphs (5-8 sentences each) covering:
- Company description and core value proposition
- Business model and market position
- Current stage and key achievements

### Market Opportunity
- Total addressable market size with specific figures
- Market timing and growth drivers
- Key customer segments and pain points

### Traction & Financial Highlights  
- Revenue metrics and growth rates
- User/customer acquisition data
- Funding history and runway

### Investment Thesis
- Core investment rationale in 2-3 bullet points
- Expected returns and timeline
- Strategic value proposition

### Risk/Return Overview
- Primary risk factors
- Risk mitigation strategies
- Expected return profile

REQUIREMENTS:
- Each subsection must have at least 2 substantial paragraphs
- Flag missing data with "[⚠️ Analyst Input Required]"
- Use specific numbers and data points ONLY from provided context
- No assumptions without evidence - flag gaps in square brackets
- **CITATIONS REQUIRED**: Use in-text citations [1], [2], etc. when referencing specific data from provided materials
- Only reference data that exists in the provided context materials
- Do NOT use external market data or industry knowledge not provided`,
      },
      company_overview: {
        title: "Company Overview",
        prompt: `Create a comprehensive Company Overview section following this EXACT structure:

## Company Overview

### Background and Founding Story
Write 2-3 detailed paragraphs covering:
- Company founding date, location, and founding circumstances
- Founder backgrounds and motivation
- Early milestones and pivot history

### Mission and Vision
- Clear mission statement
- Long-term vision and strategic goals
- Core values and company culture

### Business Model and Revenue Streams
- Primary revenue model(s) with specifics
- Customer acquisition strategy
- Unit economics and pricing strategy
- Revenue diversification plans

### Major Milestones and Current Stage
- Key product launches and partnerships
- Funding rounds and investor relationships  
- Geographic expansion and market entry
- Team growth and organizational development

### Operations and Legal Structure
- Corporate structure and jurisdiction
- Key operational facilities and locations
- Legal considerations and regulatory status
- [⚠️ Analyst Input Required] if information is missing

REQUIREMENTS:
- Each subsection must have at least 2 substantial paragraphs
- Include specific dates, figures, and metrics
- Flag assumptions with "[⚠️ Analyst Input Required]"`,
      },
      market_opportunity: {
        title: "Market Opportunity",
        prompt: `Create a detailed Market Opportunity section following this EXACT structure:

## Market Opportunity

### Total Addressable Market (TAM/SAM/SOM)
Write 2-3 detailed paragraphs covering:
- Total Addressable Market size with methodology
- Serviceable Addressable Market calculations
- Serviceable Obtainable Market projections
- Market sizing sources and assumptions

### Market Dynamics and Growth Drivers
- Historical market growth rates and trends
- Key catalysts driving market expansion
- Technology adoption curves and inflection points
- Regulatory changes and policy impacts

### Target Customer Segments
- Primary customer personas with specific characteristics
- Customer pain points and unmet needs
- Willingness to pay and budget allocation
- Decision-making processes and buying patterns

### Market Timing and Competitive Window
- Why now is the right time for this solution
- Market readiness indicators
- Competitive landscape maturity
- Barriers to entry and switching costs

### Regulatory Environment
- Current regulatory framework
- Pending legislation or policy changes
- Compliance requirements and costs
- [⚠️ Analyst Input Required] for regulatory assumptions

REQUIREMENTS:
- Include specific market size figures with sources
- Cite industry reports and analyst commentary where possible
- Flag subjective assessments with "[⚠️ Analyst Input Required]"`,
      },
      product_technology: {
        title: "Product & Technology",
        prompt: `Create a thorough Product & Technology section following this EXACT structure:

## Product & Technology

### Core Product Features and Functionality
Write 2-3 detailed paragraphs covering:
- Primary product features and user experience
- Key workflows and use cases
- Platform capabilities and integrations
- User interface and design philosophy

### Technology Architecture and Stack
- Core technology infrastructure and architecture
- Programming languages, frameworks, and tools
- Data storage and processing capabilities
- Security and compliance measures
- [DIAGRAM PLACEHOLDER: Technology Architecture]

### Technical Differentiation and Innovation
- Unique technical advantages over competitors
- Proprietary algorithms, models, or processes
- Performance benchmarks and scalability metrics
- Research and development focus areas

### Product Roadmap and Development Pipeline
- Near-term feature releases (6-12 months)
- Medium-term platform expansion (1-2 years)
- Long-term vision and strategic initiatives
- Resource allocation and development priorities

### Intellectual Property and Competitive Moats
- Patents filed, pending, or granted
- Trade secrets and proprietary knowledge
- Technical barriers to replication
- [⚠️ Analyst Input Required] for IP verification

REQUIREMENTS:
- Include technical specifications where available
- Flag assumptions about proprietary technology
- Highlight competitive advantages with evidence`,
      },
      competitive_landscape: {
        title: "Competitive Landscape",
        prompt: `Create a comprehensive Competitive Landscape section following this EXACT structure:

## Competitive Landscape

### Direct Competitors Analysis
Write 2-3 detailed paragraphs covering:
- Primary direct competitors with market positions
- Feature comparison and product differentiation
- Market share estimates and competitive dynamics
- Pricing strategies and go-to-market approaches

### Indirect Competitors and Substitutes  
- Alternative solutions and workarounds
- Adjacent markets and potential entrants
- Substitute products and legacy approaches
- Threat assessment from substitutes

### Competitive Positioning Matrix
[VISUAL PLACEHOLDER: Competitive Positioning Chart]
- Market position along key dimensions
- Competitive advantages and disadvantages
- White space and market gaps
- Strategic positioning rationale

### Barriers to Entry and Switching Costs
- Technical barriers for new entrants
- Customer switching costs and lock-in
- Network effects and scale advantages
- Regulatory or compliance barriers

### Strategic Competitive Response
- Competitive threats and risk mitigation
- Defensive moats and differentiation strategy
- Potential competitive responses to market moves
- [⚠️ Analyst Input Required] for competitive intelligence

REQUIREMENTS:
- Include specific competitor analysis with evidence
- Avoid speculation without market data
- Flag subjective competitive assessments`,
      },
      traction_financials: {
        title: "Traction & Financials",
        prompt: `Create a detailed Traction & Financials section following this EXACT structure:

## Traction & Financials

### Revenue Growth and Key Metrics
Write 2-3 detailed paragraphs covering:
- Historical revenue growth with specific figures
- Revenue breakdown by product line/geography
- Recurring vs. one-time revenue analysis
- Revenue quality and sustainability metrics

### Customer Acquisition and Retention
- Customer acquisition cost (CAC) trends
- Customer lifetime value (LTV) calculations
- Churn rates and retention analysis
- User engagement and usage metrics

### Customer Concentration and Cohort Analysis
- Top customer concentration risks
- Customer cohort behavior and trends
- Average contract values and deal sizes
- Sales cycle length and conversion rates

### Unit Economics and Path to Profitability
- Gross margins by product/service
- Operating leverage and scalability
- Cash burn rate and runway analysis
- Break-even projections and assumptions

### Funding History and Capital Efficiency
- Previous funding rounds with terms
- Use of capital and milestone achievement
- Investor composition and board structure
- Future funding requirements and timeline

### Financial Projections and Key Assumptions
- Revenue projections (3-5 years)
- Expense scaling and operational metrics
- Cash flow projections and working capital
- [⚠️ Analyst Input Required] for projection assumptions

REQUIREMENTS:
- Include specific financial metrics and growth rates
- Cite data sources and calculation methodologies
- Flag assumptions in financial modeling`,
      },
      team_leadership: {
        title: "Team & Leadership",
        prompt: `Create a comprehensive Team & Leadership section following this EXACT structure:

## Team & Leadership

### Founder Backgrounds and Experience
Write 2-3 detailed paragraphs covering:
- Founder education, career history, and domain expertise
- Previous startup experience and track record
- Industry relationships and network strength
- Leadership philosophy and management style

### Key Team Members and Expertise
- C-level executives and their backgrounds
- Core technical and operational leaders
- Advisory board composition and involvement
- Key hires and talent pipeline

### Organizational Structure and Culture
- Reporting structure and decision-making processes
- Company culture and values in practice
- Remote vs. in-person work policies
- Performance management and compensation philosophy

### Team Gaps and Hiring Plans
- Critical roles to be filled
- Talent acquisition strategy and timeline
- Geographic expansion of team
- Retention strategies and equity programs

### Equity Distribution and Alignment
- Founder equity split and vesting schedules
- Employee stock option pool size
- Investor board representation
- [⚠️ Analyst Input Required] for equity details

### Strategic Relationships and Partnerships
- Key advisor relationships and value-add
- Strategic investor involvement
- Industry partnerships and collaborations
- Board composition and governance

REQUIREMENTS:
- Verify founder and team credentials where possible
- Include specific experience and achievement details
- Flag unverified background information`,
      },
      risks_recommendation: {
        title: "Key Risks & Investment Recommendation",
        prompt: `Create a thorough Key Risks & Investment Recommendation section following this EXACT structure:

## Key Risks & Investment Recommendation

### Major Risk Factors and Assessment
Write 2-3 detailed paragraphs covering:
- Market risks and demand uncertainty
- Competitive risks and market position threats
- Execution risks and operational challenges
- Technology risks and development uncertainties
- Regulatory and compliance risks
- Team and management risks

### Risk Mitigation Strategies
- Management's approach to each major risk
- Contingency plans and alternative strategies
- Risk monitoring and early warning systems
- Insurance and hedging strategies where applicable

### Scenario Analysis
**Bull Case (30% probability)**
- Best-case revenue and market outcomes
- Key success factors and catalysts
- Expected returns and exit scenarios

**Base Case (50% probability)**  
- Most likely performance trajectory
- Moderate growth and market capture
- Realistic return expectations

**Bear Case (20% probability)**
- Downside scenarios and value preservation
- Risk factors materializing
- Downside protection and mitigation

### Investment Terms and Valuation Framework
- Proposed investment amount and ownership
- Valuation methodology and comparables
- Liquidation preferences and investor rights
- [⚠️ Analyst Input Required] for specific terms

### Exit Strategy and Return Potential
- Potential exit pathways (IPO, acquisition, etc.)
- Expected timeline to exit
- Comparable transactions and multiples
- Return projections and risk-adjusted analysis

### Final Investment Recommendation
**RECOMMENDATION: [INVEST/PASS/FURTHER DUE DILIGENCE]**
- Clear investment thesis and rationale
- Key investment highlights
- Critical due diligence items to resolve
- [⚠️ Analyst Input Required] for subjective judgments

REQUIREMENTS:
- Provide balanced risk assessment with evidence
- Flag subjective investment opinions clearly
- Include specific return projections with methodology`,
      },
    };

    const currentSection = sectionPrompts[sectionToGenerate];

    // Compile context for this section
    let contextContent = "";
    let sourceIndex = 1;
    const sourceMap = new Map(); // Track sources for citation numbering

    // Add template guidance if available
    if (templateAnalysis && templateAnalysis.length > 0) {
      contextContent += "TEMPLATE STRUCTURE GUIDANCE:\n\n";
      templateAnalysis.forEach((template) => {
        contextContent += `Template from ${template.fileName}:\n${template.analysis}\n\n`;
      });
    }

    // Add content analyses with source tracking
    if (contentAnalyses && contentAnalyses.length > 0) {
      contextContent += "ANALYZED COMPANY INFORMATION:\n\n";
      contentAnalyses.forEach((analysis) => {
        sourceMap.set(analysis.fileName, sourceIndex);
        contextContent += `Source [${sourceIndex}] - ${analysis.fileName}:\n${analysis.analysis}\n\n`;
        sourceIndex++;
      });
    }

    // Add reference texts with source tracking
    if (referenceTexts && referenceTexts.length > 0) {
      contextContent += "REFERENCE MATERIALS:\n\n";
      referenceTexts.forEach((text) => {
        sourceMap.set(text.label, sourceIndex);
        contextContent += `Source [${sourceIndex}] - ${text.label}:\n${text.content}\n\n`;
        sourceIndex++;
      });
    }

    // Add reference URLs with source tracking
    if (referenceUrls && referenceUrls.length > 0) {
      contextContent += "REFERENCE URLS:\n\n";
      referenceUrls.forEach((url) => {
        sourceMap.set(url.label, sourceIndex);
        contextContent += `Source [${sourceIndex}] - ${url.label}: ${url.url}\n\n`;
        sourceIndex++;
      });
    }

    // Add additional context
    if (additionalContext) {
      contextContent += `ADDITIONAL CONTEXT:\n${additionalContext}\n\n`;
    }

    // Create source citation guide
    let citationGuide = "\n\nSOURCE CITATION GUIDE:\n";
    sourceMap.forEach((number, source) => {
      citationGuide += `[${number}] = ${source}\n`;
    });
    contextContent += citationGuide;

    // Limit context size to prevent overload (max 20k chars)
    const maxContextLength = 20000;
    if (contextContent.length > maxContextLength) {
      contextContent =
        contextContent.substring(0, maxContextLength) +
        "\n\n[Context truncated to prevent overload]";
    }

    try {
      console.log(`Generating section: ${currentSection.title}`);

      const aiResponse = await fetch(
        "/integrations/chat-gpt/conversationgpt4",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: [
              {
                role: "system",
                content: `You are an expert venture capital analyst specializing in investment memo creation. Generate professional, well-structured memo sections that are comprehensive yet concise. 

CRITICAL INSTRUCTIONS:
- ONLY use information provided in the user context materials
- DO NOT use any external knowledge, online research, or general industry data
- DO NOT make assumptions about market sizes, competitor data, or industry trends unless explicitly provided
- If specific data is missing, clearly mark it as "[⚠️ Analyst Input Required]"
- Flag all missing information gaps rather than filling them with general knowledge
- NEVER cite external sources not provided in the context
- When referencing data, only cite the specific materials provided in the context
- Do not add commentary on market trends unless supported by the provided materials
- Stick strictly to what can be verified from the uploaded documents and context

Your role is to structure and analyze ONLY the information provided, not to supplement it with external research.`,
              },
              {
                role: "user",
                content: `Create the "${currentSection.title}" section for an investment memo.

${currentSection.prompt}

Use this context to inform your analysis:

${contextContent}

CRITICAL CITATION REQUIREMENTS:
- **MANDATORY CITATIONS**: Every factual statement, figure, quote, or data point MUST include a citation [1], [2], etc.
- Use the source numbers provided in the context above
- Examples: "The company achieved $2.5M in ARR [1]" or "According to the pitch deck, the market size is $50B [2]"
- Do NOT write any facts without citations - this is a professional investment document
- If you cannot find a source for a statement, mark it as "[⚠️ Analyst Input Required - Source needed]"

STRICT REQUIREMENTS:
- Only analyze and reference information provided in the context above
- Every data point, metric, or factual claim MUST have a citation [X]
- If information is not provided in the context, mark it as "[⚠️ Analyst Input Required]"
- Do not use external industry knowledge, market data, or general business information
- Do not make assumptions about market conditions, competitor performance, or industry benchmarks
- Focus on structuring and presenting ONLY the data and insights provided to you with proper citations

Write this section in a professional, analytical tone suitable for institutional investors. Cite sources for every factual statement using the bracketed numbers provided in the source guide above.`,
              },
            ],
          }),
        },
      );

      if (!aiResponse.ok) {
        const errorText = await aiResponse.text();
        console.error("ChatGPT section generation error:", errorText);

        if (aiResponse.status === 429) {
          throw new Error(
            "AI service is temporarily busy. Please try again in a moment.",
          );
        } else {
          throw new Error(
            `Section generation failed (${aiResponse.status}): ${errorText.substring(0, 200)}`,
          );
        }
      }

      const aiResult = await aiResponse.json();

      if (
        !aiResult.choices ||
        !aiResult.choices[0] ||
        !aiResult.choices[0].message
      ) {
        throw new Error("Invalid response from AI service. Please try again.");
      }

      const sectionContent = aiResult.choices[0].message.content;

      return Response.json({
        success: true,
        section: sectionToGenerate,
        title: currentSection.title,
        content: sectionContent,
        timestamp: new Date().toISOString(),
        contextLength: contextContent.length,
      });
    } catch (error) {
      console.error(`Error generating section ${sectionToGenerate}:`, error);
      return Response.json(
        {
          error: `Failed to generate ${currentSection.title}: ${error.message}`,
          section: sectionToGenerate,
        },
        { status: 500 },
      );
    }
  } catch (error) {
    console.error("Error in section generation:", error);
    return Response.json(
      {
        error: `Section generation failed: ${error.message}`,
        details: error.stack?.substring(0, 500),
      },
      { status: 500 },
    );
  }
}
