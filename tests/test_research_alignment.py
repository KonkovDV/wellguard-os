"""Research-aligned checks within letter classes (no new event types)."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wellguard.generator import generate
from wellguard.pipeline import run
from wellguard.physics import physics_features


def test_gas_card_exposes_consistency_and_casing_support():
    card = run(generate("gas_interference", seed=0))
    assert card["event_class"] == "gas_interference"
    assert "consistency" in card["drivers"]
    assert "current_per_freq_z" in card["drivers"]["consistency"]
    assert "intake_var_z" in card["drivers"]["consistency"]
    assert card["drivers"].get("casing_support") is True
    assert card["drivers"].get("rate_support") is True
    assert "sensor_coverage" in card["drivers"]


def test_gas_mode_b_pip_rise_whp_drop():
    # Appl. Sci. gas-lock field pattern → same letter class, not plugging.
    df = generate("normal", seed=5)
    onset = 300
    n = len(df)
    idx = np.arange(n)
    step = (idx >= onset).astype(float)
    ramp = np.clip((idx - onset) / 40.0, 0, 1) * step
    cyc = np.sin(2 * np.pi * idx / 9.0) * step
    df.loc[:, "current_a"] = df["current_a"] + 7.0 * ramp * cyc
    df.loc[:, "intake_p_bar"] = df["intake_p_bar"] + 12.0 * ramp
    df.loc[:, "whp_bar"] = df["whp_bar"] - 8.0 * ramp
    df.loc[:, "q_liq_m3d"] = df["q_liq_m3d"] - 6.0 * ramp
    card = run(df)
    assert card["event_class"] == "gas_interference"
    assert card["drivers"].get("detector") == "pip_rise_whp_drop_osc"


def test_restriction_exposes_plugging_supports():
    card = run(generate("intake_restriction", seed=0))
    assert card["event_class"] == "intake_restriction"
    assert card["drivers"].get("pip_rise_support") is True
    assert card["drivers"].get("underload_support") is True
    assert "head_support" in card["drivers"]
    assert "consistency" in card["drivers"]


def test_restriction_not_sensor_fault_when_coupling_moves():
    card = run(generate("intake_restriction", seed=1))
    assert card["event_class"] == "intake_restriction"
    assert card["is_complication"] is True


def test_sensor_fault_requires_whp_quiet():
    df = generate("sensor_fault", seed=0)
    onset = df.attrs["onset"]
    df.loc[onset:, "whp_bar"] = df.loc[onset:, "whp_bar"] + 18.0
    card = run(df)
    assert card["event_class"] != "sensor_fault_suspected"


def test_gas_factor_reinforces_only():
    df = generate("normal", seed=2)
    df["gas_factor_m3m3"] = np.linspace(20, 80, len(df))
    card = run(df)
    assert card["event_class"] == "normal"


def test_physics_includes_current_per_freq():
    f = physics_features(generate("normal", seed=0))
    assert "current_per_freq" in f.columns
    assert "intake_var" in f.columns
    assert "whp_bar" in f.columns
    assert np.isfinite(f["current_per_freq"].to_numpy()).all()
    assert np.isfinite(f["intake_var"].to_numpy()).all()
