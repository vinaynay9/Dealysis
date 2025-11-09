"""
Ollama setup and detection utilities
Checks for Ollama installation, service status, and model availability
Includes detection for Ollama bundled with Mac app
Can automatically install and set up Ollama for testing
"""
import subprocess
import httpx
import os
import sys
import platform
from pathlib import Path
from typing import Optional, Tuple
import time


def check_ollama_installed() -> bool:
    """
    Check if Ollama command is available in PATH or standard locations
    Also checks for Ollama bundled with Mac app
    """
    # Check PATH first (fastest)
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check standard installation locations
    standard_paths = [
        "/usr/local/bin/ollama",
        "/opt/homebrew/bin/ollama",
        "/usr/bin/ollama",
        os.path.expanduser("~/.local/bin/ollama"),
    ]
    
    for path in standard_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return True
    
    # Check for Ollama in Mac app bundle (if running from bundled app)
    # Mac apps typically have structure: AppName.app/Contents/Resources/
    app_bundle_paths = [
        # Common app bundle locations
        os.path.expanduser("~/Applications/Dealysis.app/Contents/Resources/ollama"),
        os.path.expanduser("~/Applications/Dealysis.app/Contents/Resources/Ollama/ollama"),
        "/Applications/Dealysis.app/Contents/Resources/ollama",
        "/Applications/Dealysis.app/Contents/Resources/Ollama/ollama",
        # Also check if we're running from a bundle
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Resources", "ollama"),
    ]
    
    for path in app_bundle_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return True
    
    return False


def check_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama service is running"""
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


async def check_model_installed(
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434"
) -> bool:
    """Check if specified model is installed in Ollama"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                return any(model in name for name in model_names)
            return False
    except Exception:
        return False


def get_ollama_status() -> Tuple[bool, bool, bool, Optional[str]]:
    """
    Get comprehensive Ollama status
    
    Returns:
        (installed, running, model_available, message)
    """
    installed = check_ollama_installed()
    running = check_ollama_running()
    
    if not installed:
        return (
            False,
            False,
            False,
            "⚠️  Ollama not installed. Install with: brew install ollama"
        )
    
    if not running:
        return (
            True,
            False,
            False,
            "⚠️  Ollama installed but not running. Start with: ollama serve"
        )
    
    # Check model synchronously (for startup check)
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            model_available = any("llama3.2:3b" in name for name in model_names)
            
            if not model_available:
                return (
                    True,
                    True,
                    False,
                    "⚠️  Ollama running but llama3.2:3b not installed. Install with: ollama pull llama3.2:3b"
                )
            
            return (
                True,
                True,
                True,
                "✅ Ollama ready (llama3.2:3b available)"
            )
    except Exception:
        return (
            True,
            True,
            False,
            "⚠️  Ollama running but unable to check models"
        )
    
    return (
        True,
        True,
        False,
        "⚠️  Ollama status unknown"
    )


async def ensure_ollama_ready() -> Tuple[bool, str]:
    """
    Check Ollama readiness asynchronously (for runtime checks)
    
    Returns:
        (ready, message)
    """
    installed = check_ollama_installed()
    if not installed:
        return (
            False,
            "⚠️  Ollama not installed. Install with: brew install ollama"
        )
    
    running = check_ollama_running()
    if not running:
        return (
            False,
            "⚠️  Ollama installed but not running. Start with: ollama serve"
        )
    
    model_available = await check_model_installed()
    if not model_available:
        return (
            False,
            "⚠️  Ollama running but llama3.2:3b not installed. Install with: ollama pull llama3.2:3b"
        )
    
    return (
        True,
        "✅ Ollama ready (llama3.2:3b available)"
    )


def check_homebrew_installed() -> bool:
    """Check if Homebrew is installed"""
    try:
        result = subprocess.run(
            ["brew", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_ollama_via_homebrew() -> Tuple[bool, str]:
    """
    Install Ollama via Homebrew
    
    Returns:
        (success, message)
    """
    if not check_homebrew_installed():
        return (
            False,
            "⚠️  Homebrew not found. Install Homebrew first: https://brew.sh"
        )
    
    print("📦 Installing Ollama via Homebrew...")
    try:
        result = subprocess.run(
            ["brew", "install", "ollama"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        if result.returncode == 0:
            return (True, "✅ Ollama installed successfully")
        else:
            error_msg = result.stderr or result.stdout
            return (
                False,
                f"⚠️  Failed to install Ollama: {error_msg[:200]}"
            )
    except subprocess.TimeoutExpired:
        return (False, "⚠️  Installation timed out")
    except Exception as e:
        return (False, f"⚠️  Installation error: {str(e)}")


def start_ollama_service() -> Tuple[bool, str]:
    """
    Start Ollama service in background and wait until it's ready
    
    Returns:
        (success, message)
    """
    if not check_ollama_installed():
        return (False, "⚠️  Ollama not installed")
    
    if check_ollama_running():
        return (True, "✅ Ollama service already running")
    
    print("🚀 Starting Ollama service...")
    try:
        # Start Ollama in background (non-blocking)
        if platform.system() == "Darwin":  # macOS
            # Use nohup or launchd for background process
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        else:
            # For other platforms
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # Poll repeatedly until service is ready (up to 30 seconds)
        max_attempts = 15
        poll_interval = 2  # seconds
        print("   Waiting for service to be ready...")
        
        for attempt in range(1, max_attempts + 1):
            time.sleep(poll_interval)
            if check_ollama_running():
                print(f"   ✅ Ollama service started and ready! (took ~{attempt * poll_interval}s)")
                return (True, "✅ Ollama service started and ready")
            else:
                print(f"   ⏳ Checking... (attempt {attempt}/{max_attempts})")
        
        # If we get here, service didn't start within timeout
        return (False, f"⚠️  Service started but not responding after {max_attempts * poll_interval}s (may need manual start)")
    except Exception as e:
        return (False, f"⚠️  Failed to start service: {str(e)}")


def install_ollama_model(model: str = "llama3.2:3b") -> Tuple[bool, str]:
    """
    Install Ollama model
    
    Returns:
        (success, message)
    """
    if not check_ollama_running():
        return (False, "⚠️  Ollama service not running")
    
    print(f"📥 Downloading model {model} (this may take a few minutes, ~2GB)...")
    try:
        result = subprocess.run(
            ["ollama", "pull", model],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes max for download
        )
        
        if result.returncode == 0:
            return (True, f"✅ Model {model} installed successfully")
        else:
            error_msg = result.stderr or result.stdout
            return (
                False,
                f"⚠️  Failed to install model: {error_msg[:200]}"
            )
    except subprocess.TimeoutExpired:
        return (False, "⚠️  Model download timed out")
    except Exception as e:
        return (False, f"⚠️  Model installation error: {str(e)}")


async def setup_ollama_automatically(auto_install: bool = False) -> Tuple[bool, str]:
    """
    Automatically set up Ollama (install, start service, download model)
    
    Args:
        auto_install: If True, will attempt to install Ollama via Homebrew if not found
    
    Returns:
        (success, message)
    """
    # Check if already ready
    ready, message = await ensure_ollama_ready()
    if ready:
        return (True, message)
    
    # Step 1: Install Ollama if needed
    if not check_ollama_installed():
        if auto_install:
            success, msg = install_ollama_via_homebrew()
            if not success:
                return (False, msg)
            print(msg)
        else:
            return (
                False,
                "⚠️  Ollama not installed. Run with auto_install=True or install manually: brew install ollama"
            )
    
    # Step 2: Start service (now waits until ready internally)
    if not check_ollama_running():
        success, msg = start_ollama_service()
        if not success:
            return (False, msg)
        print(msg)
    
    # Step 3: Check/install model
    if not await check_model_installed():
        success, msg = install_ollama_model()
        if not success:
            return (False, msg)
        print(msg)
    
    # Final check
    ready, message = await ensure_ollama_ready()
    return (ready, message)

