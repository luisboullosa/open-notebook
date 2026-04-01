from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List
import os
import uuid
import httpx
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI(title="CDISC Frontend API Mirror")

UPLOADS = Path("/app/uploads")
UPLOADS.mkdir(parents=True, exist_ok=True)

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://host.docker.internal:11435")


class GenerateRequest(BaseModel):
    projectName: str
    language: str = "R"
    nSubjects: int = 50
    sdtmDomains: List[str] = []
    adamDomains: List[str] = []
    messTypes: List[str] = []
    messinessLevel: int = 1


jobs = {}


async def run_job(job_id: str, payload: dict):
    jobs[job_id]["status"] = "running"
    try:
        prompt = f"Generate dummy dataset for {payload.get('projectName')} with {payload.get('nSubjects')} subjects. Language={payload.get('language')}"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{OLLAMA_BASE}/api/completions", json={"model": "mxbai-13b", "prompt": prompt})
            text = None
            try:
                text = resp.json()
            except Exception:
                text = resp.text

        out_dir = UPLOADS / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"result.txt"
        with out_file.open("w", encoding="utf-8") as f:
            f.write(str(text))

        # Create zip
        zip_path = UPLOADS / f"{job_id}.zip"
        import zipfile
        with zipfile.ZipFile(zip_path, "w") as z:
            z.write(out_file, arcname=out_file.name)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["path"] = str(zip_path)
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.post("/api/ollama/generate")
@app.post("/ollama/generate")
@app.post("/cdisc/api/ollama/generate")
async def generate(req: GenerateRequest, background: BackgroundTasks):
    job_id = uuid.uuid4().hex
    jobs[job_id] = {"status": "queued"}
    background.add_task(run_job, job_id, req.model_dump())
    return {"job_id": job_id}


@app.get("/api/ollama/status/{job_id}")
@app.get("/ollama/status/{job_id}")
@app.get("/cdisc/api/ollama/status/{job_id}")
async def status(job_id: str):
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(status_code=404, detail="job not found")
    return {"status": j.get("status"), "error": j.get("error")}


@app.get("/api/ollama/exports/{job_id}/download")
@app.get("/ollama/exports/{job_id}/download")
@app.get("/cdisc/api/ollama/exports/{job_id}/download")
async def download(job_id: str):
    j = jobs.get(job_id)
    if not j or j.get("status") != "completed":
        raise HTTPException(status_code=404, detail="export not ready")
    path = j.get("path")
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path, media_type="application/zip", filename=Path(path).name)


@app.get("/api/ollama/llm_health")
@app.get("/ollama/llm_health")
@app.get("/cdisc/api/ollama/llm_health")
async def llm_health():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{OLLAMA_BASE}/api/tags")
            if r.status_code == 200:
                return {"status": "ok", "detail": "ollama reachable"}
            return {"status": "unhealthy", "detail": r.text}
    except Exception as e:
        return {"status": "unhealthy", "detail": str(e)}
