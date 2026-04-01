"""Simple Ollama HTTP wrapper and helpers for generating scripts/CSVs and zipping outputs."""
from typing import Dict, Any, Optional
import os
import json
from loguru import logger
import httpx

OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
# OpenAI-compatible endpoint (rk-llama.cpp or other providers)
OPENAI_COMPATIBLE_BASE = os.getenv("OPENAI_COMPATIBLE_BASE_URL_LLM")
# Feature flag to prefer Ollama when available
ENABLE_OLLAMA = os.getenv("ENABLE_OLLAMA", "true").lower() in ("1", "true", "yes")


async def call_ollama(prompt: str, model: str = "mxbai-13b") -> str:
    """Call Ollama's simple completions endpoint and return text."""
    url = f"{OLLAMA_API_BASE}/api/completions"
    payload = {"model": model, "prompt": prompt}
    timeout = httpx.Timeout(connect=10.0, read=600.0, write=30.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            j = resp.json()
            # Ollama returns 'content' or similar; attempt common shapes
            if isinstance(j, dict) and "content" in j:
                return j["content"]
            if isinstance(j, dict) and "completion" in j:
                return j["completion"]
            # Fallback: stringify
            return json.dumps(j)
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")
        raise


async def call_openai_compatible(prompt: str, model: str = "gpt-3.5") -> str:
    """Call an OpenAI-compatible LLM endpoint (rk-llama.cpp) and return text."""
    if not OPENAI_COMPATIBLE_BASE:
        raise RuntimeError("OPENAI_COMPATIBLE_BASE_URL_LLM is not configured")
    # Try Chat Completions first
    url = OPENAI_COMPATIBLE_BASE.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 2048,
    }
    timeout = httpx.Timeout(connect=10.0, read=600.0, write=30.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            j = resp.json()
            # Common response shapes
            if isinstance(j, dict):
                # Chat completions
                choices = j.get("choices") or []
                if choices:
                    first = choices[0]
                    # message style
                    msg = first.get("message")
                    if isinstance(msg, dict) and "content" in msg:
                        return msg["content"]
                    if "text" in first:
                        return first["text"]
            return json.dumps(j)
    except Exception as e:
        logger.error(f"OpenAI-compatible call failed: {e}")
        raise


async def check_openai_compatible() -> dict:
    """Lightweight health check for the OpenAI-compatible LLM endpoint.

    Returns a dict with keys: ok (bool), url, detail (optional)
    """
    if not OPENAI_COMPATIBLE_BASE:
        return {"ok": False, "detail": "OPENAI_COMPATIBLE_BASE_URL_LLM not configured"}
    url = OPENAI_COMPATIBLE_BASE.rstrip('/') + '/v1/models'
    timeout = httpx.Timeout(connect=2.0, read=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except Exception:
                    data = {"status": "ok"}
                return {"ok": True, "url": url, "detail": data}
            else:
                return {"ok": False, "url": url, "detail": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        logger.warning(f"OpenAI-compatible healthcheck failed: {e}")
        return {"ok": False, "url": url, "detail": str(e)}


async def generate_project_files(config: Dict[str, Any], model: Optional[str] = None) -> Dict[str, bytes]:
    """High-level helper that asks the model for scripts and returns a mapping filename->bytes.

    For each domain in config the service will request a script. The service returns
    a dict where keys are relative filenames (e.g. scripts/DM_pipeline.R) and values are bytes.
    """
    model = model or config.get("model") or "mxbai-13b"
    results: Dict[str, bytes] = {}

    base_ctx = (
        f"Study: {config.get('projectName','STUDY')}. Language: {config.get('language','R')}. N subjects: {config.get('nSubjects',50)}"
    )

    domains = list(config.get("sdtmDomains", [])) + list(config.get("adamDomains", []))
    for d in domains:
        prompt = f"{base_ctx}\n\nWrite a heavily annotated {config.get('language','R')} pipeline script for the CDISC {d}.\nReturn ONLY the script code."
        # Prefer OpenAI-compatible rk-llama endpoint on Orange Pi when Ollama is disabled
        if not ENABLE_OLLAMA and OPENAI_COMPATIBLE_BASE:
            # use a small default model name if not provided
            model_name = config.get("model") or os.getenv("OPENAI_COMPATIBLE_DEFAULT_MODEL", model)
            text = await call_openai_compatible(prompt, model=model_name)
        else:
            text = await call_ollama(prompt, model=model)
        ext = "R" if config.get("language","R").upper() == "R" else "py"
        filename = f"scripts/{d.lower()}_pipeline.{ext}"
        results[filename] = text.encode("utf-8")

    # Add a small CSV example to show expected CSV output (empty or sample)
    sample_csv = "subject_id,visit,measure\n"
    for i in range(min(5, int(config.get("nSubjects", 50)))):
        sample_csv += f"SUBJ{i+1},V1,12.3\n"
    results["data/example.csv"] = sample_csv.encode("utf-8")

    # Simple project README
    readme = f"# {config.get('projectName','STUDY')}\nGenerated by Open Notebook Ollama bridge.\n"
    results["README.md"] = readme.encode("utf-8")

    return results
