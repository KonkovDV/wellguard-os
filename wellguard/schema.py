from __future__ import annotations
import numpy as np
import pandas as pd

# Canonical channels expected from routine ESP well telemetry.
CHANNELS = [
    "t_min",       # minutes since start
    "freq_hz",     # ESP drive frequency
    "whp_bar",     # wellhead pressure
    "intake_p_bar",# pump intake pressure (downhole)
    "current_a",   # motor current
    "load_pct",    # motor load
    "q_liq_m3d",   # liquid rate
    "motor_t_c",   # motor temperature
    "casing_p_bar",# annulus/casing head pressure
]

QUALITY_COL = "quality_ok"  # 1 good sample, 0 bad/missing

RANGES = {
    "freq_hz": (10, 90),
    "whp_bar": (0, 200),
    "intake_p_bar": (0, 400),
    "current_a": (0, 400),
    "load_pct": (0, 130),
    "q_liq_m3d": (0, 2000),
    "motor_t_c": (0, 250),
    "casing_p_bar": (0, 200),
}


def coerce_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce known channels to float64 once. Invalid values become NaN (fail-closed via QC)."""
    out = df.copy()
    for c in CHANNELS:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    if QUALITY_COL in out.columns:
        out[QUALITY_COL] = pd.to_numeric(out[QUALITY_COL], errors="coerce")
    return out


def qc_report(df: pd.DataFrame) -> dict:
    """Schema, unit-range and completeness checks. Returns a QC dict."""
    issues: list[str] = []
    for c in CHANNELS:
        if c not in df.columns:
            issues.append(f"missing_channel:{c}")

    out_of_range = 0
    numeric_missing = 0
    for c, (lo, hi) in RANGES.items():
        if c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce")
            numeric_missing += int((~np.isfinite(v.to_numpy())).sum())
            out_of_range += int(((v < lo) | (v > hi)).sum())
    if len(df) < 30:
        issues.append(f"insufficient_history:{len(df)}")

    completeness = 0.0
    if QUALITY_COL in df.columns:
        q = pd.to_numeric(df[QUALITY_COL], errors="coerce")
        qv = q.to_numpy(dtype=float)
        invalid_q = int((~np.isfinite(qv) | (qv < 0.0) | (qv > 1.0)).sum())
        if invalid_q:
            issues.append(f"invalid_quality_ok:{invalid_q}")
        finite = qv[np.isfinite(qv)]
        completeness = float(np.clip(finite.mean(), 0, 1)) if len(finite) else 0.0
    else:
        present = [c for c in CHANNELS if c in df.columns]
        if present:
            completeness = 1.0 - float(
                df[present].apply(pd.to_numeric, errors="coerce").isna().mean().mean()
            )

    if numeric_missing:
        issues.append(f"non_numeric_or_missing:{numeric_missing}")
    if out_of_range:
        issues.append(f"out_of_range:{out_of_range}")

    return {
        "n_rows": int(len(df)),
        "issues": issues,
        "out_of_range": int(out_of_range),
        "numeric_missing": int(numeric_missing),
        "completeness": round(completeness, 4),
        "schema_ok": len(issues) == 0 and len(df) > 0,
    }
