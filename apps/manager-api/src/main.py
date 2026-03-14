# OldClaw Manager API
# Provides REST endpoints for project, asset, playbook, and evidence orchestration.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any

app = FastAPI(title="OldClaw Manager API", version="0.1.0")

# ---------- Health ----------
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ---------- DTOs (simplified) ----------
class ProjectCreateReq(BaseModel):
    name: str
    request_text: str
    assets: List[str] | None = None

class AssetCreateReq(BaseModel):
    name: str
    type: str
    platform: str | None = None
    metadata: Any | None = None

# ---------- Project endpoints ----------
@app.post("/projects")
async def create_project(req: ProjectCreateReq):
    raise HTTPException(status_code=501, detail="create_project not implemented yet")

@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    # Placeholder stub
    raise HTTPException(status_code=404, detail="Project not found")

@app.post("/projects/{project_id}/execute")
async def execute_project(project_id: str, mode: str = "one_shot"):
    raise HTTPException(status_code=501, detail="execute_project not implemented yet")

# ---------- Asset endpoints ----------
@app.post("/assets")
async def create_asset(req: AssetCreateReq):
    raise HTTPException(status_code=501, detail="create_asset not implemented yet")

@app.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    raise HTTPException(status_code=404, detail="Asset not found")

@app.get("/assets/{asset_id}/resolve")
async def resolve_asset(asset_id: str):
    return {"asset_id": asset_id, "endpoints": []}

# ---------- Playbook execution ----------
@app.post("/playbooks/run")
async def run_playbook(playbook_id: str, input: Any = None):
    raise HTTPException(status_code=501, detail="run_playbook not implemented yet")

# ---------- Evidence listing ----------
@app.get("/projects/{project_id}/evidence")
async def list_evidence(project_id: str):
    return {"project_id": project_id, "evidence": []}
