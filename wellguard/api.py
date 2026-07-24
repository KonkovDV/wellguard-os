from __future__ import annotations
import io
import pandas as pd
try:
    from fastapi import FastAPI, UploadFile, File, HTTPException
except Exception:  # fastapi optional at import time
    FastAPI = None

from .pipeline import run
from .generator import generate, SCENARIOS
from . import __version__

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_ROWS = 2_000_000


if FastAPI is not None:
    app = FastAPI(title="WellGuard OS", version=__version__,
                  description="Advisory-only ESP well surveillance. Read-only. Never actuates.")

    @app.get("/health")
    def health():
        return {"status": "ok", "version": __version__, "advisory_only": True}

    @app.get("/demo/{scenario}")
    def demo(scenario: str, seed: int = 0):
        if scenario not in SCENARIOS:
            raise HTTPException(404, f"unknown scenario; choose {SCENARIOS}")
        return run(generate(scenario, seed=seed))

    @app.post("/screen")
    async def screen(file: UploadFile = File(...)):
        raw = await file.read()
        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "file too large; max 25 MiB")
        # Reject oversized payloads before allocating a full DataFrame.
        if raw.count(b"\n") > MAX_ROWS + 1:
            raise HTTPException(413, "too many rows; max 2,000,000")
        try:
            df = pd.read_csv(io.BytesIO(raw))
        except Exception as e:
            raise HTTPException(400, f"invalid CSV: {e}") from e
        if len(df) > MAX_ROWS:
            raise HTTPException(413, "too many rows; max 2,000,000")
        return run(df)  # read-only: nothing is persisted or actuated
