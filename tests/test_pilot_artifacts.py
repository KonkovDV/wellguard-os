"""Pilot artifact tests: go/no-go docs exist; shadow-report is honest dry-run."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from wellguard.generator import generate
from shadow.run_shadow import replay
from shadow.report_shadow import summarize, write_report, COMPLICATION_CLASSES


def test_pilot_docs_present():
    root = Path(__file__).resolve().parents[1]
    for rel in [
        "docs/GO_NO_GO_CHECKLIST.md",
        "docs/EXPERT_LABELING.md",
        "docs/CLAIM_FREEZE.md",
        "data/templates/expert_labeling_template.csv",
    ]:
        assert (root / rel).exists(), rel


def test_expert_template_has_letter_classes():
    text = Path("data/templates/expert_labeling_template.csv").read_text(encoding="utf-8")
    assert "gas_interference" in text
    assert "operation_change" in text
    assert "useful_for_technologist" in text


def test_shadow_report_dry_run_flags(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "artifacts").mkdir()
    csv = tmp_path / "demo.csv"
    generate("gas_interference", seed=0, n=800).to_csv(csv, index=False)
    summary = replay(str(csv), "shadow_decisions.jsonl", window=720, step=60)
    report = write_report(summary["output"])
    assert report["field_accuracy_claimed"] is False
    assert report["economic_effect_claimed"] is False
    assert report["actuation"] == "never"
    assert report["windows"] >= 1
    assert "gas_interference" in COMPLICATION_CLASSES
    # empty dispositions on fresh dry-run
    assert report["expert_disposition_filled"] == 0
    saved = json.loads(Path(report["output"]).read_text(encoding="utf-8"))
    assert saved["report_type"] == "shadow_dry_run"
