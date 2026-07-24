import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark.redteam import evaluate

def test_redteam_floors_pass():
    r, violations = evaluate()
    assert violations == [], f"violations: {violations}"
    assert r["safety_invariants"]["sensor_fault_as_complication"] == 0
