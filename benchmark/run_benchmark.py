from __future__ import annotations
import sys, json, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wellguard.generator import generate, SCENARIOS, EXPECTED_CLASS, COMPLICATIONS
from wellguard.pipeline import run

SEEDS = list(range(12))
CASE_MINUTES = 720
COMPLICATION_CLASSES = {"gas_interference", "intake_restriction", "water_breakthrough_candidate"}


def run_benchmark(seeds=SEEDS) -> dict:
    rows = []
    for sc in SCENARIOS:
        for seed in seeds:
            df = generate(sc, seed=seed)
            card = run(df)
            rows.append({
                "scenario": sc,
                "seed": seed,
                "true_class": EXPECTED_CLASS[sc],
                "pred_class": card["event_class"],
                "is_true_complication": sc in COMPLICATIONS,
                "pred_complication": card["event_class"] in COMPLICATION_CLASSES,
                "true_onset": df.attrs["onset"],
                "pred_onset": card["onset_index"],
            })

    n = len(rows)
    class_acc = np.mean([r["pred_class"] == r["true_class"] for r in rows])

    tp = sum(r["is_true_complication"] and r["pred_complication"] for r in rows)
    fp = sum((not r["is_true_complication"]) and r["pred_complication"] for r in rows)
    fn = sum(r["is_true_complication"] and (not r["pred_complication"]) for r in rows)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    non_comp = [r for r in rows if not r["is_true_complication"]]
    false_alarms = sum(r["pred_complication"] for r in non_comp)
    non_comp_hours = len(non_comp) * CASE_MINUTES / 60.0
    fa_per_hour = false_alarms / non_comp_hours if non_comp_hours else 0.0

    delays = [max(0, r["pred_onset"] - r["true_onset"]) for r in rows
              if r["is_true_complication"] and r["pred_onset"] >= 0 and r["pred_complication"]]
    onset_err = [abs(r["pred_onset"] - r["true_onset"]) for r in rows
                 if r["is_true_complication"] and r["pred_onset"] >= 0 and r["pred_complication"]]

    # safety invariants
    sensor_as_comp = sum(r["scenario"] == "sensor_fault" and r["pred_complication"] for r in rows)
    op_as_comp = sum(r["scenario"] == "operation_change" and r["pred_complication"] for r in rows)
    transient_as_comp = sum(r["scenario"] == "transient_stress" and r["pred_complication"] for r in rows)

    return {
        "n_cases": n,
        "n_seeds": len(seeds),
        "class_accuracy": round(float(class_acc), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "false_complication_alarms_per_hour": round(float(fa_per_hour), 4),
        "detection_delay_min": {
            "median": float(np.median(delays)) if delays else None,
            "max": float(np.max(delays)) if delays else None,
        },
        "onset_error_min": {
            "median": float(np.median(onset_err)) if onset_err else None,
            "max": float(np.max(onset_err)) if onset_err else None,
        },
        "safety_invariants": {
            "sensor_fault_as_complication": int(sensor_as_comp),
            "operation_change_as_complication": int(op_as_comp),
            "transient_as_complication": int(transient_as_comp),
        },
    }


def ml_groupkfold_cv(seeds=SEEDS) -> dict:
    """Auxiliary ML sanity check with honest GroupKFold (group = seed).
    Demonstrates leakage-safe validation; does NOT govern the decision."""
    try:
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.model_selection import GroupKFold, cross_val_score
    except Exception as e:
        return {"available": False, "reason": str(e)}
    from wellguard.physics import physics_features
    X, y, groups = [], [], []
    for sc in SCENARIOS:
        for seed in seeds:
            df = generate(sc, seed=seed)
            f = physics_features(df)
            tail = f.tail(120)
            feats = []
            for c in ["head_coef", "q_per_freq", "current_per_q", "current_var",
                      "intake_p_bar", "current_a", "load_pct", "motor_t_c"]:
                feats += [tail[c].mean(), tail[c].std()]
            X.append(feats); y.append(sc); groups.append(seed)
    X = np.array(X); y = np.array(y); groups = np.array(groups)
    gkf = GroupKFold(n_splits=min(5, len(set(groups))))
    clf = GradientBoostingClassifier(random_state=0)
    scores = cross_val_score(clf, X, y, groups=groups, cv=gkf)
    return {"available": True, "cv_mean_accuracy": round(float(scores.mean()), 4),
            "cv_std": round(float(scores.std()), 4), "splits": int(gkf.get_n_splits())}


if __name__ == "__main__":
    res = run_benchmark()
    res["ml_auxiliary"] = ml_groupkfold_cv()
    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/benchmark.json", "w") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=2))
