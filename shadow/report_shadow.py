"""Summarize a shadow JSONL journal into a dry-run pilot report.

Does not claim field accuracy. Counts cards, classes, QC issues, and
expert-disposition fill rates for the letter's shadow review loop.
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from wellguard import __version__

COMPLICATION_CLASSES = {
    "gas_interference",
    "intake_restriction",
    "water_breakthrough_candidate",
}


def load_records(path: str | Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def summarize(records: list[dict]) -> dict:
    classes = Counter(r.get("event_class", "unknown") for r in records)
    complications = sum(1 for r in records if r.get("event_class") in COMPLICATION_CLASSES)
    quality = sum(1 for r in records if r.get("event_class") == "sensor_quality_issue")
    disposition_filled = sum(1 for r in records if r.get("expert_disposition") not in (None, ""))
    useful_yes = sum(1 for r in records if r.get("expert_useful") in (True, 1, "1", "true", "yes"))
    useful_no = sum(1 for r in records if r.get("expert_useful") in (False, 0, "0", "false", "no"))
    alarm_overlap = sum(
        1 for r in records
        if (r.get("window_context") or {}).get("existing_alarm_any")
        and r.get("event_class") in COMPLICATION_CLASSES
    )
    n = len(records)
    return {
        "model_version": records[0].get("model_version", __version__) if records else __version__,
        "report_type": "shadow_dry_run",
        "field_accuracy_claimed": False,
        "economic_effect_claimed": False,
        "actuation": "never",
        "advisory_only": True,
        "windows": n,
        "class_counts": dict(classes),
        "complication_cards": complications,
        "quality_issue_cards": quality,
        "complication_rate": round(complications / n, 4) if n else 0.0,
        "quality_issue_rate": round(quality / n, 4) if n else 0.0,
        "expert_disposition_filled": disposition_filled,
        "expert_disposition_fill_rate": round(disposition_filled / n, 4) if n else 0.0,
        "expert_useful_yes": useful_yes,
        "expert_useful_no": useful_no,
        "complication_windows_with_plant_alarm": alarm_overlap,
        "next_step": (
            "Fill expert_disposition / expert_useful on JSONL during pilot review; "
            "then complete docs/GO_NO_GO_CHECKLIST.md. Do not treat this dry-run as field validation."
        ),
    }


def write_report(jsonl: str | Path, output: str | Path | None = None) -> dict:
    records = load_records(jsonl)
    report = summarize(records)
    if output is None:
        stem = Path(jsonl).stem
        output = Path("artifacts") / f"{stem}_report.json"
    out = Path(output)
    if out.parts and out.parts[0] != "artifacts" and not out.is_absolute():
        out = Path("artifacts") / out.name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["output"] = str(out)
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description="Shadow JSONL dry-run report (not field validation)")
    p.add_argument("jsonl")
    p.add_argument("--output", default=None)
    a = p.parse_args(argv)
    print(json.dumps(write_report(a.jsonl, a.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
