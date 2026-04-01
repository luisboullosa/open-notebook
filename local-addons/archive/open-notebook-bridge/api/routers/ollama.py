from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from api.command_service import CommandService
from open_notebook.config import UPLOADS_FOLDER
from pathlib import Path
from loguru import logger
from api.ollama_service import check_openai_compatible

router = APIRouter()


class GenerateRequest(BaseModel):
    projectName: str
    language: str = "R"
    nSubjects: int = 50
    sdtmDomains: list = []
    adamDomains: list = []
    messTypes: list = []
    messinessLevel: int = 1


@router.post("/ollama/generate")
async def generate_endpoint(req: GenerateRequest):
    try:
        job_id = await CommandService.submit_command_job(
            "open_notebook", "generate_ollama_export", req.model_dump()
        )
        return {"job_id": job_id}
    except Exception as e:
        logger.error(f"Failed to submit Ollama export job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama/status/{job_id}")
async def status(job_id: str):
    try:
        st = await CommandService.get_command_status(job_id)
        return st
    except Exception as e:
        logger.error(f"Failed to get status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama/exports/{job_id}/download")
async def download_export(job_id: str):
    # Exports are written to data/uploads/ollama_exports with timestamped filenames.
    out_dir = Path(UPLOADS_FOLDER) / "ollama_exports"
    if not out_dir.exists():
        raise HTTPException(status_code=404, detail="No exports found")
    # Find the newest file matching job_id substring (best-effort)
    matches = sorted(out_dir.glob(f"*{job_id}*.zip"), reverse=True)
    if not matches:
        # Fallback: return latest file
        files = sorted(out_dir.glob("*.zip"), reverse=True)
        if not files:
            raise HTTPException(status_code=404, detail="No export artifacts available")
        path = files[0]
    else:
        path = matches[0]

    return FileResponse(path, media_type="application/zip", filename=path.name)


@router.get("/ollama/llm_health")
async def llm_health():
    try:
        res = await check_openai_compatible()
        if res.get("ok"):
            return {"status": "ok", "detail": res.get("detail")}
        raise HTTPException(status_code=503, detail=res.get("detail"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
