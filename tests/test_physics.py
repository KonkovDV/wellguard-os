import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from wellguard.generator import generate
from wellguard.physics import physics_features, detect_mode_changes

def test_features_shape_and_finite():
    df = generate("normal", seed=1)
    f = physics_features(df)
    assert len(f) == len(df)
    for c in ["head_coef", "q_per_freq", "current_per_q", "current_var"]:
        assert np.isfinite(f[c].to_numpy()).all()

def test_mode_change_detected_on_operation_change():
    df = generate("operation_change", seed=0, onset=240)
    f = physics_features(df)
    mc = detect_mode_changes(f["freq_n"].to_numpy())
    assert (mc > 150).any()

def test_no_mode_change_on_normal():
    df = generate("normal", seed=2)
    f = physics_features(df)
    mc = detect_mode_changes(f["freq_n"].to_numpy())
    assert not (mc > 150).any()
