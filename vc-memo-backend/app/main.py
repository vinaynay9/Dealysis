from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utils.ollama_setup import get_ollama_status, setup_ollama_automatically
import logging
import os

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VC Memo Automation API",
    description="Generate investment memos from deal documents",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Check Ollama status on app startup and optionally set it up"""
    # Check if auto-setup is enabled via environment variable
    auto_setup = os.getenv("OLLAMA_AUTO_SETUP", "false").lower() == "true"
    auto_install = os.getenv("OLLAMA_AUTO_INSTALL", "false").lower() == "true"
    
    installed, running, model_available, message = get_ollama_status()
    logger.info(f"Ollama Status: {message}")
    
    if not installed or not running or not model_available:
        if auto_setup:
            logger.info("🔧 Auto-setup enabled, attempting to configure Ollama...")
            success, setup_message = await setup_ollama_automatically(auto_install=auto_install)
            if success:
                logger.info(f"✅ {setup_message}")
            else:
                logger.warning(f"⚠️  {setup_message}")
                logger.info("💡 The system will use OpenAI if Ollama is unavailable.")
        else:
            logger.info("💡 Tip: Ollama is optional. The system will use OpenAI if Ollama is unavailable.")
            logger.info("💡 To enable Ollama for cost savings:")
            logger.info("   1. Install: brew install ollama")
            logger.info("   2. Start: ollama serve")
            logger.info("   3. Download model: ollama pull llama3.2:3b")
            logger.info("💡 Or set OLLAMA_AUTO_SETUP=true to auto-configure on startup")
    else:
        logger.info("✅ Ollama is ready and will be used for non-critical extractions")

