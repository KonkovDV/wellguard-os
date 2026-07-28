"""Deep Red Team probes for WellGuard OS — exit 1 on regression."""
from __future__ import annotations
import io, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wellguard.generator import generate
from wellguard.pipeline import run
from wellguard.schema import qc_report
from wellguard.classify import classify
from wellguard import __version__

failures: list[str] = []


def expect(name: str, cond: bool, detail: str) -> None:
    print(f"[{'OK' if cond else 'FAIL'}] {name}: {detail}")
    if not cond:
        failures.append(name)


# --- Prior gates ---
df = generate("normal", seed=0)
df["intake_p_bar"] = 9999.0
expect("oor_fail_closed", run(df)["event_class"] == "sensor_quality_issue", "OOR")

df = generate("gas_interference", seed=0)
df.loc[df.attrs["onset"]:, "freq_hz"] += 5.0
expect("freq_no_mask", run(df)["event_class"] == "gas_interference", run(df)["event_class"])

expect("early_onset", run(generate("gas_interference", seed=0, onset=0))["event_class"] == "gas_interference", "onset0")

# --- New: water_cut alone must NOT invent complication without physics hold ---
df = generate("normal", seed=1)
df["water_cut_pct"] = np.linspace(5, 40, len(df))
card = run(df)
expect("water_cut_alone_no_false_wb", card["event_class"] == "normal", card["event_class"])

# --- New: duplicate timestamps fail closed ---
df = generate("normal", seed=2)
df.loc[10:20, "t_min"] = df.loc[9, "t_min"]
expect("dup_time_fail", run(df)["event_class"] == "sensor_quality_issue", run(df)["event_class"])

# --- New: reverse time fail ---
df = generate("normal", seed=3)
df["t_min"] = df["t_min"].iloc[::-1].to_numpy()
expect("reverse_time_fail", run(df)["event_class"] == "sensor_quality_issue", "timeline")

# --- New: empty frame ---
expect("empty_fail", run(pd.DataFrame())["event_class"] == "sensor_quality_issue", "empty")

# --- New: card contract ---
card = run(generate("gas_interference", seed=0))
expect("card_not_probability", card["score_is_probability"] is False, card["score_type"])
expect("card_limits", "output_limits" in card and card["actuation"] == "never", "limits")
expect("card_no_failure_claim", card["confirms_failure_or_accident"] is False, "safety")

# --- New: annotation too long ---
df = generate("normal", seed=4)
df["operator_annotation"] = "X" * 200
qc = qc_report(df)
expect("annotation_len_flagged", any("operator_annotation" in i for i in qc["issues"]), qc["issues"])

# --- New: API module constants ---
api = (ROOT / "wellguard" / "api.py").read_text(encoding="utf-8")
expect("api_precheck", 'raw.count(b"\\n")' in api and api.find('raw.count(b"\\n")') < api.find("pd.read_csv"), "order")
expect("api_try_run", "HTTPException(422" in api or "422" in api, "422 on pipeline reject")

# --- New: docker bind ---
docker = (ROOT / "Dockerfile").read_text(encoding="utf-8")
expect("docker_host", "0.0.0.0" in docker.split("CMD")[-1], docker.strip().splitlines()[-1])

# --- Floors ---
from benchmark.redteam import evaluate
r, v = evaluate()
expect("redteam_floors", v == [], str(v))
expect("version_semver", len(__version__.split(".")) == 3, __version__)

print("\n===", "PASS" if not failures else f"FAIL {failures}", "===")
sys.exit(1 if failures else 0)
