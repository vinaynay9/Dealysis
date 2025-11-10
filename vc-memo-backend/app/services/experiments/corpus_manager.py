"""
Corpus management service
"""
import hashlib
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.services.experiments.storage import Storage as ExperimentStorage


class CorpusManager:
    """Manages corpus creation and artifact handling"""
    
    def __init__(self, storage: ExperimentStorage = None, artifacts_dir: str = "runtime/experiments/artifacts"):
        self.storage = storage or ExperimentStorage()
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    def compute_sha256(self, file_content: bytes) -> str:
        """Compute SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _save_artifact_file(self, corpus_id: str, artifact_id: str, content: bytes, filename: str) -> str:
        """Save artifact file to disk and return file path"""
        corpus_dir = self.artifacts_dir / corpus_id
        corpus_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine extension from filename
        ext = Path(filename).suffix or ".bin"
        file_path = corpus_dir / f"{artifact_id}{ext}"
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return str(file_path)
    
    def create_corpus(self, name: str, files: List[Dict[str, Any]]) -> str:
        """Create a corpus from uploaded files"""
        import uuid
        
        corpus_id = str(uuid.uuid4())
        artifacts = []
        
        for file_data in files:
            content = file_data["content"]
            artifact_id = str(uuid.uuid4())
            filename = file_data["filename"]
            
            # Compute SHA256
            sha256 = self.compute_sha256(content)
            
            # Save file to disk
            file_path = self._save_artifact_file(corpus_id, artifact_id, content, filename)
            
            artifacts.append({
                "id": artifact_id,
                "name": filename,
                "type": file_data.get("type", filename.split(".")[-1] if "." in filename else "unknown"),
                "sha256": sha256,
                "bytes": len(content),
                "file_path": file_path  # Store path for later retrieval
            })
        
        # Save corpus metadata
        corpus = {
            "id": corpus_id,
            "name": name,
            "artifacts": artifacts
        }
        self.storage.save_corpus(corpus)
        
        return corpus_id
    
    def load_artifact_content(self, corpus_id: str, artifact_id: str) -> Optional[bytes]:
        """Load artifact file content from disk"""
        corpus_dir = self.artifacts_dir / corpus_id
        
        # Try to find the artifact file (may have different extensions)
        for file_path in corpus_dir.glob(f"{artifact_id}.*"):
            if file_path.is_file():
                with open(file_path, "rb") as f:
                    return f.read()
        
        return None
    
    def load_corpus_artifacts(self, corpus_id: str) -> List[Dict[str, Any]]:
        """Load all artifacts for a corpus as document dictionaries"""
        corpus = self.storage.get_corpus(corpus_id)
        if not corpus:
            return []
        
        documents = []
        for artifact in corpus.get("artifacts", []):
            artifact_id = artifact.get("id")
            if not artifact_id:
                continue
            
            content = self.load_artifact_content(corpus_id, artifact_id)
            if content is None:
                continue
            
            # Determine content type
            file_type = artifact.get("type", "unknown")
            content_type_map = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "csv": "text/csv",
                "txt": "text/plain",
                "md": "text/markdown"
            }
            content_type = content_type_map.get(file_type, "application/octet-stream")
            
            documents.append({
                "filename": artifact.get("name", "unknown"),
                "content": content,
                "content_type": content_type
            })
        
        return documents

