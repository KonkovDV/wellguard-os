from __future__ import annotations
import argparse, json, sys
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
    s = sub.add_parser("screen", help="screen a telemetry CSV")
    s.add_argument("csv")
    sub.add_parser("version", help="print version")
    a = p.parse_args(argv)
    if a.cmd == "version":
        print(__version__); return 0
    if a.cmd == "demo":
        df = generate(a.scenario, seed=a.seed)
        card = run(df)
        card["_true_scenario"] = df.attrs["scenario"]
        print(json.dumps(card, ensure_ascii=False, indent=2)); return 0
    if a.cmd == "screen":
        df = pd.read_csv(a.csv)
        print(json.dumps(run(df), ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    sys.exit(main())
