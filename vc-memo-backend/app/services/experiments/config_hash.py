"""
Config hashing utilities for deterministic run identification.
"""
import json
import hashlib
from typing import Dict, Any, List


def compute_config_hash(
    prompt_bundle: Dict[str, str],
    generation: Dict[str, Any],
    critical: Dict[str, Any],
    formatting: Dict[str, Any],
    qc: Dict[str, Any],
    missing: Dict[str, Any],
    decode: Dict[str, Any],
    model: str,
    artifact_hashes: List[str]
) -> str:
    """
    Compute SHA256 hash of canonical config blob.
    
    Args:
        prompt_bundle: {name, version}
        generation: GenerationSettings dict
        critical: CriticalDataRequirements dict
        formatting: OutputFormattingSettings dict
        qc: QualityControlSettings dict
        missing: MissingInformationPolicy dict
        decode: DecodeParams dict
        model: Model name string
        artifact_hashes: Sorted list of artifact SHA256 hashes
    
    Returns:
        SHA256 hex digest
    """
    # Create canonical blob
    canonical = {
        "promptBundle": prompt_bundle,
        "generation": generation,
        "critical": critical,
        "formatting": formatting,
        "qc": qc,
        "missing": missing,
        "decode": decode,
        "model": model,
        "artifacts": sorted(artifact_hashes)  # Sort for determinism
    }
    
    # Serialize to JSON with sorted keys
    blob = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    
    # Compute hash
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def compute_artifact_hash(content: bytes) -> str:
    """Compute SHA256 hash of artifact content"""
    return hashlib.sha256(content).hexdigest()

