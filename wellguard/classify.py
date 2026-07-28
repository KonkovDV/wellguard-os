from __future__ import annotations
import numpy as np
import pandas as pd
from .physics import physics_features, detect_mode_changes
from .detect import zscore, cusum, first_sustained
from .schema import qc_report, QUALITY_COL, MODE_COL, coerce_telemetry

# Physics-guided rule layer (governs). Auxiliary ML in benchmark does not override.
# Method lineage: SPE 230862 / SPE 229219 (rules first, sparse labels, mode vs fault);
# gas: Sci. Reports 2026 (PIP drop/osc) + Appl. Sci. nodal gas-lock field pattern (PIP↑+WHP↓
# with amp osc) — both map to letter class gas_interference, not gas-lock confirmation.
# Plugging: JPEPT 2024 (rate↓+PIP↑, low amp osc). No RUL, no control — letter freeze.

WARMUP = 150
HOLD = 20
TAIL = 90
REF = 45


def _sustained_mean(z: np.ndarray, tail: int) -> float:
    return float(np.nanmean(z[-tail:]))


def _absolute_gas(feat: pd.DataFrame) -> tuple[bool, int]:
    """Warmup-poison resistant gas check: tail vs short head reference."""
    cv = feat["current_var"].to_numpy(dtype=float)
    intake = feat["intake_p_bar"].to_numpy(dtype=float)
    if not np.isfinite(intake).any():
        return False, -1
    n = len(cv)
    ref_n = min(REF, max(20, n // 10))
    if n < ref_n + HOLD:
        return False, -1
    ref_cv = float(np.nanmedian(cv[:ref_n]))
    ref_in = float(np.nanmedian(intake[:ref_n]))
    if not np.isfinite(ref_in):
        return False, -1
    cond = (cv > (ref_cv + 1.5)) & (intake < (ref_in - 3.0))
    onset = first_sustained(cond, HOLD)
    tail_cv = float(np.nanmean(cv[-TAIL:]))
    tail_in = float(np.nanmean(intake[-TAIL:]))
    ok = onset >= 0 and tail_cv > ref_cv + 1.5 and tail_in < ref_in - 3.0
    return ok, onset


def _declared_mode_shift(df: pd.DataFrame, warmup: int) -> int:
    if MODE_COL not in df.columns or len(df) <= warmup + 1:
        return -1
    modes = df[MODE_COL].astype(str).str.lower().to_numpy()
    shift_targets = {"transition", "workover", "ramp", "frequency_change", "startup", "shutdown"}
    for i in range(max(warmup, 1), len(modes)):
        if modes[i] != modes[i - 1] and modes[i] in shift_targets:
            return int(i)
    return -1


def _consistency_bundle(s: dict) -> dict:
    """Explainable cross-channel summary for the operator card (SPE 230862-style evidence)."""
    return {
        "q_per_freq_z": round(s.get("q_per_freq", 0.0), 2),
        "current_per_freq_z": round(s.get("current_per_freq", 0.0), 2),
        "head_coef_z": round(s.get("head_coef", 0.0), 2),
        "current_var_z": round(s.get("current_var", 0.0), 2),
        "intake_var_z": round(s.get("intake_var", 0.0), 2),
    }


def _gas_supports(s: dict) -> dict:
    """Optional multi-channel supports within gas_interference (not new classes)."""
    casing_support = bool(np.isfinite(s["casing_p_bar"]) and s["casing_p_bar"] > 1.5)
    rate_support = bool(s["q_liq_m3d"] < -1.5 or s["q_per_freq"] < -1.5)
    pip_osc_support = bool(np.isfinite(s.get("intake_var", 0.0)) and s["intake_var"] > 1.5)
    cooling_support = bool(s.get("motor_t_c", 0.0) > 1.2)
    whp_drop_support = bool(s.get("whp_bar", 0.0) < -1.5)
    return {
        "casing_support": casing_support,
        "rate_support": rate_support,
        "pip_osc_support": pip_osc_support,
        "cooling_support": cooling_support,
        "whp_drop_support": whp_drop_support,
    }


def _optional_channel_rise(df: pd.DataFrame, col: str, warmup: int, delta: float) -> bool:
    if col not in df.columns:
        return False
    x = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(x).any():
        return False
    head = float(np.nanmedian(x[:max(30, warmup // 2)]))
    tail = float(np.nanmean(x[-TAIL:]))
    return np.isfinite(head) and np.isfinite(tail) and (tail - head) > delta


def _sensor_coverage(qc: dict, intake_available: bool) -> dict:
    """SPE 230862-style sparse-sensor transparency (no accuracy claim)."""
    return {
        "intake_available": intake_available,
        "present_optional_extras": list(qc.get("present_optional_extras") or []),
        "schema_ok": bool(qc.get("schema_ok")),
    }


def classify(df: pd.DataFrame) -> dict:
    df = coerce_telemetry(df)
    qc = qc_report(df)
    if not qc["schema_ok"]:
        return {"event_class": "sensor_quality_issue", "onset_index": -1,
                "confidence": 0.0, "is_complication": False, "qc": qc,
                "tail_completeness": qc["completeness"],
                "drivers": {"issues": qc["issues"]}}
    feat = physics_features(df)
    n = len(feat)
    warmup = min(WARMUP, max(30, n // 4))
    intake_available = bool(qc.get("intake_available")) and bool(np.isfinite(
        feat["intake_p_bar"].to_numpy(dtype=float)
    ).any())

    if QUALITY_COL in df.columns:
        qv = pd.to_numeric(df[QUALITY_COL], errors="coerce").to_numpy(dtype=float)
        qv = np.where(np.isfinite(qv), qv, 0.0)
        qv = np.clip(qv, 0.0, 1.0)
        tail_completeness = float(qv[-TAIL:].mean())
    else:
        tail_completeness = qc["completeness"]

    z_cols = ["head_coef", "q_per_freq", "current_per_freq", "current_per_q", "current_var",
              "intake_var", "intake_p_bar", "whp_bar", "casing_p_bar", "current_a", "load_pct",
              "q_liq_m3d", "motor_t_c"]
    z = {c: zscore(feat[c].to_numpy(dtype=float), warmup) for c in z_cols}

    mode_changes = detect_mode_changes(feat["freq_n"].to_numpy(dtype=float))
    late_mode_idxs = mode_changes[mode_changes > warmup]
    late_mode_change = late_mode_idxs.size > 0
    declared_shift = _declared_mode_shift(df, warmup)
    current_mode = str(df[MODE_COL].iloc[-1]) if MODE_COL in df.columns else "unknown"

    s = {c: _sustained_mean(z[c], TAIL) for c in z}

    result = {
        "event_class": "normal",
        "onset_index": -1,
        "confidence": 0.0,
        "is_complication": False,
        "qc": qc,
        "tail_completeness": round(tail_completeness, 3),
        "drivers": {"operating_mode": current_mode, "intake_available": intake_available,
                    "sensor_coverage": _sensor_coverage(qc, intake_available),
                    "consistency": _consistency_bundle(s)},
    }

    if tail_completeness < 0.6:
        result["event_class"] = "sensor_quality_issue"
        result["confidence"] = 0.5
        result["drivers"] = {
            "reason": "tail_completeness_below_threshold",
            "tail_completeness": round(tail_completeness, 3),
            "issues": qc.get("issues", []),
            "operating_mode": current_mode,
        }
        return result

    # Affinity-consistent freq step: rate and current track speed (liquid-dominated).
    affinity_consistent = abs(s["q_per_freq"]) < 3.0 and abs(s["current_per_freq"]) < 3.5
    coverage = _sensor_coverage(qc, intake_available)
    gas_factor_support = (
        _optional_channel_rise(df, "gas_factor_m3m3", warmup, 5.0)
        or _optional_channel_rise(df, "gas_rate_m3d", warmup, 50.0)
    )

    # 2) gas interference — two field-aligned PIP modes, one letter class
    if intake_available:
        supports = _gas_supports(s)
        supports["gas_factor_support"] = bool(gas_factor_support)
        support_boost = 0.05 * sum(1 for v in supports.values() if v)

        # Mode A: amp osc + PIP drop (Sci. Reports / interference)
        gas_cond = (z["current_var"] > 4.0) & (z["intake_p_bar"] < -2.0)
        gas_onset = first_sustained(gas_cond, HOLD)
        if gas_onset >= 0 and s["current_var"] > 3.0:
            c = cusum(z["current_var"], k=1.0, positive=True)
            conf = float(np.clip(c[-1] / 200.0 + support_boost, 0.3, 0.95))
            result.update(event_class="gas_interference", onset_index=gas_onset,
                          is_complication=True, confidence=conf,
                          drivers={"detector": "pip_drop_osc",
                                   "current_var_z": round(s["current_var"], 2),
                                   "head_coef_z": round(s["head_coef"], 2),
                                   **supports,
                                   "operating_mode": current_mode,
                                   "sensor_coverage": coverage,
                                   "consistency": _consistency_bundle(s)})
            return result

        # Mode B: amp osc + PIP rise + WHP drop (nodal gas-lock field pattern; ≠ plugging)
        gas_lock_cond = (
            (z["current_var"] > 4.0) & (z["intake_p_bar"] > 2.0) & (z["whp_bar"] < -1.5)
        )
        gas_lock_onset = first_sustained(gas_lock_cond, HOLD)
        if gas_lock_onset >= 0 and s["current_var"] > 3.0 and s["intake_p_bar"] > 1.5:
            c = cusum(z["current_var"], k=1.0, positive=True)
            conf = float(np.clip(c[-1] / 200.0 + support_boost, 0.3, 0.95))
            result.update(event_class="gas_interference", onset_index=gas_lock_onset,
                          is_complication=True, confidence=conf,
                          drivers={"detector": "pip_rise_whp_drop_osc",
                                   "current_var_z": round(s["current_var"], 2),
                                   "intake_z": round(s["intake_p_bar"], 2),
                                   "whp_z": round(s["whp_bar"], 2),
                                   **supports,
                                   "operating_mode": current_mode,
                                   "sensor_coverage": coverage,
                                   "consistency": _consistency_bundle(s)})
            return result

        abs_gas_ok, abs_gas_onset = _absolute_gas(feat)
        if abs_gas_ok:
            conf = float(min(0.9, 0.55 + support_boost))
            result.update(event_class="gas_interference", onset_index=int(abs_gas_onset),
                          is_complication=True, confidence=conf,
                          drivers={"detector": "absolute_head_tail",
                                   "current_var_z": round(s["current_var"], 2),
                                   **supports,
                                   "operating_mode": current_mode,
                                   "sensor_coverage": coverage,
                                   "consistency": _consistency_bundle(s)})
            return result

    # 3) sensor-fault: intake moved; rate/power AND wellhead quiet (channel-local)
    if intake_available:
        intake_moved = abs(s["intake_p_bar"]) > 3.0
        coupling_quiet = (abs(s["q_liq_m3d"]) < 1.5 and abs(s["current_a"]) < 1.5
                          and abs(s["load_pct"]) < 1.5)
        whp_quiet = abs(s["whp_bar"]) < 1.8
        if intake_moved and coupling_quiet and whp_quiet:
            cond = np.abs(z["intake_p_bar"]) > 2.5
            onset = first_sustained(cond, HOLD)
            if onset >= 0:
                result.update(event_class="sensor_fault_suspected",
                              onset_index=int(onset),
                              confidence=0.6,
                              drivers={"intake_z": round(s["intake_p_bar"], 2),
                                       "coupling": "quiet",
                                       "whp_quiet": True,
                                       "operating_mode": current_mode,
                                       "sensor_coverage": coverage,
                                       "consistency": _consistency_bundle(s)})
                return result

    # 4) intake restriction / plugging: rate+load down, low amp osc (≠ gas Mode B)
    restr_cond = (z["q_per_freq"] < -3.0) & (z["load_pct"] < -2.0) & (z["current_var"] < 3.5)
    restr_onset = first_sustained(restr_cond, HOLD)
    if restr_onset >= 0 and s["q_per_freq"] < -2.5 and s["current_var"] < 3.0:
        c = cusum(z["q_per_freq"], k=1.0, positive=False)
        pip_rise_support = bool(intake_available and s["intake_p_bar"] > 2.0)
        head_support = bool(s["head_coef"] > 2.0 or s["head_coef"] < -2.0)
        annulus_support = bool(np.isfinite(s["casing_p_bar"]) and s["casing_p_bar"] > 1.5)
        underload_support = bool(s["load_pct"] < -2.0 and s["current_a"] < -1.5)
        boost = 0.05 * sum(
            1 for v in (pip_rise_support, head_support, annulus_support, underload_support) if v
        )
        conf = float(np.clip(c[-1] / 200.0 + boost, 0.3, 0.95))
        result.update(event_class="intake_restriction", onset_index=restr_onset,
                      is_complication=True, confidence=conf,
                      drivers={"q_per_freq_z": round(s["q_per_freq"], 2),
                               "load_z": round(s["load_pct"], 2),
                               "pip_rise_support": pip_rise_support,
                               "head_support": head_support,
                               "annulus_support": annulus_support,
                               "underload_support": underload_support,
                               "operating_mode": current_mode,
                               "sensor_coverage": coverage,
                               "consistency": _consistency_bundle(s)})
        return result

    # 5) water breakthrough candidate; water_cut only reinforces
    wb_cond = (z["current_per_q"] > 2.0) & (z["motor_t_c"] > 2.0)
    wb_onset = first_sustained(wb_cond, HOLD)
    water_cut_support = False
    if "water_cut_pct" in df.columns:
        wc = pd.to_numeric(df["water_cut_pct"], errors="coerce").to_numpy(dtype=float)
        if np.isfinite(wc).any():
            head = float(np.nanmedian(wc[:max(30, warmup // 2)]))
            tail = float(np.nanmean(wc[-TAIL:]))
            water_cut_support = np.isfinite(head) and np.isfinite(tail) and (tail - head) > 2.0
    if (wb_onset >= 0 and s["current_per_q"] > 1.5 and s["motor_t_c"] > 1.5
            and abs(s["q_per_freq"]) < 2.0):
        result.update(event_class="water_breakthrough_candidate", onset_index=int(wb_onset),
                      is_complication=True,
                      confidence=0.6 if water_cut_support else 0.55,
                      drivers={"current_per_q_z": round(s["current_per_q"], 2),
                               "motor_t_z": round(s["motor_t_c"], 2),
                               "water_cut_support": bool(water_cut_support),
                               "operating_mode": current_mode,
                               "sensor_coverage": coverage,
                               "consistency": _consistency_bundle(s)})
        return result

    # 6) operation change
    if (late_mode_change or declared_shift >= 0) and affinity_consistent and s["current_var"] < 3.0:
        onset = int(late_mode_idxs[0]) if late_mode_change else int(declared_shift)
        result.update(event_class="operation_change", onset_index=onset,
                      confidence=0.8,
                      drivers={"freq_step": bool(late_mode_change),
                               "declared_mode_shift": declared_shift >= 0,
                               "affinity_consistent": True,
                               "operating_mode": current_mode,
                               "sensor_coverage": coverage,
                               "consistency": _consistency_bundle(s)})
        return result

    return result
