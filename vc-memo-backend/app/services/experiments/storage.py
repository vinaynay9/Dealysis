"""
Storage layer for experiments, runs, and presets.
Uses JSONL for append-only storage.
"""
import json
import os
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from uuid import UUID
import uuid


class Storage:
    """Simple JSONL-based storage for experiments"""
    
    def __init__(self, data_dir: str = "runtime/experiments"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.corpora_file = self.data_dir / "corpora.jsonl"
        self.experiments_file = self.data_dir / "experiments.jsonl"
        self.runs_file = self.data_dir / "runs.jsonl"
        self.presets_file = self.data_dir / "presets.jsonl"
        
        # Initialize files if they don't exist
        for file in [self.corpora_file, self.experiments_file, self.runs_file, self.presets_file]:
            if not file.exists():
                file.touch()
    
    # Corpora
    def save_corpus(self, corpus: Dict[str, Any]) -> str:
        """Save a corpus to storage"""
        corpus_id = corpus.get("id", str(uuid.uuid4()))
        corpus["id"] = corpus_id
        corpus["created_at"] = datetime.utcnow().isoformat()
        
        with open(self.corpora_file, "a") as f:
            f.write(json.dumps(corpus) + "\n")
        
        return corpus_id
    
    def create_corpus(self, name: str, artifacts: List[Dict[str, Any]]) -> str:
        """Create a corpus (alias for save_corpus with different signature)"""
        corpus = {
            "id": str(uuid.uuid4()),
            "name": name,
            "artifacts": artifacts
        }
        return self.save_corpus(corpus)
    
    def get_corpus(self, corpus_id: str) -> Optional[Dict[str, Any]]:
        """Get a corpus by ID"""
        with open(self.corpora_file, "r") as f:
            for line in f:
                if line.strip():
                    corpus = json.loads(line)
                    if corpus.get("id") == corpus_id:
                        return corpus
        return None
    
    def list_corpora(self) -> List[Dict[str, Any]]:
        """List all corpora"""
        corpora = []
        with open(self.corpora_file, "r") as f:
            for line in f:
                if line.strip():
                    corpora.append(json.loads(line))
        return corpora
    
    # Experiments
    def save_experiment(self, experiment: Dict[str, Any]) -> str:
        """Save an experiment to storage"""
        experiment_id = experiment.get("id", str(uuid.uuid4()))
        experiment["id"] = experiment_id
        if "created_at" not in experiment:
            experiment["created_at"] = datetime.utcnow().isoformat()
        
        with open(self.experiments_file, "a") as f:
            f.write(json.dumps(experiment) + "\n")
        
        return experiment_id
    
    def create_experiment(self, experiment_data: Dict[str, Any]) -> str:
        """Create an experiment (alias for save_experiment)"""
        return self.save_experiment(experiment_data)
    
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get an experiment by ID"""
        with open(self.experiments_file, "r") as f:
            for line in f:
                if line.strip():
                    exp = json.loads(line)
                    if exp.get("id") == experiment_id:
                        return exp
        return None
    
    def list_experiments(self, corpus_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List experiments, optionally filtered by corpus"""
        experiments = []
        with open(self.experiments_file, "r") as f:
            for line in f:
                if line.strip():
                    exp = json.loads(line)
                    if not corpus_id or exp.get("corpus_id") == corpus_id:
                        experiments.append(exp)
        return experiments
    
    # Runs
    def save_run(self, run: Dict[str, Any]) -> str:
        """Save a run to storage"""
        run_id = run.get("id", str(uuid.uuid4()))
        run["id"] = run_id
        if "started_at" not in run:
            run["started_at"] = datetime.utcnow().isoformat()
        
        with open(self.runs_file, "a") as f:
            f.write(json.dumps(run) + "\n")
        
        return run_id
    
    def update_run(self, run_id: str, updates: Dict[str, Any]) -> bool:
        """Update a run (find and replace)"""
        runs = []
        found = False
        
        with open(self.runs_file, "r") as f:
            for line in f:
                if line.strip():
                    run = json.loads(line)
                    if run.get("id") == run_id:
                        run.update(updates)
                        found = True
                    runs.append(run)
        
        if found:
            # Rewrite file
            with open(self.runs_file, "w") as f:
                for run in runs:
                    f.write(json.dumps(run) + "\n")
        
        return found
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a run by ID"""
        with open(self.runs_file, "r") as f:
            for line in f:
                if line.strip():
                    run = json.loads(line)
                    if run.get("id") == run_id:
                        return run
        return None
    
    def list_runs(self, experiment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List runs, optionally filtered by experiment"""
        runs = []
        with open(self.runs_file, "r") as f:
            for line in f:
                if line.strip():
                    run = json.loads(line)
                    if not experiment_id or run.get("experiment_id") == experiment_id:
                        runs.append(run)
        return runs
    
    # Presets
    def save_preset(self, preset: Dict[str, Any]) -> str:
        """Save a preset to storage"""
        preset_id = preset.get("id", str(uuid.uuid4()))
        preset["id"] = preset_id
        preset["created_at"] = datetime.utcnow().isoformat()
        
        with open(self.presets_file, "a") as f:
            f.write(json.dumps(preset) + "\n")
        
        return preset_id
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """List all presets"""
        presets = []
        with open(self.presets_file, "r") as f:
            for line in f:
                if line.strip():
                    presets.append(json.loads(line))
        return presets
    
    def get_preset(self, preset_id: str) -> Optional[Dict[str, Any]]:
        """Get a preset by ID"""
        with open(self.presets_file, "r") as f:
            for line in f:
                if line.strip():
                    preset = json.loads(line)
                    if preset.get("id") == preset_id:
                        return preset
        return None


# Alias for backward compatibility with services
ExperimentStorage = Storage
