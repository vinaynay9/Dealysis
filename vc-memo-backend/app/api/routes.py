from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime
from app.services.pipeline.pipeline import run_memo_pipeline
from app.core.models import JobStatus
from app.services.generation.template_parser import TemplateParser

router = APIRouter()

# In-memory job storage (replace with Redis/DB in production)
jobs: Dict[str, dict] = {}


@router.post("/upload-and-process")
async def upload_and_process(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(
        ..., description="Deal documents (PDF, DOCX, PPTX, TXT, MD, XLSX, XLS, CSV)"
    ),
    company_name: str = Form(...),
    funding_stage: str = Form(...),
    template_file: Optional[UploadFile] = File(
        None,
        description="Optional: Template memo (PDF/DOCX/TXT/MD/YAML) to extract structure from",
    ),
):
    """Upload deal documents and start memo generation"""

    # Validate files
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files allowed")

    job_id = str(uuid.uuid4())

    try:
        # Process uploaded files
        documents = []
        total_size = 0

        for file in files:
            content = await file.read()
            file_size = len(content)
            total_size += file_size

            # Limit individual file size to 50MB (VC pitch decks can be large)
            if file_size > 50 * 1024 * 1024:
                raise HTTPException(
                    status_code=400, detail=f"File {file.filename} exceeds 50MB limit"
                )

            documents.append(
                {
                    "filename": file.filename,
                    "content": content,
                    "content_type": file.content_type or "application/octet-stream",
                }
            )

        # Limit total upload to 200MB (to accommodate multiple large documents)
        if total_size > 200 * 1024 * 1024:
            raise HTTPException(
                status_code=400, detail="Total upload exceeds 200MB limit"
            )

        # Initialize job first
        jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PROCESSING,
            "created_at": datetime.now().isoformat(),
            "company_name": company_name,
            "funding_stage": funding_stage,
            "files_count": len(files),
            "progress": "Initializing...",
            "result": None,
            "error": None,
        }

        # Read template file content if provided (but don't parse yet - do it in background)
        template_doc = None
        if template_file:
            template_content = await template_file.read()
            template_doc = {
                "filename": template_file.filename,
                "content": template_content,
                "content_type": template_file.content_type,
            }
            jobs[job_id][
                "progress"
            ] = "Template file received, will parse in background..."

        # Start background processing (template parsing happens there)
        background_tasks.add_task(
            process_memo_async,
            job_id,
            documents,
            template_doc,
            company_name,
            funding_stage,
        )

        return {
            "job_id": job_id,
            "status": JobStatus.PROCESSING,
            "message": f"Processing {len(files)} documents for {company_name}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


async def process_memo_async(
    job_id: str,
    documents: list,
    template_doc: dict,
    company_name: str,
    funding_stage: str,
):
    """Background task to run memo generation pipeline"""

    try:
        # Parse template if provided (happens in background now)
        template_structure = None
        if template_doc:
            try:
                jobs[job_id]["progress"] = "Parsing template structure..."
                template_parser = TemplateParser()
                template_structure = await template_parser.parse_template(template_doc)
                jobs[job_id][
                    "progress"
                ] = f"Template parsed: {template_structure.get('template_name', 'Custom Template')}"
            except Exception as e:
                # Log error but continue with default template
                print(f"Error parsing template file: {e}")
                jobs[job_id][
                    "progress"
                ] = f"Template parsing failed, using default template: {str(e)}"
                template_structure = None
        else:
            jobs[job_id]["progress"] = "Using default template..."

        jobs[job_id]["progress"] = "Running LangGraph pipeline..."

        # Run the pipeline with parsed template structure
        result = await run_memo_pipeline(job_id, documents, template_structure)

        if result["success"]:
            jobs[job_id]["status"] = JobStatus.COMPLETED
            jobs[job_id]["result"] = {
                "memo_content": result["memo_content"],
                "confidence_scores": result["confidence_scores"],
                "flagged_items": result["flagged_items"],
                "uncertainty_flags": result.get("uncertainty_flags", []),
                "company_name": company_name,
                "funding_stage": funding_stage,
                "generated_at": datetime.now().isoformat(),
            }
            # Add performance metrics if available
            if "performance" in result:
                jobs[job_id]["performance"] = result["performance"]
            jobs[job_id]["progress"] = "Completed successfully"
        else:
            jobs[job_id]["status"] = JobStatus.FAILED
            jobs[job_id]["error"] = result.get("error_messages", ["Unknown error"])
            jobs[job_id]["progress"] = "Failed"

    except Exception as e:
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = [str(e)]
        jobs[job_id]["progress"] = "Failed with exception"


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Check job processing status"""

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    response = {
        "job_id": job_id,
        "status": job["status"],
        "created_at": job["created_at"],
        "progress": job.get("progress", ""),
        "company_name": job.get("company_name", ""),
        "funding_stage": job.get("funding_stage", ""),
    }

    if job["status"] == JobStatus.COMPLETED:
        response["completed_at"] = job["result"]["generated_at"]
    elif job["status"] == JobStatus.FAILED:
        response["error"] = job.get("error", ["Unknown error"])

    return response


@router.get("/memo/{job_id}")
async def get_memo(job_id: str):
    """Get completed memo content"""

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400, detail=f"Memo not ready. Current status: {job['status']}"
        )

    return job["result"]


@router.get("/memo/{job_id}/download")
async def download_memo(job_id: str):
    """Download memo as markdown file"""

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Memo not ready")

    memo_content = job["result"]["memo_content"]
    company_name = job["company_name"].replace(" ", "_")
    filename = (
        f"{company_name}_investment_memo{datetime.now().strftime('%Y%m%d%H%M%S')}.md"
    )

    return JSONResponse(
        content={"filename": filename, "content": memo_content},
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its results"""

    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]
    return {"message": "Job deleted successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len(
            [j for j in jobs.values() if j["status"] == JobStatus.PROCESSING]
        ),
    }


@router.get("/")
async def root():
    """API information"""
    return {
        "name": "VC Memo Automation API",
        "version": "1.0.0",
        "description": "Generate investment memos from deal documents",
        "endpoints": {
            "upload": {
                "path": "/upload-and-process",
                "method": "POST",
                "description": "Upload documents and start processing",
            },
            "status": {
                "path": "/status/{job_id}",
                "method": "GET",
                "description": "Check job status",
            },
            "memo": {
                "path": "/memo/{job_id}",
                "method": "GET",
                "description": "Get completed memo",
            },
            "download": {
                "path": "/memo/{job_id}/download",
                "method": "GET",
                "description": "Download memo as markdown",
            },
            "delete": {
                "path": "/job/{job_id}",
                "method": "DELETE",
                "description": "Delete job",
            },
            "health": {
                "path": "/health",
                "method": "GET",
                "description": "Health check",
            },
        },
    }

# MARK: - Admin Experimentation Endpoints

from app.services.experiments.corpus_manager import CorpusManager
from app.services.experiments.experiment_service import ExperimentService
from app.services.experiments.run_service import RunService
from app.schemas.admin import CompanyCorpus, Experiment, RunResult, GridSpec, Preset
from uuid import UUID

corpus_manager = CorpusManager()
experiment_service = ExperimentService()
run_service = RunService()

# Corpora endpoints
@router.post("/corpora")
async def create_corpus(
    name: str = Form(...),
    artifacts: List[UploadFile] = File(...)
):
    """Create a new corpus with artifacts"""
    files_data = []
    for file in artifacts:
        content = await file.read()
        files_data.append({
            "filename": file.filename,
            "type": file.filename.split(".")[-1] if "." in file.filename else "unknown",
            "content": content
        })
    
    corpus_id = corpus_manager.create_corpus(name, files_data)
    
    # Get the created corpus to return full details
    corpus = corpus_manager.storage.get_corpus(corpus_id)
    if corpus:
        # Convert to response format (remove file_path from artifacts)
        response_artifacts = []
        for artifact in corpus.get("artifacts", []):
            response_artifacts.append({
                "id": artifact.get("id"),
                "name": artifact.get("name"),
                "type": artifact.get("type"),
                "sha256": artifact.get("sha256"),
                "bytes": artifact.get("bytes")
            })
        
        return {
            "id": corpus_id,
            "name": name,
            "artifacts": response_artifacts,
            "createdAt": corpus.get("created_at", datetime.utcnow().isoformat())
        }
    
    # Fallback response
    return {
        "id": corpus_id,
        "name": name,
        "artifacts": [{"name": f["filename"], "type": f["type"]} for f in files_data],
        "createdAt": datetime.utcnow().isoformat()
    }

@router.get("/corpora/{corpus_id}")
async def get_corpus(corpus_id: str):
    """Get corpus by ID"""
    corpus = corpus_manager.storage.get_corpus(corpus_id)
    if not corpus:
        raise HTTPException(status_code=404, detail="Corpus not found")
    return corpus

@router.get("/corpora")
async def list_corpora():
    """List all corpora"""
    return corpus_manager.storage.list_corpora()

# Experiments endpoints
@router.post("/experiments")
async def create_experiment(experiment: Experiment):
    """Create a new experiment"""
    experiment_id = experiment_service.create_experiment(experiment.dict(by_alias=True))
    return {"id": experiment_id, "status": "created"}

@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Get experiment by ID"""
    experiment = experiment_service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment

@router.get("/experiments")
async def list_experiments(corpus_id: Optional[str] = None):
    """List experiments, optionally filtered by corpus"""
    return experiment_service.list_experiments(corpus_id)

# Runs endpoints
@router.post("/runs")
async def run_single(
    experiment_id: str = Form(...),
    model: Optional[str] = Form(None),
    decode: Optional[str] = Form(None)
):
    """Execute a single run"""
    decode_params = json.loads(decode) if decode else None
    result = await run_service.run_single(experiment_id, model, decode_params)
    return result

@router.post("/runs/batch")
async def run_batch(
    experiment_id: str = Form(...),
    grid: str = Form(...)
):
    """Execute batch runs from grid spec"""
    grid_spec = json.loads(grid)
    results = await run_service.run_batch(experiment_id, grid_spec)
    return results

@router.get("/runs")
async def list_runs(experiment_id: Optional[str] = None):
    """List runs, optionally filtered by experiment"""
    return run_service.storage.list_runs(experiment_id)

@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get run by ID"""
    run = run_service.storage.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str):
    """Cancel a queued or running run"""
    success = await run_service.cancel_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail="Run not found or cannot be cancelled")
    return {"status": "cancelled"}

@router.patch("/runs/{run_id}/rating")
async def update_run_rating(
    run_id: str,
    human_rating: Optional[int] = Form(None),
    human_notes: Optional[str] = Form(None)
):
    """Update human rating and notes for a run"""
    run = run_service.storage.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    updates = {}
    if human_rating is not None:
        updates["human_rating"] = human_rating
    if human_notes is not None:
        updates["human_notes"] = human_notes
    
    run_service.storage.update_run(run_id, updates)
    updated_run = run_service.storage.get_run(run_id)
    
    # Convert to RunResult schema
    from app.schemas.admin import RunResult
    return RunResult(**updated_run).dict(by_alias=True)

# Presets endpoints
@router.post("/presets")
async def save_preset(preset: Preset):
    """Save a preset"""
    preset_dict = preset.dict(by_alias=True)
    preset_id = run_service.storage.save_preset(preset_dict)
    return {"id": preset_id, "status": "saved"}

@router.get("/presets")
async def list_presets():
    """List all presets"""
    return run_service.storage.list_presets()

# Exports endpoint
@router.get("/runs/{run_id}/export")
async def export_run(run_id: str):
    """Export run as ZIP with config, memo, and scores"""
    import zipfile
    import io
    from fastapi.responses import StreamingResponse
    
    run = run_service.storage.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    experiment = experiment_service.get_experiment(run["experiment_id"])
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # config.json
        config = {
            "promptBundle": experiment.get("prompt_bundle", {}),
            "generation": experiment.get("generation", {}),
            "critical": experiment.get("critical", {}),
            "formatting": experiment.get("formatting", {}),
            "qc": experiment.get("qc", {}),
            "missing": experiment.get("missing", {}),
            "decode": experiment.get("decode", {}),
            "model": run.get("model"),
            "configHash": run.get("config_hash"),
            "seed": run.get("seed")
        }
        zip_file.writestr("config.json", json.dumps(config, indent=2))
        
        # memo.md
        zip_file.writestr("memo.md", run.get("memo_text", ""))
        
        # scores.json
        scores = {
            "sectionScores": run.get("section_scores", {}),
            "compositeScore": run.get("composite_score", 0.0),
            "flags": run.get("flags", [])
        }
        zip_file.writestr("scores.json", json.dumps(scores, indent=2))
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=run_{run_id}.zip"}
    )
