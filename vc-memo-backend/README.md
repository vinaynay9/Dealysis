# VC Memo Backend - Quick Start Guide

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**

   ```bash
   echo 'OPENAI_API_KEY=your_openai_api_key_here' > .env
   ```

3. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Testing

1. **Server will be available at:**

   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

2. **Run the test script:**

   ```bash
   # In another terminal
   python -m tests.test_api
   ```

3. **Manual testing with curl:**

   ```bash
   # Upload files
   curl -X POST http://localhost:8000/upload-and-process \
     -F "company_name=TestCorp" \
     -F "funding_stage=Series A" \
     -F "files=@sample_pitch.txt" \
     -F "files=@sample_financials.txt"

   # Check status (use job_id from response)
   curl http://localhost:8000/status/{job_id}

   # Get memo
   curl http://localhost:8000/memo/{job_id}
   ```

## API Endpoints

- `POST /upload-and-process` - Upload documents and start processing
- `GET /status/{job_id}` - Check processing status
- `GET /memo/{job_id}` - Get completed memo
- `GET /memo/{job_id}/download` - Download memo as markdown
- `DELETE /job/{job_id}` - Delete a job
- `GET /health` - Health check

## Project Structure

```
vc-memo-backend/
├── app/
│   ├── api/          # API routes and endpoints
│   ├── core/         # Core configuration and models
│   ├── services/     # Business logic (extractors, pipeline, etc.)
│   └── utils/        # Utility functions (caching, rate limiting)
├── tests/            # Test files
├── mock-data/        # Sample data for testing
├── requirements.txt  # Python dependencies
└── render.yaml       # Deployment configuration
```

## Architecture

The system uses:

- **FastAPI** for the REST API
- **LangGraph** for orchestrating the memo generation pipeline
- **OpenAI GPT-4o/GPT-4o-mini** for information extraction and memo writing
- **Async processing** with background tasks for long-running operations
- **Caching** to reduce API costs and improve performance

The pipeline:

1. Parse documents using LangChain loaders (PDF, DOCX, XLSX, etc.)
2. Analyze financial files separately for metrics extraction
3. Extract information in parallel (company, financials, market, team, progress)
4. Generate memo sections based on template structure
5. Compile final investment memo with confidence scores and flagged items
