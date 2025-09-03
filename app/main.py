from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import List
from . import services, llm
from .neo4j_client import Neo4jClient
from .models import *
import os
import ollama

app = FastAPI(title="AI-Powered ASPM Backend")
db = Neo4jClient()

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI-Powered ASPM Backend!"}

@app.on_event("startup")
def startup_event():
    db.init_constraints()

@app.on_event("shutdown")
def shutdown_event():
    db.close()

@app.post("/webhook/semgrep")
def webhook_semgrep(payload: WebhookPayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(services.ingest_semgrep, payload, db)
    return {"status": "success", "message": "Findings queued for ingestion."}

@app.get("/risks", response_model=List[FindingOut])
def get_risks():
    findings = services.list_risks(db)
    return findings

@app.get("/risks/{fp}", response_model=FindingOut)
def get_risk_details(fp: str):
    finding = services.get_finding(fp, db)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@app.post("/risks/{fp}/status", response_model=FindingOut)
def update_risk_status(fp: str, status_update: StatusUpdate):
    updated_finding = services.update_status(fp, status_update.status, db)
    if not updated_finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    # We need to fetch the full finding details again to include repo/commit
    return services.get_finding(fp, db)

@app.post("/risks/{fp}/explain", response_model=ExplanationResponse)
def get_risk_explanation(fp: str):
    explanation = services.explain_risk(fp, db)
    if explanation is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return ExplanationResponse(explanation=explanation)

@app.post("/train/ollama", response_model=TrainJobOut)
def train_ollama_model(req: TrainRequest, background_tasks: BackgroundTasks):
    # This is a blocking call in the service, but we'll run it in the background
    # For a real app, you'd use a proper job queue like Celery or RQ
    background_tasks.add_task(services.ollama_train, req)
    return TrainJobOut(status="started", model_name=req.model_name)

@app.get("/model/info", response_model=ModelInfo)
def get_model_info():
    provider = os.getenv("LLM_PROVIDER", "stub").lower()
    model_name = None
    details = None
    if provider == "ollama":
        model_name = os.getenv("OLLAMA_MODEL")
        try:
            details = ollama.show(model_name).model_dump()
        except ollama.ResponseError:
            details = {"error": f"Model '{model_name}' not found locally."}
    elif provider == "openai":
        model_name = os.getenv("OPENAI_MODEL")

    return ModelInfo(provider=provider, model=model_name, details=details)
