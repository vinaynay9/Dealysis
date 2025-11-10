"""
Run service - Execute single and batch runs with async queue
"""
import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.services.experiments.storage import Storage
from app.services.experiments.config_hash import compute_config_hash, compute_artifact_hash
from app.services.experiments.scoring.rubric import Rubric
from app.services.pipeline.pipeline import run_memo_pipeline
from app.services.experiments.experiment_service import ExperimentService
from app.services.experiments.corpus_manager import CorpusManager


class RunService:
    """Manages run execution with async queue"""
    
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.experiment_service = ExperimentService()
        self.corpus_manager = CorpusManager()
        self.rubric = Rubric()
        self._run_queue = asyncio.Queue()
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._cancelled_runs: set = set()
    
    async def run_single(
        self, 
        experiment_id: str, 
        model: str = None, 
        decode: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a single run (queued)"""
        run_id = str(uuid.uuid4())
        
        # Get experiment
        experiment = self.storage.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        # Get corpus and artifacts
        corpus = self.storage.get_corpus(experiment.get("corpus_id"))
        if not corpus:
            raise ValueError(f"Corpus not found for experiment")
        
        # Build config hash
        artifact_hashes = [a.get("sha256", "") for a in corpus.get("artifacts", [])]
        config_hash = compute_config_hash(
            prompt_bundle=experiment.get("prompt_bundle", {}),
            generation=experiment.get("generation", {}),
            critical=experiment.get("critical", {}),
            formatting=experiment.get("formatting", {}),
            qc=experiment.get("qc", {}),
            missing=experiment.get("missing", {}),
            decode=decode or experiment.get("decode", {}),
            model=model or experiment.get("model", "gpt-4o"),
            artifact_hashes=artifact_hashes
        )
        
        # Create run record
        run = {
            "id": run_id,
            "experiment_id": experiment_id,
            "model": model or experiment.get("model", "gpt-4o"),
            "config_hash": config_hash,
            "status": "queued",
            "started_at": datetime.utcnow().isoformat(),
            "duration_ms": 0,
            "memo_text": "",
            "section_scores": {},
            "composite_score": 0.0,
            "flags": [],
            "error": None,
            "seed": decode.get("seed") if decode else experiment.get("decode", {}).get("seed")
        }
        
        self.storage.save_run(run)
        
        # Queue for execution
        await self._run_queue.put(run_id)
        asyncio.create_task(self._process_run_queue())
        
        return run
    
    async def run_batch(
        self, 
        experiment_id: str, 
        grid: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute batch runs from grid spec (all queued)"""
        runs = []
        
        models = grid.get("models", [])
        temperatures = grid.get("temperatures", [])
        thresholds = grid.get("thresholds", [])
        seeds = grid.get("seeds", [None])
        
        # Validate grid size
        total_cells = len(models) * len(temperatures) * len(thresholds) * len(seeds)
        if total_cells > 128:
            raise ValueError(f"Grid too large: {total_cells} cells (max 128)")
        
        # Create runs for each combination
        for model in models:
            for temp in temperatures:
                for threshold in thresholds:
                    for seed in seeds:
                        decode = {
                            "temperature": temp,
                            "topP": 0.95,
                            "maxTokens": 4000,
                            "seed": seed
                        }
                        
                        run = await self.run_single(experiment_id, model, decode)
                        runs.append(run)
        
        return runs
    
    async def _process_run_queue(self):
        """Process queued runs"""
        while not self._run_queue.empty():
            run_id = await self._run_queue.get()
            
            if run_id in self._cancelled_runs:
                self._cancelled_runs.discard(run_id)
                self.storage.update_run(run_id, {"status": "cancelled"})
                continue
            
            # Create task for this run
            task = asyncio.create_task(self._execute_run(run_id))
            self._running_tasks[run_id] = task
    
    async def _execute_run(self, run_id: str):
        """Execute a single run"""
        start_time = time.time()
        
        try:
            # Update status to running
            self.storage.update_run(run_id, {"status": "running"})
            
            # Get run record
            run = self.storage.get_run(run_id)
            if not run:
                return
            
            # Get experiment and corpus
            experiment = self.storage.get_experiment(run["experiment_id"])
            if not experiment:
                self.storage.update_run(run_id, {
                    "status": "failed",
                    "error": "Experiment not found",
                    "duration_ms": int((time.time() - start_time) * 1000)
                })
                return
            
            corpus_id = experiment.get("corpus_id")
            corpus = self.storage.get_corpus(corpus_id)
            if not corpus:
                self.storage.update_run(run_id, {
                    "status": "failed",
                    "error": "Corpus not found",
                    "duration_ms": int((time.time() - start_time) * 1000)
                })
                return
            
            # Load documents from corpus artifacts
            documents = self.corpus_manager.load_corpus_artifacts(corpus_id)
            if not documents:
                self.storage.update_run(run_id, {
                    "status": "failed",
                    "error": "No artifacts found in corpus",
                    "duration_ms": int((time.time() - start_time) * 1000)
                })
                return
            
            # Prepare settings from experiment
            # Convert experiment settings to pipeline format
            generation_settings = {
                "minimumConfidenceThreshold": experiment.get("generation", {}).get("minimumConfidenceThreshold", 0.7),
                "criticalFieldConfidenceThreshold": experiment.get("generation", {}).get("criticalFieldConfidenceThreshold", 0.8),
                "flagLowConfidenceSections": experiment.get("generation", {}).get("flagLowConfidenceSections", True),
                "requireConfidenceForCompletion": experiment.get("generation", {}).get("requireConfidenceForCompletion", False),
                "confidenceCalculationMethod": experiment.get("generation", {}).get("confidenceCalculationMethod", "hybrid"),
                "formatting": experiment.get("formatting", {}),
                "qc": experiment.get("qc", {}),
                "critical": experiment.get("critical", {}),
                "missing": experiment.get("missing", {})
            }
            
            # Get seed
            seed = run.get("seed")
            
            # Run pipeline
            result = await run_memo_pipeline(
                job_id=run_id,
                documents=documents,
                template_structure=None,
                generation_settings=generation_settings,
                seed=seed
            )
            
            if not result.get("success"):
                self.storage.update_run(run_id, {
                    "status": "failed",
                    "error": str(result.get("error", "Unknown error")),
                    "duration_ms": int((time.time() - start_time) * 1000)
                })
                return
            
            # Score the memo
            memo_text = result.get("memo_content", "")
            confidence_scores = result.get("confidence_scores", {})
            
            # Get required fields from experiment
            critical = experiment.get("critical", {})
            required_fields = {
                "financial": critical.get("requiredFinancialFields", []),
                "progress": critical.get("requiredProgressFields", []),
                "market": critical.get("requiredMarketFields", []),
                "company": critical.get("requiredCompanyFields", []),
                "team": critical.get("requiredTeamFields", [])
            }
            
            # Score with rubric
            # Convert confidence_scores dict to simple float values for rubric
            simple_scores = {k: float(v) if isinstance(v, (int, float)) else 0.5 for k, v in confidence_scores.items()}
            
            section_scores_dict, composite_score, flags = self.rubric.score(
                memo_text=memo_text,
                section_scores=simple_scores,
                required_fields=required_fields,
                citations_enabled=experiment.get("formatting", {}).get("includeSourceCitations", True)
            )
            
            # Flatten section scores for storage (extract confidence values)
            flattened_scores = {}
            for section, score_data in section_scores_dict.items():
                if isinstance(score_data, dict):
                    flattened_scores[section] = score_data.get("confidence", 0.5)
                else:
                    flattened_scores[section] = float(score_data) if isinstance(score_data, (int, float)) else 0.5
            
            # Update run with results
            duration_ms = int((time.time() - start_time) * 1000)
            
            self.storage.update_run(run_id, {
                "status": "succeeded",
                "duration_ms": duration_ms,
                "memo_text": memo_text,
                "section_scores": flattened_scores,
                "composite_score": composite_score,
                "flags": flags
            })
            
        except Exception as e:
            self.storage.update_run(run_id, {
                "status": "failed",
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            })
        finally:
            # Remove from running tasks
            self._running_tasks.pop(run_id, None)
    
    async def cancel_run(self, run_id: str) -> bool:
        """Cancel a queued or running run"""
        run = self.storage.get_run(run_id)
        if not run:
            return False
        
        status = run.get("status")
        
        if status == "queued":
            # Mark as cancelled, will be handled in queue processing
            self._cancelled_runs.add(run_id)
            self.storage.update_run(run_id, {"status": "cancelled"})
            return True
        elif status == "running":
            # Try to cancel the task
            task = self._running_tasks.get(run_id)
            if task:
                task.cancel()
                self.storage.update_run(run_id, {"status": "cancelled"})
                return True
        
        return False
