from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import pandas as pd
from . import __version__
from .generator import generate, SCENARIOS
from .pipeline import run


def main(argv=None):
    p = argparse.ArgumentParser(prog="wellguard", description="WellGuard OS advisory CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="run a built-in synthetic scenario")
    d.add_argument("--scenario", default="gas_interference", choices=SCENARIOS)
    d.add_argument("--seed", type=int, default=0)

    s = sub.add_parser("screen", help="screen a telemetry CSV (read-only card)")
    s.add_argument("csv")

    e = sub.add_parser("export-demo", help="export synthetic canonical CSV for shadow/archive dry-run")
    e.add_argument("--scenario", default="gas_interference", choices=SCENARIOS)
    e.add_argument("--seed", type=int, default=0)
    e.add_argument("--output", default="artifacts/demo_canonical.csv")

    sh = sub.add_parser("shadow", help="read-only fixed-window shadow replay → JSONL under artifacts/")
    sh.add_argument("csv")
    sh.add_argument("--output", default="shadow_decisions.jsonl")
    sh.add_argument("--window", type=int, default=720)
    sh.add_argument("--step", type=int, default=60)

    v = sub.add_parser("validate-archive", help="validate CSV against GPN archive contract + QC")
    v.add_argument("csv")
    v.add_argument("--pressure-unit", default="bar", choices=["bar", "psi"])
    v.add_argument("--asset-id-hash", default="demo")
    v.add_argument("--well-id-hash", default="demo")
    v.add_argument("--timezone", default="UTC")
    v.add_argument("--sampling-interval-s", type=int, default=60)
    v.add_argument("--unit-system", default="SI")

    sub.add_parser("version", help="print version")
    a = p.parse_args(argv)

    if a.cmd == "version":
        print(__version__)
        return 0

    if a.cmd == "demo":
        df = generate(a.scenario, seed=a.seed)
        card = run(df)
        card["_true_scenario"] = df.attrs["scenario"]
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return 0

    if a.cmd == "screen":
        df = pd.read_csv(a.csv)
        print(json.dumps(run(df), ensure_ascii=False, indent=2))
        return 0

    if a.cmd == "export-demo":
        df = generate(a.scenario, seed=a.seed)
        out = Path(a.output)
        if out.parts and out.parts[0] != "artifacts":
            out = Path("artifacts") / out.name
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        print(json.dumps({"output": str(out), "rows": len(df), "scenario": a.scenario}, indent=2))
        return 0

    if a.cmd == "shadow":
        from shadow.run_shadow import replay
        print(json.dumps(replay(a.csv, a.output, window=a.window, step=a.step), ensure_ascii=False, indent=2))
        return 0

    if a.cmd == "validate-archive":
        from .dataio.gpn_archive import load_archive
        md = {
            "asset_id_hash": a.asset_id_hash,
            "well_id_hash": a.well_id_hash,
            "timezone": a.timezone,
            "sampling_interval_s": a.sampling_interval_s,
            "unit_system": a.unit_system,
        }
        _, meta = load_archive(a.csv, {}, md, pressure_unit=a.pressure_unit)
        print(json.dumps(meta, ensure_ascii=False, indent=2, default=str))
        return 0 if meta["qc"]["schema_ok"] and meta["contract"]["contract_ok"] else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
