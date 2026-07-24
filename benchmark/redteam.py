from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark.run_benchmark import run_benchmark

# Synthetic-only acceptance floors. Exit code 1 on any violation (CI gate).
FLOORS = {
    "class_accuracy_min": 0.95,
    "precision_min": 0.90,
    "recall_min": 0.75,
    "false_alarms_per_hour_max": 0.5,
    "detection_delay_max_min": 120.0,
}


def evaluate() -> tuple[dict, list]:
    r = run_benchmark()
    v = []
    if r["class_accuracy"] < FLOORS["class_accuracy_min"]:
        v.append(f"class_accuracy {r['class_accuracy']} < {FLOORS['class_accuracy_min']}")
    if r["precision"] < FLOORS["precision_min"]:
        v.append(f"precision {r['precision']} < {FLOORS['precision_min']}")
    if r["recall"] < FLOORS["recall_min"]:
        v.append(f"recall {r['recall']} < {FLOORS['recall_min']}")
    if r["false_complication_alarms_per_hour"] > FLOORS["false_alarms_per_hour_max"]:
        v.append(f"false_alarms/h {r['false_complication_alarms_per_hour']} > {FLOORS['false_alarms_per_hour_max']}")
    dmax = r["detection_delay_min"]["max"]
    if dmax is not None and dmax > FLOORS["detection_delay_max_min"]:
        v.append(f"detection_delay_max {dmax} > {FLOORS['detection_delay_max_min']}")
    si = r["safety_invariants"]
    for k, val in si.items():
        if val != 0:
            v.append(f"safety_invariant {k} = {val} (must be 0)")
    return r, v


if __name__ == "__main__":
    r, violations = evaluate()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if violations:
        print("\nRED-TEAM VIOLATIONS:")
        for x in violations:
            print("  -", x)
        sys.exit(1)
    print("\nRED-TEAM: all floors PASS")
