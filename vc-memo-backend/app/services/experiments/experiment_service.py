"""
Experiment service - CRUD operations
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.services.experiments.storage import Storage as ExperimentStorage


class ExperimentService:
    """Manages experiment CRUD operations"""
    
    def __init__(self, storage: ExperimentStorage = None):
        self.storage = storage or ExperimentStorage()
    
    def create_experiment(self, experiment_data: Dict[str, Any]) -> str:
        """Create a new experiment"""
        return self.storage.create_experiment(experiment_data)
    
    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment by ID"""
        return self.storage.get_experiment(experiment_id)
    
    def list_experiments(self, corpus_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List experiments, optionally filtered by corpus"""
        return self.storage.list_experiments(corpus_id)

