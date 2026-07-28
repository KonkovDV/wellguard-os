"""Letter-alignment tests: INDUSTRIX application contract vs repo."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
from wellguard.generator import generate
from wellguard.pipeline import run
from wellguard.schema import qc_report, REQUIRED_CHANNELS, MODE_COL


def test_operating_mode_required():
    df = generate("normal", seed=0).drop(columns=[MODE_COL])
    card = run(df)
    assert card["event_class"] == "sensor_quality_issue"
    assert any("operating_mode" in i for i in card["qc"]["issues"])


def test_intake_optional_still_classifies():
    df = generate("intake_restriction", seed=0).drop(columns=["intake_p_bar"])
    qc = qc_report(df)
    assert qc["schema_ok"] is True
    assert qc["intake_available"] is False
    assert any("missing_optional:intake_p_bar" in w for w in qc["warnings"])
    card = run(df)
    assert card["event_class"] == "intake_restriction"
    assert card["is_complication"] is True


def test_timeline_gap_flagged():
    df = generate("normal", seed=0)
    df.loc[400:, "t_min"] = df.loc[400:, "t_min"] + 500
    qc = qc_report(df)
    assert qc["schema_ok"] is False
    assert any(i.startswith("timeline_large_gaps:") for i in qc["issues"])


def test_heuristic_score_not_probability():
    card = run(generate("gas_interference", seed=0))
    assert card["score_is_probability"] is False
    assert card["score_type"] == "heuristic_rule_strength"
    assert "heuristic_score" in card
    assert card["replaces_engineer"] is False
    assert card["confirms_failure_or_accident"] is False
    assert "output_limits" in card


def test_operator_annotation_too_long_fails_closed():
    df = generate("normal", seed=0)
    df["operator_annotation"] = "Z" * 128
    card = run(df)
    assert card["event_class"] == "sensor_quality_issue"
    assert any("operator_annotation" in i for i in card["qc"]["issues"])


def test_water_cut_alone_does_not_invent_complication():
    df = generate("normal", seed=0)
    df["water_cut_pct"] = np.linspace(5, 45, len(df))
    card = run(df)
    assert card["event_class"] == "normal"
    assert card["is_complication"] is False


def test_water_cut_reinforces_wb_candidate():
    df = generate("water_breakthrough", seed=0)
    df["water_cut_pct"] = np.linspace(10, 40, len(df))
    card = run(df)
    assert card["event_class"] == "water_breakthrough_candidate"
    assert card["drivers"].get("water_cut_support") is True
    assert "water_cut_pct" in card["qc"]["present_optional_extras"]


def test_required_channels_match_letter_minimum():
    assert MODE_COL in REQUIRED_CHANNELS
    assert "intake_p_bar" not in REQUIRED_CHANNELS
    for c in ["t_min", "freq_hz", "current_a", "load_pct", "whp_bar",
              "motor_t_c", "casing_p_bar", "q_liq_m3d"]:
        assert c in REQUIRED_CHANNELS
