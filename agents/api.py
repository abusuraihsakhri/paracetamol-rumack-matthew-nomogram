"""FastAPI endpoints for nomogram calculation and legacy operations."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from .base import AuditLogger
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor
from rumack_matthew import calculate_metrics

supervisor = SystemSupervisor(model_provider="mock")
app = FastAPI(
    title="Paracetamol Rumack Matthew Nomogram API",
    description="Clinical reference calculator and legacy audit operations",
    version="3.1.0",
)


class ChatRequest(BaseModel):
    query: str


class NomogramRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hours_post_ingestion: float
    concentration_mcg_ml: float
    ingestion_pattern: str = "acute"
    time_known: bool = True
    delayed_absorption: bool = False


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "paracetamol-rumack-matthew-nomogram", "version": "3.1.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/nomogram")
def api_nomogram(payload: NomogramRequest):
    try:
        return calculate_metrics(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    return supervisor.process_task(payload).to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
