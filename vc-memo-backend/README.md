# VC Memo Backend - Quick Start Guide

## Setup

1. **Create a virtual environment (recommended):**

   ```bash
   # Create venv
   python3 -m venv venv

   # Activate it
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   ```bash
   cp env.example .env
   # Then edit .env and add your OPENAI_API_KEY
   ```

4. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## CLI Tool

Generate memos directly from the terminal:

```bash
python -m app.cli generate-memo \
  --files path/to/deck.pdf path/to/financials.xlsx \
  --company-name "Zinnia" \
  --funding-stage "Series A" \
  --output memo_zinnia.md
```

**Options:**

- `--files`: File paths (can specify multiple times)
- `--company-name`: Company name (required)
- `--funding-stage`: Funding stage (required)
- `--template`: Optional template file path
- `--output`: Output file path (default: `memo_{company}_{timestamp}.md`)
- `--no-file`: Disable file output, show in terminal only

The CLI shows real-time progress and saves results to a markdown file by default.

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

## Ollama Integration (Optional)

The system automatically detects and uses Ollama for non-critical extractions to reduce costs:

- **Automatic Detection**: Checks Ollama status on app startup
- **Cost Savings**: Non-critical extractions (market, team, company) use Ollama (free)
- **Fallback**: Automatically uses OpenAI if Ollama is unavailable
- **Storage**: ~2GB required for llama3.2:3b model
- **Auto-Setup**: Can automatically install and configure Ollama for testing

**Manual Setup (optional):**

```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# Download model (in another terminal)
ollama pull llama3.2:3b
```

**Auto-Setup (for testing/development):**

The backend can automatically set up Ollama on startup. Add to your `.env`:

```bash
# Auto-configure Ollama (start service, download model if needed)
OLLAMA_AUTO_SETUP=true

# Also install Ollama via Homebrew if not found (requires Homebrew)
OLLAMA_AUTO_INSTALL=true
```

When `OLLAMA_AUTO_SETUP=true`, the backend will:

1. Check if Ollama is installed
2. Start the Ollama service if needed
3. Download the model if missing

The app will log Ollama status on startup. If not available, it will use OpenAI for all extractions.

## Architecture

The system uses:

- **FastAPI** for the REST API
- **LangGraph** for orchestrating the memo generation pipeline
- **OpenAI GPT-4o/GPT-4o-mini** for information extraction and memo writing
- **Ollama** (optional) for non-critical extractions to reduce costs
- **Async processing** with background tasks for long-running operations
- **Caching** to reduce API costs and improve performance

The pipeline:

1. Parse documents using LangChain loaders (PDF, DOCX, XLSX, etc.)
2. Analyze financial files separately for metrics extraction
3. Extract information in parallel (company, financials, market, team, progress)
4. Generate memo sections based on template structure
5. Compile final investment memo with confidence scores and flagged items
