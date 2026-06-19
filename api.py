"""
DocFlow API — programmatic access to MarkItDown conversion.

Run with:
    uvicorn api:app --reload --port 8000

Endpoints:
    POST /convert         -> upload a file, get back Markdown text + stats
    POST /convert-url      -> pass {"url": "..."} JSON, get back Markdown text + stats
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from markitdown import MarkItDown
import os
import tempfile
import time

app = FastAPI(title="DocFlow API", description="Convert documents to Markdown via MarkItDown.")


class UrlRequest(BaseModel):
    url: str


def _stats(text: str):
    return {
        "word_count": len(text.split()),
        "char_count": len(text),
        "estimated_tokens": max(1, len(text) // 4),
    }


@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.name if hasattr(file, "name") else file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        start = time.time()
        md = MarkItDown()
        result = md.convert(tmp_path)
        elapsed = time.time() - start

        return {
            "filename": file.filename,
            "markdown": result.text_content,
            "conversion_time_sec": round(elapsed, 3),
            **_stats(result.text_content),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/convert-url")
async def convert_url(payload: UrlRequest):
    try:
        start = time.time()
        md = MarkItDown()
        result = md.convert(payload.url)
        elapsed = time.time() - start

        return {
            "url": payload.url,
            "markdown": result.text_content,
            "conversion_time_sec": round(elapsed, 3),
            **_stats(result.text_content),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion failed: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}
