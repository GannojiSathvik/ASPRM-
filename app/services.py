import ollama
from .neo4j_client import Neo4jClient
import os
from .models import WebhookPayload, TrainRequest
from .llm import get_explanation_from_llm

def ingest_semgrep(payload: WebhookPayload, db: Neo4jClient):
    for result in payload.results:
        finding_data = {
            "fingerprint": result.extra.fingerprint,
            "check_id": result.check_id,
            "path": result.path,
            "line": result.start.line,
            "message": result.extra.message,
            "severity": result.extra.severity,
            "code_snippet": result.extra.lines,
            "repo_name": payload.repo_name,
            "file_path": result.path,
            "commit_hash": payload.commit
        }
        db.ingest_finding(finding_data)

def list_risks(db: Neo4jClient):
    return db.list_findings()

def get_finding(fp: str, db: Neo4jClient):
    return db.get_finding(fp)

def update_status(fp: str, status: str, db: Neo4jClient):
    return db.update_finding_status(fp, status)

def explain_risk(fp: str, db: Neo4jClient):
    finding = db.get_finding(fp)
    if not finding:
        return None
    return get_explanation_from_llm(finding)

def ollama_train(req: TrainRequest):
    modelfile_content = f"""
    FROM {req.base_model}
    SYSTEM "{req.system_prompt}"
    ADAPTER {os.path.abspath(req.dataset_path)}
    """
    try:
        # Check if Ollama server is running
        ollama.ping()
    except ollama.ResponseError as e:
        return {"status": "error", "model_name": req.model_name, "details": f"Ollama server not reachable: {str(e)}"}

    # Check if dataset path exists
    if not os.path.exists(req.dataset_path):
        return {"status": "error", "model_name": req.model_name, "details": f"Dataset file not found at {req.dataset_path}"}

    try:
        ollama.create(model=req.model_name, modelfile=modelfile_content)
        return {"status": "success", "model_name": req.model_name}
    except Exception as e:
        return {"status": "error", "model_name": req.model_name, "details": str(e)}
