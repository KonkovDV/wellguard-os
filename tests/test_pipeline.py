import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wellguard.generator import generate
from wellguard.pipeline import run
from wellguard.schema import qc_report

def test_card_keys():
    card = run(generate("normal", seed=0))
    for k in ["event_class","recommended_action","explanation","onset_index",
              "confidence","is_complication","advisory_only","actuation"]:
        assert k in card

def test_qc_flags_low_quality():
    df = generate("normal", seed=0)
    df.loc[df.index[-200:], "quality_ok"] = 0
    card = run(df)
    assert card["event_class"] == "sensor_quality_issue"

def test_empty_input_fails_closed():
    card = run(__import__('pandas').DataFrame())
    assert card["event_class"] == "sensor_quality_issue"
    assert card["is_complication"] is False

def test_nan_input_fails_closed():
    import numpy as np
    df = generate("normal", seed=0)
    df.loc[df.index[-100:], "intake_p_bar"] = np.nan
    card = run(df)
    assert card["event_class"] == "sensor_quality_issue"
    assert card["is_complication"] is False

def test_missing_required_channel_fails_closed():
    df = generate("normal", seed=0).drop(columns=["current_a"])
    card = run(df)
    assert card["event_class"] == "sensor_quality_issue"

def test_explicit_pressure_adapter():
    import pandas as pd
    from wellguard.adapters import map_columns
    x = pd.DataFrame({"P": [14.5038]})
    y = map_columns(x, {"P": "whp_bar"}, source_pressure_unit="psi")
    assert abs(float(y.iloc[0, 0]) - 1.0) < 0.01

def test_insufficient_history_fails_closed():
    card = run(generate("normal", n=20))
    assert card["event_class"] == "sensor_quality_issue"

def test_inf_input_fails_closed():
    import numpy as np
    df = generate("normal", seed=0)
    df.loc[0, "current_a"] = np.inf
    card = run(df)
    assert card["event_class"] == "sensor_quality_issue"
