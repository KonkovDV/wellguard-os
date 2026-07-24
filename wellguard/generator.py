from __future__ import annotations
import numpy as np
import pandas as pd

# Deterministic synthetic generator of complicated ESP well regimes.
# Every scenario returns raw telemetry + a ground-truth label + onset index.
# This is SYNTHETIC. No field-performance claim is derived from it.

SCENARIOS = [
    "normal",
    "gas_interference",
    "intake_restriction",
    "water_breakthrough",
    "sensor_fault",
    "operation_change",
    "transient_stress",
]

# Which scenarios are true downhole complications (positives for detection metrics).
COMPLICATIONS = {"gas_interference", "intake_restriction", "water_breakthrough"}

# Map scenario -> expected governed event class.
EXPECTED_CLASS = {
    "normal": "normal",
    "gas_interference": "gas_interference",
    "intake_restriction": "intake_restriction",
    "water_breakthrough": "water_breakthrough_candidate",
    "sensor_fault": "sensor_fault_suspected",
    "operation_change": "operation_change",
    "transient_stress": "normal",
}


def _base(n, rng):
    t = np.arange(n, dtype=float)
    diurnal = 0.4 * np.sin(2 * np.pi * t / 720.0)
    freq = np.full(n, 50.0) + rng.normal(0, 0.05, n)
    q = 120.0 + 4 * diurnal + rng.normal(0, 1.2, n)
    intake = 85.0 + 2 * diurnal + rng.normal(0, 0.6, n)
    whp = 22.0 + 0.5 * diurnal + rng.normal(0, 0.4, n)
    current = 48.0 + 0.15 * (q - 120) + rng.normal(0, 0.5, n)
    load = 72.0 + 0.1 * (q - 120) + rng.normal(0, 0.6, n)
    motor_t = 95.0 + 1.5 * diurnal + rng.normal(0, 0.5, n)
    casing = 14.0 + rng.normal(0, 0.3, n)
    return dict(freq=freq, q=q, intake=intake, whp=whp, current=current,
               load=load, motor_t=motor_t, casing=casing)


def generate(scenario: str, seed: int = 0, n: int = 720, onset: int | None = None) -> pd.DataFrame:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario}")
    rng = np.random.default_rng(seed)
    b = _base(n, rng)
    if onset is None:
        onset = n // 3
    idx = np.arange(n)
    ramp = np.clip((idx - onset) / 90.0, 0, 1)  # 0->1 over 90 min after onset
    step = (idx >= onset).astype(float)
    quality = np.ones(n)

    if scenario == "gas_interference":
        # cyclic current, intake pressure drop, head coefficient loss, mild rate loss
        cyc = np.sin(2 * np.pi * idx / 9.0) * step
        b["current"] += 6.0 * ramp * cyc + 1.5 * ramp
        b["intake"] -= 10.0 * ramp
        b["q"] -= 8.0 * ramp
        b["load"] += 3.0 * ramp * cyc
    elif scenario == "intake_restriction":
        # sustained rate + load + intake decline, current down, head coef up
        b["q"] -= 30.0 * ramp
        b["load"] -= 12.0 * ramp
        b["intake"] -= 16.0 * ramp
        b["current"] -= 5.0 * ramp
    elif scenario == "water_breakthrough":
        # slow density rise: current and motor temp creep up, rate ~flat, head stable
        slow = np.clip((idx - onset) / 240.0, 0, 1)
        b["current"] += 7.0 * slow
        b["motor_t"] += 6.0 * slow
        b["casing"] += 1.0 * slow
    elif scenario == "sensor_fault":
        # intake pressure sensor drifts alone; q/current/load physically unchanged
        b["intake"] += 22.0 * ramp
    elif scenario == "operation_change":
        # deliberate frequency change; all channels shift consistently
        b["freq"] += 4.0 * step
        b["q"] += 12.0 * step
        b["current"] += 4.0 * step
        b["load"] += 4.0 * step
        b["intake"] -= 3.0 * step
    elif scenario == "transient_stress":
        # brief spikes that must NOT persist into an alarm
        for c in (onset, onset + 120, onset + 300):
            if c < n:
                w = (np.abs(idx - c) <= 2).astype(float)
                b["current"] += 9.0 * w
                b["intake"] -= 9.0 * w
                b["q"] -= 9.0 * w
        # a short data-quality dropout
        lo = min(onset + 200, n - 5)
        quality[lo:lo + 4] = 0

    df = pd.DataFrame({
        "t_min": idx.astype(float),
        "freq_hz": b["freq"],
        "whp_bar": b["whp"],
        "intake_p_bar": b["intake"],
        "current_a": b["current"],
        "load_pct": b["load"],
        "q_liq_m3d": b["q"],
        "motor_t_c": b["motor_t"],
        "casing_p_bar": b["casing"],
        "quality_ok": quality,
    })
    df.attrs["scenario"] = scenario
    df.attrs["label"] = EXPECTED_CLASS[scenario]
    df.attrs["is_complication"] = scenario in COMPLICATIONS
    df.attrs["onset"] = int(onset)
    return df
