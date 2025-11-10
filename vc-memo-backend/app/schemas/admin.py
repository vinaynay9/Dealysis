"""
Admin experiment schemas - Pydantic models mirroring Swift types
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class CorpusArtifact(BaseModel):
    id: UUID
    name: str
    type: str  # "docx", "xlsx", "pdf", "txt"
    sha256: str
    bytes: int


class CompanyCorpus(BaseModel):
    id: UUID
    name: str
    artifacts: List[CorpusArtifact] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PromptBundleRef(BaseModel):
    name: str  # e.g. "vc-memo"
    version: str  # e.g. "1.3.0"


class DecodeParams(BaseModel):
    temperature: float = 0.2
    top_p: float = Field(default=1.0, alias="topP")
    max_tokens: int = Field(default=4000, alias="maxTokens")
    seed: Optional[int] = None

    class Config:
        populate_by_name = True


class Experiment(BaseModel):
    id: UUID
    name: str
    corpus_id: UUID = Field(alias="corpusId")
    prompt_bundle: PromptBundleRef = Field(alias="promptBundle")
    generation: Dict[str, Any]  # GenerationSettings as JSON
    critical: Dict[str, Any]  # CriticalDataRequirements as JSON
    formatting: Dict[str, Any]  # OutputFormattingSettings as JSON
    qc: Dict[str, Any]  # QualityControlSettings as JSON
    missing: Dict[str, Any]  # MissingInformationPolicy as JSON
    decode: DecodeParams
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")

    class Config:
        populate_by_name = True


from enum import Enum

class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunResult(BaseModel):
    id: UUID
    experiment_id: UUID = Field(alias="experimentId")
    model: str
    config_hash: str = Field(alias="configHash")
    started_at: datetime = Field(default_factory=datetime.utcnow, alias="startedAt")
    duration_ms: int = Field(default=0, alias="durationMs")
    memo_text: str = Field(default="", alias="memoText")
    section_scores: Dict[str, float] = Field(default_factory=dict, alias="sectionScores")
    composite_score: float = Field(default=0.0, alias="compositeScore")
    flags: List[str] = Field(default_factory=list)
    status: str = Field(default="pending")
    error: Optional[str] = None
    human_rating: Optional[int] = Field(default=None, alias="humanRating", ge=1, le=5)
    human_notes: Optional[str] = Field(default=None, alias="humanNotes")

    class Config:
        populate_by_name = True


class GridSpec(BaseModel):
    models: List[str] = Field(default_factory=list)
    temperatures: List[float] = Field(default_factory=list)
    thresholds: List[float] = Field(default_factory=list)
    seeds: List[Optional[int]] = Field(default_factory=list)

    @property
    def cell_count(self) -> int:
        return len(self.models) * len(self.temperatures) * len(self.thresholds) * max(len(self.seeds), 1)


class Preset(BaseModel):
    id: UUID
    name: str
    version: str
    tag: Optional[str] = None
    settings: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow, alias="createdAt")

    class Config:
        populate_by_name = True

