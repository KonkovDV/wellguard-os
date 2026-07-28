from __future__ import annotations
import numpy as np
import pandas as pd

# Canonical telemetry contract aligned with INDUSTRIX application letter (frozen claims).
# Intake pressure is optional ("если доступно"); operating_mode is a declared mode label.

REQUIRED_CHANNELS = [
    "t_min",        # time axis (minutes since start or equivalent monotonic scale)
    "freq_hz",      # ESP drive frequency
    "whp_bar",      # wellhead pressure
    "current_a",    # motor current
    "load_pct",     # motor load
    "q_liq_m3d",    # liquid rate
    "motor_t_c",    # motor temperature
    "casing_p_bar", # annulus/casing head pressure
    "operating_mode",  # declared operating regime label (steady/transition/…)
]

# Used when present; absence degrades gas/sensor-fault paths but does not fail schema.
CONDITIONAL_CHANNELS = [
    "intake_p_bar",  # pump intake pressure — optional if unavailable
]

# Reserved extras from the application letter / archive contract (passthrough + future use).
OPTIONAL_EXTRA_CHANNELS = [
    "water_cut_pct",
    "gas_rate_m3d",
    "gas_factor_m3m3",
    "vibration_rms",
    "esp_start_stop",      # 1 = start/stop event window
    "existing_alarm",      # 1 = plant alarm active
    "daily_report_flag",   # 1 = linked daily-report row
    "operator_annotation", # short coded note / hash, not free-text PII
    "intervention_flag",   # 1 = intervention recorded
]

# Numeric channels coerced for physics (excludes operating_mode and flags/text extras).
NUMERIC_CHANNELS = [
    "t_min", "freq_hz", "whp_bar", "intake_p_bar", "current_a", "load_pct",
    "q_liq_m3d", "motor_t_c", "casing_p_bar",
    "water_cut_pct", "gas_rate_m3d", "gas_factor_m3m3", "vibration_rms",
    "esp_start_stop", "existing_alarm", "daily_report_flag", "intervention_flag",
]

# Backward-compatible alias: full preferred set for demos/docs.
CHANNELS = REQUIRED_CHANNELS[:-1] + CONDITIONAL_CHANNELS + ["operating_mode"]

QUALITY_COL = "quality_ok"  # 1 good sample, 0 bad/missing
MODE_COL = "operating_mode"

EXPECTED_UNITS = {
    "t_min": "min",
    "freq_hz": "Hz",
    "whp_bar": "bar",
    "intake_p_bar": "bar",
    "current_a": "A",
    "load_pct": "%",
    "q_liq_m3d": "m3/d",
    "motor_t_c": "°C",
    "casing_p_bar": "bar",
    "water_cut_pct": "%",
    "gas_rate_m3d": "m3/d",
    "gas_factor_m3m3": "m3/m3",
    "vibration_rms": "mm/s",
}

RANGES = {
    "freq_hz": (10, 90),
    "whp_bar": (0, 200),
    "intake_p_bar": (0, 400),
    "current_a": (0, 400),
    "load_pct": (0, 130),
    "q_liq_m3d": (0, 2000),
    "motor_t_c": (0, 250),
    "casing_p_bar": (0, 200),
    "water_cut_pct": (0, 100),
    "gas_rate_m3d": (0, 50000),
    "gas_factor_m3m3": (0, 2000),
    "vibration_rms": (0, 100),
}


def coerce_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce known numeric channels to float64 once. Invalid values become NaN."""
    out = df.copy()
    for c in NUMERIC_CHANNELS:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    if QUALITY_COL in out.columns:
        out[QUALITY_COL] = pd.to_numeric(out[QUALITY_COL], errors="coerce")
    if MODE_COL in out.columns:
        out[MODE_COL] = out[MODE_COL].astype(str).str.strip().str.lower()
    return out


def _timeline_issues(df: pd.DataFrame) -> list[str]:
    """Monotonic time axis and large-gap checks (letter: проверка временной шкалы)."""
    issues: list[str] = []
    if "t_min" not in df.columns or len(df) < 2:
        return issues
    t = pd.to_numeric(df["t_min"], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(t).all():
        issues.append("timeline_non_finite")
        return issues
    d = np.diff(t)
    if np.any(d < 0):
        issues.append(f"timeline_not_monotonic:{int((d < 0).sum())}")
    if np.any(d == 0):
        issues.append(f"timeline_duplicate_stamps:{int((d == 0).sum())}")
    pos = d[d > 0]
    if len(pos) >= 10:
        med = float(np.median(pos))
        if med > 0:
            big = int((d > max(5.0 * med, med + 30.0)).sum())
            if big:
                issues.append(f"timeline_large_gaps:{big}")
    return issues


def qc_report(df: pd.DataFrame) -> dict:
    """Schema, timeline, unit-range and completeness checks. Returns a QC dict."""
    issues: list[str] = []
    warnings: list[str] = []

    for c in REQUIRED_CHANNELS:
        if c not in df.columns:
            issues.append(f"missing_channel:{c}")

    for c in CONDITIONAL_CHANNELS:
        if c not in df.columns:
            warnings.append(f"missing_optional:{c}")

    present_extras = [c for c in OPTIONAL_EXTRA_CHANNELS if c in df.columns]

    out_of_range = 0
    numeric_missing = 0
    for c, (lo, hi) in RANGES.items():
        if c in df.columns:
            v = pd.to_numeric(df[c], errors="coerce")
            numeric_missing += int((~np.isfinite(v.to_numpy())).sum())
            out_of_range += int(((v < lo) | (v > hi)).sum())

    if len(df) < 30:
        issues.append(f"insufficient_history:{len(df)}")

    issues.extend(_timeline_issues(df))

    if MODE_COL in df.columns:
        modes = df[MODE_COL].astype(str).str.strip()
        if modes.eq("").any() | modes.str.lower().isin(["nan", "none"]).any():
            issues.append("invalid_operating_mode")

    if "operator_annotation" in df.columns:
        # Coded notes only — reject long free-text that may carry PII.
        lengths = df["operator_annotation"].astype(str).str.len()
        too_long = int((lengths > 64).sum())
        if too_long:
            issues.append(f"operator_annotation_too_long:{too_long}")

    if len(df.columns) > 256:
        issues.append(f"too_many_columns:{len(df.columns)}")

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
        present = [c for c in REQUIRED_CHANNELS + CONDITIONAL_CHANNELS if c in df.columns and c != MODE_COL]
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
        "warnings": warnings,
        "present_optional_extras": present_extras,
        "expected_units": EXPECTED_UNITS,
        "out_of_range": int(out_of_range),
        "numeric_missing": int(numeric_missing),
        "completeness": round(completeness, 4),
        "intake_available": "intake_p_bar" in df.columns,
        "schema_ok": len(issues) == 0 and len(df) > 0,
    }
