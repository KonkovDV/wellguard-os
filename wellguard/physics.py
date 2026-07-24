from __future__ import annotations
import numpy as np
import pandas as pd

# Physics-guided features. Simplified, mechanistically motivated proxies
# (affinity laws + power/rate coupling). NOT a full electro-hydraulic ESP model.
# Assumptions documented in docs/PHYSICS.md.

EPS = 1e-6


def physics_features(df: pd.DataFrame) -> pd.DataFrame:
    freq_n = np.asarray(df["freq_hz"], dtype=float) / 50.0
    q = np.asarray(df["q_liq_m3d"], dtype=float)
    whp = np.asarray(df["whp_bar"], dtype=float)
    current = np.asarray(df["current_a"], dtype=float)
    load = np.asarray(df["load_pct"], dtype=float)
    motor_t = np.asarray(df["motor_t_c"], dtype=float)

    if "intake_p_bar" in df.columns:
        intake = np.asarray(df["intake_p_bar"], dtype=float)
    else:
        intake = np.full(len(df), np.nan)

    # Pump differential proxy and head coefficient via affinity law (H ~ f^2).
    pump_dp = intake - whp
    head_coef = pump_dp / (freq_n ** 2 + EPS)
    q_per_freq = q / (freq_n + EPS)
    current_per_q = current / (np.abs(q) + EPS)
    cur = pd.Series(current)
    current_var = cur.rolling(9, min_periods=3).std().bfill().to_numpy()

    out = pd.DataFrame({
        "t_min": np.asarray(df["t_min"], dtype=float),
        "freq_n": freq_n,
        "head_coef": head_coef,
        "q_per_freq": q_per_freq,
        "current_per_q": current_per_q,
        "current_var": current_var,
        "intake_p_bar": intake,
        "current_a": current,
        "load_pct": load,
        "q_liq_m3d": q,
        "motor_t_c": motor_t,
    })
    if "water_cut_pct" in df.columns:
        out["water_cut_pct"] = np.asarray(df["water_cut_pct"], dtype=float)
    return out


def detect_mode_changes(freq_n: np.ndarray, thresh: float = 0.03) -> np.ndarray:
    """Return indices where the drive frequency steps (operation change)."""
    base = pd.Series(np.asarray(freq_n, dtype=float)).rolling(15, min_periods=5).median().bfill().to_numpy()
    d = np.abs(np.diff(base, prepend=base[0]))
    return np.where(d > thresh)[0]
