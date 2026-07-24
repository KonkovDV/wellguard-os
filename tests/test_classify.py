import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from wellguard.generator import generate, SCENARIOS, EXPECTED_CLASS
from wellguard.pipeline import run

@pytest.mark.parametrize("sc", SCENARIOS)
def test_expected_class_multi_seed(sc):
    hits = 0
    for seed in range(5):
        card = run(generate(sc, seed=seed))
        hits += card["event_class"] == EXPECTED_CLASS[sc]
    assert hits == 5, f"{sc}: {hits}/5"

def test_sensor_fault_never_complication():
    for seed in range(8):
        card = run(generate("sensor_fault", seed=seed))
        assert not card["is_complication"]
        assert card["event_class"] == "sensor_fault_suspected"

def test_operation_change_not_complication():
    for seed in range(8):
        card = run(generate("operation_change", seed=seed))
        assert not card["is_complication"]

def test_transient_does_not_persist_to_alarm():
    for seed in range(8):
        card = run(generate("transient_stress", seed=seed))
        assert not card["is_complication"]

def test_advisory_only_contract():
    card = run(generate("gas_interference", seed=0))
    assert card["advisory_only"] is True
    assert card["actuation"] == "never"
