import time
from typing import Any, Dict, Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.config import UPLOADS_FOLDER
from api.ollama_service import generate_project_files

import zipfile
from pathlib import Path


class OllamaExportInput(CommandInput):
    projectName: str
    language: str = "R"
    nSubjects: int = 50
    sdtmDomains: list = []
    adamDomains: list = []
    messTypes: list = []
    messinessLevel: int = 1


class OllamaExportOutput(CommandOutput):
    success: bool
    job_id: Optional[str]
    export_path: Optional[str]
    error_message: Optional[str] = None


@command("generate_ollama_export", app="open_notebook")
async def generate_ollama_export(input_data: OllamaExportInput) -> OllamaExportOutput:
    start = time.time()
    job_id = None
    export_path = None
    try:
        cfg = dict(
            projectName=input_data.projectName,
            language=input_data.language,
            nSubjects=input_data.nSubjects,
            sdtmDomains=input_data.sdtmDomains,
            adamDomains=input_data.adamDomains,
            messTypes=input_data.messTypes,
            messinessLevel=input_data.messinessLevel,
        )

        logger.info(f"Generating Ollama export for project {cfg.get('projectName')}")
        files = await generate_project_files(cfg)

        out_dir = Path(UPLOADS_FOLDER) / "ollama_exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        # Use timestamp for filename
        stamp = int(time.time())
        zip_name = f"{cfg.get('projectName')}_{stamp}.zip"
        zip_path = out_dir / zip_name

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for rel, b in files.items():
                zf.writestr(rel, b)

        export_path = str(zip_path)
        elapsed = time.time() - start
        logger.info(f"Export created at {export_path} in {elapsed:.2f}s")

        return OllamaExportOutput(success=True, job_id=job_id, export_path=export_path)

    except Exception as e:
        logger.error(f"Ollama export failed: {e}")
        return OllamaExportOutput(success=False, job_id=job_id, export_path=None, error_message=str(e))
