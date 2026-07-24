"""Explicit adapters for public/customer telemetry schemas.

No network access, unit guessing, or silent imputation. Missing channels remain
visible to the QC gate and result in sensor_quality_issue.
"""
from __future__ import annotations
import pandas as pd
from .schema import CHANNELS

def map_columns(df: pd.DataFrame, mapping: dict[str, str], *, source_pressure_unit: str = "bar") -> pd.DataFrame:
    out = df.rename(columns=mapping).copy()
    if source_pressure_unit == "psi":
        for c in ("whp_bar", "intake_p_bar", "casing_p_bar"):
            if c in out:
                out[c] = pd.to_numeric(out[c], errors="coerce") * 0.0689475729
    elif source_pressure_unit != "bar":
        raise ValueError("source_pressure_unit must be 'bar' or 'psi'")
    return out

def validate_canonical(df: pd.DataFrame) -> list[str]:
    return [c for c in CHANNELS if c not in df.columns]
