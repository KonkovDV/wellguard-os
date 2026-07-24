"""Hardening tests for Red Team findings closed in v0.1.3."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import pytest
from wellguard.generator import generate
from wellguard.pipeline import run
from wellguard.schema import qc_report, coerce_telemetry
from wellguard.classify import classify
from wellguard.dataio.threew import PA_TO_BAR, _map_frame
from shadow.run_shadow import resolve_output_path


def test_out_of_range_fails_closed():
    df = generate("normal", seed=0)
    df["intake_p_bar"] = 9999.0
    qc = qc_report(df)
    card = run(df)
    assert qc["schema_ok"] is False
    assert any(i.startswith("out_of_range:") for i in qc["issues"])
    assert card["event_class"] == "sensor_quality_issue"
    assert card["is_complication"] is False


def test_negative_oor_fails_closed():
    df = generate("normal", seed=0)
    df["current_a"] = -50.0
    assert run(df)["event_class"] == "sensor_quality_issue"


def test_freq_step_does_not_mask_gas():
    df = generate("gas_interference", seed=0)
    onset = df.attrs["onset"]
    df.loc[onset:, "freq_hz"] = df.loc[onset:, "freq_hz"] + 5.0
    card = run(df)
    assert card["event_class"] == "gas_interference"
    assert card["is_complication"] is True


def test_early_onset_gas_still_detected():
    card = run(generate("gas_interference", seed=0, onset=0))
    assert card["event_class"] == "gas_interference"
    assert card["is_complication"] is True


def test_string_numeric_dtype_coerced_not_crash():
    df = generate("gas_interference", seed=0)
    for c in ["freq_hz", "whp_bar", "intake_p_bar", "current_a", "load_pct",
              "q_liq_m3d", "motor_t_c", "casing_p_bar"]:
        df[c] = df[c].astype(str)
    card = run(df)
    assert card["event_class"] == "gas_interference"


def test_sensor_fault_requires_persistent_onset():
    df = generate("normal", seed=1, n=200)
    df.loc[df.index[-5:], "intake_p_bar"] = float(df["intake_p_bar"].iloc[-5]) + 40
    cls = classify(df)
    assert cls["event_class"] != "sensor_fault_suspected" or cls["onset_index"] >= 0
    # short spike must not mint a timeless sensor_fault card
    assert not (cls["event_class"] == "sensor_fault_suspected" and cls["onset_index"] < 0)


def test_invalid_quality_ok_fails_closed():
    df = generate("normal", seed=0)
    df["quality_ok"] = 100.0
    qc = qc_report(df)
    assert qc["schema_ok"] is False
    assert any(i.startswith("invalid_quality_ok:") for i in qc["issues"])
    assert run(df)["event_class"] == "sensor_quality_issue"


def test_operator_card_includes_qc():
    card = run(pd.DataFrame())
    assert "qc" in card
    assert card["qc"]["schema_ok"] is False
    assert card["qc"]["issues"]


def test_tail_quality_drivers_nonempty():
    df = generate("normal", seed=0)
    df.loc[df.index[-200:], "quality_ok"] = 0
    card = run(df)
    assert card["event_class"] == "sensor_quality_issue"
    assert card["drivers"]


def test_3w_pressure_pa_to_bar():
    raw = pd.DataFrame({"P-TPT": [1e5], "P-PDG": [2e5], "T-TPT": [90.0]})
    mapped = _map_frame(raw)
    assert abs(float(mapped["whp_bar"].iloc[0]) - 1.0) < 1e-9
    assert abs(float(mapped["intake_p_bar"].iloc[0]) - 2.0) < 1e-9
    assert PA_TO_BAR == 1e-5


def test_shadow_output_sandboxed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts").mkdir()
    out = resolve_output_path("../secret.jsonl", root=tmp_path / "artifacts")
    assert out.parent == (tmp_path / "artifacts").resolve()
    assert out.name == "secret.jsonl"
    out2 = resolve_output_path("artifacts/nested/log.jsonl", root=tmp_path / "artifacts")
    assert "artifacts" in str(out2)
    assert out2.name == "log.jsonl"


def test_coerce_telemetry_idempotent():
    df = generate("normal", seed=0)
    a = coerce_telemetry(df)
    b = coerce_telemetry(a)
    assert list(a.columns) == list(b.columns)
