from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from app.services.pipeline import run_memo_pipeline
from app.core.models import JobStatus
from app.services.template_parser import TemplateParser

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
