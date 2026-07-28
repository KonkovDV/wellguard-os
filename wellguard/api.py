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
MAX_COLUMNS = 256


if FastAPI is not None:
    app = FastAPI(
        title="WellGuard OS",
        version=__version__,
        description=(
            "Advisory-only ESP well surveillance. Read-only. Never actuates. "
            "Cards are reasons to check — not failure/accident confirmation."
        ),
    )

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "version": __version__,
            "advisory_only": True,
            "actuation": "never",
            "field_accuracy_claimed": False,
        }

    @app.get("/demo/{scenario}")
    def demo(scenario: str, seed: int = 0):
        if scenario not in SCENARIOS:
            raise HTTPException(404, f"unknown scenario; choose {SCENARIOS}")
        if seed < 0 or seed > 10_000:
            raise HTTPException(400, "seed out of allowed range 0..10000")
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
        if df.empty:
            raise HTTPException(400, "empty CSV")
        if len(df) > MAX_ROWS:
            raise HTTPException(413, "too many rows; max 2,000,000")
        if len(df.columns) > MAX_COLUMNS:
            raise HTTPException(413, f"too many columns; max {MAX_COLUMNS}")
        try:
            return run(df)  # read-only: nothing is persisted or actuated
        except Exception as e:
            raise HTTPException(422, f"telemetry rejected: {e}") from e
