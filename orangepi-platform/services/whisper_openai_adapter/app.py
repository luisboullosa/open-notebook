from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL", "http://whisper:9000").rstrip("/")
WHISPER_ASR_PATH = os.getenv("WHISPER_ASR_PATH", "/asr")

app = FastAPI(title="whisper-openai-adapter")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models")
async def list_models() -> dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": "whisper-1",
                "object": "model",
                "owned_by": "open_notebook_local",
            }
        ],
    }


async def _forward_to_whisper(*, file: UploadFile, language: str | None, task: str) -> str:
    audio_bytes = await file.read()
    files = {
        "audio_file": (
            file.filename or "audio.wav",
            audio_bytes,
            file.content_type or "application/octet-stream",
        )
    }
    data: dict[str, str] = {"task": task, "output": "json"}
    if language:
        data["language"] = language

    asr_url = f"{WHISPER_BASE_URL}{WHISPER_ASR_PATH}"
    timeout = httpx.Timeout(120.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(asr_url, files=files, data=data)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    text = ""
    content_type = response.headers.get("content-type", "")

    if "application/json" in content_type:
        payload = response.json()
        if isinstance(payload, dict):
            text = str(payload.get("text") or "")
    else:
        text = response.text.strip()

    return str(text)


@app.post("/v1/audio/transcriptions")
async def transcriptions(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    language: str | None = Form(None),
    response_format: str = Form("json"),
    prompt: str | None = Form(None),
    temperature: float | None = Form(None),
) -> Any:
    _ = (model, prompt, temperature)
    text = await _forward_to_whisper(file=file, language=language, task="transcribe")

    if response_format == "text":
        return PlainTextResponse(content=text)

    return JSONResponse(content={"text": text})


@app.post("/v1/audio/translations")
async def translations(
    file: UploadFile = File(...),
    model: str = Form("whisper-1"),
    response_format: str = Form("json"),
    prompt: str | None = Form(None),
    temperature: float | None = Form(None),
) -> Any:
    _ = (model, prompt, temperature)
    text = await _forward_to_whisper(file=file, language=None, task="translate")

    if response_format == "text":
        return PlainTextResponse(content=text)

    return JSONResponse(content={"text": text})