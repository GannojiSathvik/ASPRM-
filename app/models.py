from pydantic import BaseModel
from typing import List, Optional, Dict

# --- Models for Webhook Ingestion ---
class ScanLocation(BaseModel):
    line: int
    col: Optional[int] = None

class SemgrepExtra(BaseModel):
    fingerprint: str
    lines: str
    message: str
    severity: str
    metadata: Dict = {}

class SemgrepResult(BaseModel):
    check_id: str
    path: str
    start: ScanLocation
    extra: SemgrepExtra

class WebhookPayload(BaseModel):
    results: List[SemgrepResult]
    repo_name: Optional[str] = "default/repo"
    commit: Optional[str] = "HEAD"

# --- Models for API Responses ---
class FindingOut(BaseModel):
    fingerprint: str
    check_id: str
    path: str
    line: int
    message: str
    severity: str
    status: str
    repo_name: Optional[str]
    commit: Optional[str]

class ExplanationResponse(BaseModel):
    explanation: str

class ModelInfo(BaseModel):
    provider: str
    model: Optional[str] = None
    details: Optional[Dict] = None

# --- Models for API Inputs ---
class StatusUpdate(BaseModel):
    status: str # e.g., "fixed", "false_positive", "open"

class TrainRequest(BaseModel):
    model_name: str
    dataset_path: str
    base_model: str = "llama3"
    system_prompt: Optional[str] = "You are an expert Application Security assistant."

class TrainJobOut(BaseModel):
    status: str
    model_name: str
    details: Optional[str] = None
