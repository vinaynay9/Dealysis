# OpenAI API Call Structure Analysis

---

## 🚨 IMMEDIATE ACTION REQUIRED

Your `insufficient_quota` error is due to **hitting your OpenAI account spending limit**, not just rate limits.

### Quick Fixes (Choose One):

**Option A: Increase Your OpenAI Quota (Fastest)**

1. Go to https://platform.openai.com/settings/organization/billing
2. Check your current usage and spending limit
3. Increase your monthly budget or upgrade to a higher tier
4. Typical needs: $50/month for light usage, $200/month for moderate usage

**Option B: Reduce API Calls Immediately (No cost)**

1. Edit `app/services/document_parser.py` line 32: Change `chunk_size=1200` to `chunk_size=3000`
2. Edit `app/services/extractors.py` line 196: Change `self.max_concurrent = 4` to `self.max_concurrent = 2`
3. This will reduce API calls by ~60-70%

**Option C: Switch to Cheaper Models (Temporary relief)**

1. Edit `app/services/extractors.py` line 174: Change `ChatOpenAI(model="gpt-4o"` to `ChatOpenAI(model="gpt-4o-mini"`
2. This makes all extractions use the cheaper model (5x less expensive)
3. May reduce accuracy slightly

---

## Overview

This document outlines the OpenAI API call pattern for a single job processing documents through the VC memo pipeline.

## Problem Identified

**You're hitting quota limits because the extraction phase makes 5x the number of document chunks in API calls!**

## Visual Call Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         JOB STARTS: Upload 4 Files                       │
│                     (Pitch Deck, Email Chain, Diligence, Financials)    │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: DOCUMENT PARSING (0 API calls)                                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│  • Parse PDFs, DOCX, XLSX using LangChain loaders                       │
│  • Split into chunks: 1,200 chars, 200 overlap                          │
│  • Output: 50 chunks (example)                                           │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: FINANCIAL ANALYSIS (0 API calls)                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│  • Pandas-based Excel/CSV analysis                                       │
│  • Calculate ARR, runway, growth rates                                   │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  🔥 STAGE 3: EXTRACTION (250 API calls) 🔥                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                                           │
│  Run 5 extractors IN PARALLEL:                                           │
│                                                                           │
│  ┌─────────────────────┐                                                 │
│  │  PROGRESS Extractor │ ──→ Process ALL 50 chunks                      │
│  │  (gpt-4o)          │     └→ 50 API calls × ~3,400 tokens each       │
│  └─────────────────────┘        = 170,000 tokens                        │
│           │                                                               │
│  ┌─────────────────────┐                                                 │
│  │ FINANCIAL Extractor │ ──→ Process ALL 50 chunks                      │
│  │  (gpt-4o)          │     └→ 50 API calls × ~3,400 tokens each       │
│  └─────────────────────┘        = 170,000 tokens                        │
│           │                                                               │
│  ┌─────────────────────┐                                                 │
│  │  MARKET Extractor   │ ──→ Process ALL 50 chunks                      │
│  │  (gpt-4o-mini)     │     └→ 50 API calls × ~2,800 tokens each       │
│  └─────────────────────┘        = 140,000 tokens                        │
│           │                                                               │
│  ┌─────────────────────┐                                                 │
│  │  COMPANY Extractor  │ ──→ Process ALL 50 chunks                      │
│  │  (gpt-4o-mini)     │     └→ 50 API calls × ~2,800 tokens each       │
│  └─────────────────────┘        = 140,000 tokens                        │
│           │                                                               │
│  ┌─────────────────────┐                                                 │
│  │   TEAM Extractor    │ ──→ Process ALL 50 chunks                      │
│  │  (gpt-4o-mini)     │     └→ 50 API calls × ~2,800 tokens each       │
│  └─────────────────────┘        = 140,000 tokens                        │
│                                                                           │
│  • Concurrency: 4 requests at a time per extractor                       │
│  • Total Time: ~3-5 minutes (with rate limiting)                         │
│  • Total Tokens: ~760,000 tokens                                         │
│                                                                           │
│  ⚠️  THE PROBLEM: Every extractor processes EVERY chunk!                 │
│      Even chunks with no relevant information.                           │
│                                                                           │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: MEMO GENERATION (8 API calls)                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                                           │
│  Generate 8 sections SEQUENTIALLY (500ms delay between):                 │
│                                                                           │
│  1. Executive Summary    ──→ gpt-4o call (~3,300 tokens)                │
│         ↓ 500ms delay                                                     │
│  2. Company Overview     ──→ gpt-4o call (~3,800 tokens)                │
│         ↓ 500ms delay                                                     │
│  3. Market Opportunity   ──→ gpt-4o call (~4,100 tokens)                │
│         ↓ 500ms delay                                                     │
│  4. Progress & Metrics   ──→ gpt-4o call (~3,800 tokens)                │
│         ↓ 500ms delay                                                     │
│  5. Financial Overview   ──→ gpt-4o call (~3,200 tokens)                │
│         ↓ 500ms delay                                                     │
│  6. Management Team      ──→ gpt-4o call (~3,200 tokens)                │
│         ↓ 500ms delay                                                     │
│  7. Thesis & Risks      ──→ gpt-4o call (~3,800 tokens)                │
│         ↓ 500ms delay                                                     │
│  8. Recommendation      ──→ gpt-4o call (~2,800 tokens)                │
│                                                                           │
│  • Total Time: ~8-20 seconds                                              │
│  • Total Tokens: ~26,400 tokens                                          │
│                                                                           │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          MEMO COMPLETE                                   │
│                                                                           │
│  📊 Total API Calls: 258                                                 │
│  📊 Total Tokens: ~786,400                                               │
│  ⏱️  Total Time: ~4-6 minutes                                            │
│  💰 Estimated Cost:                                                       │
│     • gpt-4o: ~$2.00 (356K tokens)                                       │
│     • gpt-4o-mini: ~$0.06 (420K tokens)                                  │
│     • Total: ~$2.06 per job                                              │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

🚨 KEY INSIGHT: 97% of API calls happen in the extraction stage!
   (250 extraction calls vs 8 memo generation calls)
```

---

## Pipeline Stages

### 1. Document Parsing Stage

- **OpenAI API Calls**: `0`
- **Operations**: LangChain loaders parse documents and split into chunks
- **Chunk Configuration**:
  - Target size: 1,200 characters
  - Overlap: 200 characters
  - **Typical Output**: 20-100+ chunks (varies by document size)

---

### 2. Financial File Analysis Stage

- **OpenAI API Calls**: `0`
- **Operations**: Pandas-based analysis of Excel/CSV files
- **No LLM usage** - pure numerical analysis

---

### 3. **🔥 EXTRACTION STAGE (HEAVY API USAGE) 🔥**

This is where the quota problem occurs!

#### Call Structure

For **EACH** extraction type, the system processes **ALL** chunks:

```
Extraction Types (5 total):
├── progress      → processes ALL chunks → gpt-4o (critical)
├── financial     → processes ALL chunks → gpt-4o (critical)
├── market        → processes ALL chunks → gpt-4o-mini
├── company       → processes ALL chunks → gpt-4o-mini
└── team          → processes ALL chunks → gpt-4o-mini
```

#### Example with 50 Chunks:

```
Total API Calls = 5 extraction types × 50 chunks = 250 API calls
```

#### Concurrency Settings:

- **Max concurrent requests**: 4 (set in extractors.py line 196)
- All 5 extraction types run in **parallel** (async gather)
- Within each type, chunks processed with **semaphore limit of 4**

#### Token Usage Per Call:

**Input Tokens (Prompt + Chunk Content):**

- Critical types (progress, financial): Up to **4,000 tokens** per chunk
- Non-critical types (market, company, team): Up to **3,000 tokens** per chunk
- Average realistic input: ~2,000-3,000 tokens per call

**Output Tokens (JSON Response):**

- Typical: **200-500 tokens** per response
- Format: Structured JSON with extracted fields

#### Models Used:

- `gpt-4o` for critical extractions (progress, financial)
- `gpt-4o-mini` for non-critical (market, company, team)

#### Estimated Token Usage (50 chunks example):

```
Progress:   50 calls × 3,000 input + 400 output = 170,000 tokens (gpt-4o)
Financial:  50 calls × 3,000 input + 400 output = 170,000 tokens (gpt-4o)
Market:     50 calls × 2,500 input + 300 output = 140,000 tokens (gpt-4o-mini)
Company:    50 calls × 2,500 input + 300 output = 140,000 tokens (gpt-4o-mini)
Team:       50 calls × 2,500 input + 300 output = 140,000 tokens (gpt-4o-mini)
────────────────────────────────────────────────────────────────────
Total Input:  ~650,000 tokens
Total Output: ~85,000 tokens
Total:        ~735,000 tokens for extraction phase alone!
```

#### Caching:

- **Only non-critical types** (market, company, team) are cached
- **Critical types** (progress, financial) are NEVER cached (line 208 in extractors.py)
- Cache uses SQLite (`cache/summary_cache.db`)

---

### 4. Memo Generation Stage

#### Call Structure:

```
8 sections (from template_standard.yaml):
1. Executive Summary      → 1 call to gpt-4o
2. Company Overview       → 1 call to gpt-4o
3. Market Opportunity     → 1 call to gpt-4o
4. Progress & Metrics     → 1 call to gpt-4o
5. Financial Overview     → 1 call to gpt-4o
6. Management Team        → 1 call to gpt-4o
7. Thesis & Risks        → 1 call to gpt-4o
8. Recommendation        → 1 call to gpt-4o

Total: 8 API calls
```

#### Processing Pattern:

- **Sequential execution** (not parallel)
- **500ms delay** between sections (line 66 in memo_generator.py)
- Total generation time: ~8-20 seconds (depends on response times)

#### Token Usage Per Call:

**Input Tokens:**

- Prompt template: ~800 tokens
- Extracted data (formatted): 1,000-3,000 tokens
- **Average input**: ~2,000-3,000 tokens per section

**Output Tokens:**

- Varies by section (1-4 paragraphs)
- Executive Summary: ~300-600 tokens
- Company Overview: ~600-1,200 tokens
- Market Opportunity: ~800-1,600 tokens
- Progress & Metrics: ~800-1,200 tokens
- Financial Overview: ~400-800 tokens
- Team: ~400-800 tokens
- Thesis & Risks: ~800-1,200 tokens
- Recommendation: ~300-500 tokens
- **Average output**: ~700-1,000 tokens per section

#### Estimated Token Usage (8 sections):

```
8 sections × (2,500 input + 800 output) = 26,400 tokens (gpt-4o)

Total Input:  ~20,000 tokens
Total Output: ~6,400 tokens
Total:        ~26,400 tokens for memo generation
```

---

## Total API Call Summary (Per Job)

### For a typical document set (50 chunks):

| Stage               | API Calls     | Models                                        | Total Tokens        |
| ------------------- | ------------- | --------------------------------------------- | ------------------- |
| **Extraction**      | **250 calls** | gpt-4o (100 calls)<br>gpt-4o-mini (150 calls) | **~735,000 tokens** |
| **Memo Generation** | **8 calls**   | gpt-4o (8 calls)                              | **~26,400 tokens**  |
| **TOTAL**           | **258 calls** |                                               | **~761,400 tokens** |

### Token Distribution:

```
gpt-4o:       ~356,400 tokens (108 calls)
  - Extraction: ~340,000 tokens (100 calls)
  - Generation: ~26,400 tokens (8 calls)

gpt-4o-mini:  ~420,000 tokens (150 calls)
  - Extraction: ~420,000 tokens (150 calls)
```

---

## Why You're Hitting Quota Limits

### Root Cause:

**Every extraction type processes ALL chunks independently**

If you upload:

- 4 documents (typical for a deal)
- Average 12-15 chunks per document = ~50 chunks
- Result: **250 extraction API calls** + 8 generation calls = **258 total calls**

### With Larger Document Sets:

- 10 documents × 10 chunks = 100 chunks
- Result: **500 extraction calls** + 8 = **508 total calls**
- Token usage: **~1.5 million tokens**

### API Rate Limits (OpenAI):

- **Free tier**: 3 RPM (requests per minute), 40K TPM (tokens per minute)
- **Tier 1** ($5 spent): 500 RPM, 200K TPM
- **Tier 2** ($50 spent): 5,000 RPM, 2M TPM

**Your current concurrency (4) would hit:**

- 4 concurrent × 3,000 tokens = **12,000 tokens in flight**
- With 250 calls, you need multiple minutes even with good quota
- If quota is insufficient_quota, you're hitting **account spend limits**

---

## Optimization Recommendations

### 1. **Reduce Redundant Chunk Processing** ⭐ BIGGEST WIN

Currently each extraction type processes ALL chunks. Instead:

- Use semantic routing to send chunks only to relevant extractors
- Financial chunks → only financial extractor
- Team chunks → only team extractor
- Could reduce calls by **60-70%**

### 2. **Use Batch API for Extraction**

- OpenAI Batch API is 50% cheaper
- Trade-off: 24h turnaround instead of real-time
- Could reduce costs by 50%

### 3. **Smarter Chunking**

- Current: 1,200 char chunks (very small)
- Increase to 3,000-4,000 char chunks
- Could reduce chunk count by **60-70%**
- Example: 50 chunks → 15-20 chunks = **75-100 API calls total** instead of 250

### 4. **Enable Caching for Critical Types**

- Currently financial/progress extractions are NOT cached
- First run is expensive, but reruns would be free
- Trade-off: need cache invalidation strategy

### 5. **Use Claude or Gemini for Extraction**

- Claude 3.5 Haiku: 5x cheaper than gpt-4o-mini
- Gemini 1.5 Flash: 10x cheaper
- Keep gpt-4o for memo generation only

### 6. **Reduce Max Concurrent Requests**

- Current: 4 concurrent
- Lower to 2-3 to stay under rate limits
- Slower but won't hit quota errors

### 7. **Implement Proper Quota Monitoring**

- Track token usage per job
- Alert when approaching limits
- Queue jobs when quota is low

---

## Immediate Fix for Your Current Issue

Your error message indicates **insufficient_quota**, not rate limiting. This means:

**You've hit your account spending limit!**

### Steps to Fix:

1. **Check billing**: Go to OpenAI Platform → Billing → Usage
2. **Increase spending limit**: Settings → Limits → Adjust monthly budget
3. **Or upgrade tier**: Make a $5-50 payment to move to higher tier

### Temporary Workaround:

1. Reduce `max_concurrent` from 4 to 2 in `extractors.py`
2. Increase chunk size to 3,000 characters in `document_parser.py`
3. This will 2-3x reduce your API calls immediately

---

## Code References

### Extraction Configuration:

- `extractors.py` line 196: `self.max_concurrent = 4`
- `extractors.py` line 177: Model selection (gpt-4o vs gpt-4o-mini)
- `extractors.py` line 232: Token limits (3000-4000)
- `extractors.py` line 208: Cache bypass for critical types

### Chunk Configuration:

- `document_parser.py` line 32: `chunk_size: int = 1200`
- `document_parser.py` line 33: `chunk_overlap: int = 200`

### Rate Limiting:

- `rate_limiter.py` line 188: `RateLimiter` class with retry logic
- `rate_limiter.py` line 25: `_min_request_interval = 0.1` (100ms between requests)

### Memo Generation:

- `memo_generator.py` line 66: `await asyncio.sleep(0.5)` (500ms delay)
- `memo_generator.py` line 30: Model = gpt-4o (from config.py line 30)

---

## Questions to Consider

1. **What's your OpenAI tier?** (Check platform.openai.com/settings/organization/limits)
2. **What's your monthly spend limit?** (This is causing insufficient_quota)
3. **How many jobs per day do you expect?** (To calculate if current approach is sustainable)
4. **Is real-time response required?** (If not, batch API could save 50% cost)
5. **Do you need all 5 extraction types for every chunk?** (Probably not - biggest optimization)
