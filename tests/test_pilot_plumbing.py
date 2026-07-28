"""Tests that strengthen letter-scoped archive/shadow plumbing without new claims."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
import pandas as pd
from wellguard.generator import generate
from wellguard.dataio.gpn_archive import load_archive, validate_against_contract, load_contract
from shadow.run_shadow import replay, resolve_output_path


def _meta():
    return {
        "asset_id_hash": "a",
        "well_id_hash": "w",
        "timezone": "UTC",
        "sampling_interval_s": 60,
        "unit_system": "SI",
    }


def test_contract_loads_and_lists_letter_channels():
    c = load_contract()
    assert "operating_mode" in c["required_channels"]
    assert "intake_p_bar" in c["conditional_channels"]
    for x in ("water_cut_pct", "existing_alarm", "daily_report_flag", "esp_start_stop"):
        assert x in c["optional_channels"]


def test_validate_against_contract_ok_on_generator():
    df = generate("normal", seed=0)
    report = validate_against_contract(df)
    assert report["contract_ok"] is True
    assert report["missing_required"] == []


def test_load_archive_rejects_missing_required(tmp_path):
    p = tmp_path / "bad.csv"
    pd.DataFrame({"freq_hz": [50.0]}).to_csv(p, index=False)
    try:
        load_archive(p, {}, _meta(), pressure_unit="bar")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "required" in str(e).lower() or "missing" in str(e).lower()


def test_shadow_journal_has_disposition_slots(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts").mkdir()
    csv = tmp_path / "demo.csv"
    df = generate("gas_interference", seed=0, n=800)
    df["existing_alarm"] = 0
    df.to_csv(csv, index=False)
    summary = replay(str(csv), "shadow_decisions.jsonl", window=720, step=60)
    assert summary["read_only"] is True
    assert summary["actuation"] == "never"
    out = Path(summary["output"])
    line = out.read_text(encoding="utf-8").strip().splitlines()[0]
    rec = json.loads(line)
    assert "model_version" in rec
    assert "expert_disposition" in rec
    assert rec["expert_disposition"] is None
    assert rec["score_is_probability"] is False
    assert "window_context" in rec
