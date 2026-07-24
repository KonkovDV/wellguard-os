from __future__ import annotations
import numpy as np
import pandas as pd
from .physics import physics_features, detect_mode_changes
from .detect import zscore, cusum, first_sustained
from .schema import qc_report, QUALITY_COL, coerce_telemetry

# Physics-guided rule layer. Governs the final event class.
# A calibrated ML score (benchmark.run_benchmark) is auxiliary, never overrides safety.

WARMUP = 150      # minutes of assumed-normal history for the causal baseline
HOLD = 20         # persistence hold-time (minutes) before an event is admitted
TAIL = 90         # trailing window used to judge the current sustained state
REF = 45          # short head used for absolute early-onset fallbacks


def _sustained_mean(z: np.ndarray, tail: int) -> float:
    return float(np.mean(z[-tail:]))


def _absolute_gas(feat: pd.DataFrame) -> tuple[bool, int]:
    """Warmup-poison resistant gas check: tail vs short head reference."""
    cv = feat["current_var"].to_numpy(dtype=float)
    intake = feat["intake_p_bar"].to_numpy(dtype=float)
    n = len(cv)
    ref_n = min(REF, max(20, n // 10))
    if n < ref_n + HOLD:
        return False, -1
    ref_cv = float(np.nanmedian(cv[:ref_n]))
    ref_in = float(np.nanmedian(intake[:ref_n]))
    cond = (cv > (ref_cv + 1.5)) & (intake < (ref_in - 3.0))
    onset = first_sustained(cond, HOLD)
    tail_cv = float(np.nanmean(cv[-TAIL:]))
    tail_in = float(np.nanmean(intake[-TAIL:]))
    ok = onset >= 0 and tail_cv > ref_cv + 1.5 and tail_in < ref_in - 3.0
    return ok, onset


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

    # trailing data-quality gate
    if QUALITY_COL in df.columns:
        qv = pd.to_numeric(df[QUALITY_COL], errors="coerce").to_numpy(dtype=float)
        qv = np.where(np.isfinite(qv), qv, 0.0)
        qv = np.clip(qv, 0.0, 1.0)
        tail_completeness = float(qv[-TAIL:].mean())
    else:
        tail_completeness = qc["completeness"]

    z = {c: zscore(feat[c].to_numpy(dtype=float), warmup) for c in
         ["head_coef", "q_per_freq", "current_per_q", "current_var",
          "intake_p_bar", "current_a", "load_pct", "q_liq_m3d", "motor_t_c"]}

    mode_changes = detect_mode_changes(feat["freq_n"].to_numpy(dtype=float))
    late_mode_idxs = mode_changes[mode_changes > warmup]
    late_mode_change = late_mode_idxs.size > 0

    # sustained trailing means (physics state "now")
    s = {c: _sustained_mean(z[c], TAIL) for c in z}

    result = {
        "event_class": "normal",
        "onset_index": -1,
        "confidence": 0.0,
        "is_complication": False,
        "qc": qc,
        "tail_completeness": round(tail_completeness, 3),
        "drivers": {},
    }

    # 1) hard data-quality gate
    if tail_completeness < 0.6:
        result["event_class"] = "sensor_quality_issue"
        result["confidence"] = 0.5
        result["drivers"] = {
            "reason": "tail_completeness_below_threshold",
            "tail_completeness": round(tail_completeness, 3),
            "issues": qc.get("issues", []),
        }
        return result

    # Rate-tracking check for deliberate frequency steps (head_coef moves with f^2 — not used).
    affinity_consistent = abs(s["q_per_freq"]) < 3.0

    # 2) gas interference — relative z-scores first; absolute head/tail fallback for early onset
    gas_cond = (z["current_var"] > 4.0) & (z["intake_p_bar"] < -2.0)
    gas_onset = first_sustained(gas_cond, HOLD)
    if gas_onset >= 0 and s["current_var"] > 3.0:
        c = cusum(z["current_var"], k=1.0, positive=True)
        result.update(event_class="gas_interference", onset_index=gas_onset,
                      is_complication=True,
                      confidence=float(np.clip(c[-1] / 200.0, 0.3, 0.95)),
                      drivers={"current_var_z": round(s["current_var"], 2),
                               "head_coef_z": round(s["head_coef"], 2)})
        return result

    abs_gas_ok, abs_gas_onset = _absolute_gas(feat)
    if abs_gas_ok:
        result.update(event_class="gas_interference", onset_index=int(abs_gas_onset),
                      is_complication=True, confidence=0.55,
                      drivers={"detector": "absolute_head_tail",
                               "current_var_z": round(s["current_var"], 2)})
        return result

    # 3) sensor-fault suspected: intake moved a lot but rate/power did NOT respond
    intake_moved = abs(s["intake_p_bar"]) > 3.0
    coupling_quiet = (abs(s["q_liq_m3d"]) < 1.5 and abs(s["current_a"]) < 1.5
                      and abs(s["load_pct"]) < 1.5)
    if intake_moved and coupling_quiet:
        cond = np.abs(z["intake_p_bar"]) > 2.5
        onset = first_sustained(cond, HOLD)
        if onset >= 0:
            result.update(event_class="sensor_fault_suspected",
                          onset_index=int(onset),
                          confidence=0.6,
                          drivers={"intake_z": round(s["intake_p_bar"], 2),
                                   "coupling": "quiet"})
            return result

    # 4) intake restriction: sustained rate + load (+ intake) decline together
    restr_cond = (z["q_per_freq"] < -3.0) & (z["load_pct"] < -2.0)
    restr_onset = first_sustained(restr_cond, HOLD)
    if restr_onset >= 0 and s["q_per_freq"] < -2.5:
        c = cusum(z["q_per_freq"], k=1.0, positive=False)
        result.update(event_class="intake_restriction", onset_index=restr_onset,
                      is_complication=True,
                      confidence=float(np.clip(c[-1] / 200.0, 0.3, 0.95)),
                      drivers={"q_per_freq_z": round(s["q_per_freq"], 2),
                               "load_z": round(s["load_pct"], 2)})
        return result

    # 5) water breakthrough candidate: slow current + motor-temp creep, rate ~flat
    wb_cond = (z["current_per_q"] > 2.0) & (z["motor_t_c"] > 2.0)
    wb_onset = first_sustained(wb_cond, HOLD)
    if (wb_onset >= 0 and s["current_per_q"] > 1.5 and s["motor_t_c"] > 1.5
            and abs(s["q_per_freq"]) < 2.0):
        result.update(event_class="water_breakthrough_candidate", onset_index=wb_onset,
                      is_complication=True, confidence=0.55,
                      drivers={"current_per_q_z": round(s["current_per_q"], 2),
                               "motor_t_z": round(s["motor_t_c"], 2)})
        return result

    # 6) operation change after complication checks — freq step must not mask gas above.
    if late_mode_change and affinity_consistent and s["current_var"] < 3.0:
        onset = int(late_mode_idxs[0])
        result.update(event_class="operation_change", onset_index=onset,
                      confidence=0.8,
                      drivers={"freq_step": True, "affinity_consistent": True})
        return result

    return result
