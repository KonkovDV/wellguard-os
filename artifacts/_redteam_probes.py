"""Post-fix verification probes for Red Team findings (v0.1.3). Exit 1 if any regress."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wellguard.generator import generate
from wellguard.pipeline import run
from wellguard.schema import qc_report, CHANNELS
from wellguard.classify import classify
from wellguard.dataio import threew
from shadow.run_shadow import resolve_output_path

failures: list[str] = []


def expect(name: str, cond: bool, detail: str) -> None:
    status = "OK" if cond else "REGRESS"
    print(f"[{status}] {name}: {detail}")
    if not cond:
        failures.append(name)


# RT-01 / RT-04 style OOR
df = generate("normal", seed=0)
df["intake_p_bar"] = 9999.0
expect("RT01_oor_fail_closed", run(df)["event_class"] == "sensor_quality_issue", run(df)["event_class"])

# RT-02 freq mask
df = generate("gas_interference", seed=0)
onset = df.attrs["onset"]
df.loc[onset:, "freq_hz"] = df.loc[onset:, "freq_hz"] + 5.0
card = run(df)
expect("RT02_freq_no_mask", card["event_class"] == "gas_interference" and card["is_complication"], card["event_class"])

# RT-03 early onset
card = run(generate("gas_interference", seed=0, onset=0))
expect("RT03_early_onset_gas", card["event_class"] == "gas_interference", card["event_class"])

# RT-05 units
expect("RT05_pa_to_bar", threew.PA_TO_BAR == 1e-5 and "PA_TO_BAR" in Path("wellguard/dataio/threew.py").read_text(encoding="utf-8"), "factor set")

# RT-06 API pre-check
api = Path("wellguard/api.py").read_text(encoding="utf-8")
pre = api.find('raw.count(b"\\n")')
parse = api.find("pd.read_csv")
expect("RT06_row_precheck", 0 <= pre < parse, f"pre={pre} parse={parse}")

# RT-07 coerce
df = generate("gas_interference", seed=0)
for c in CHANNELS:
    if c != "t_min":
        df[c] = df[c].astype(str)
expect("RT07_string_coerce", run(df)["event_class"] == "gas_interference", "pipeline on str dtypes")

# RT-08 docker host
docker = Path("Dockerfile").read_text(encoding="utf-8")
expect("RT08_docker_0_0_0_0", '--host", "0.0.0.0"' in docker or "--host\", \"0.0.0.0\"" in docker or "0.0.0.0" in docker.split("CMD")[-1], docker.strip().splitlines()[-1])

# RT-09 no timeless sensor_fault
df = generate("normal", seed=1, n=200)
df.loc[df.index[-5:], "intake_p_bar"] = float(df["intake_p_bar"].iloc[-5]) + 40
cls = classify(df)
expect("RT09_no_onset_neg1_fault", not (cls["event_class"] == "sensor_fault_suspected" and cls["onset_index"] < 0), cls)

# RT-10 qc on card
card = run(pd.DataFrame())
expect("RT10_qc_on_card", "qc" in card and card["qc"]["issues"], sorted(card.keys()))

# RT-11 shadow sandbox
out = resolve_output_path("../evil.jsonl")
expect("RT11_shadow_sandbox", out.parts[-2:] == ("artifacts", "evil.jsonl") or out.name == "evil.jsonl" and "artifacts" in out.parts, str(out))

# RT-12 quality_ok
df = generate("normal", seed=0)
df["quality_ok"] = 100.0
expect("RT12_quality_ok", qc_report(df)["schema_ok"] is False, qc_report(df)["issues"])

from benchmark.redteam import evaluate
r, v = evaluate()
expect("REDTEAM_FLOORS", v == [], v)

print("\n===", "PASS" if not failures else f"FAIL {failures}", "===")
sys.exit(1 if failures else 0)
