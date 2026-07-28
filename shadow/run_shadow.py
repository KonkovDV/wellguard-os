"""Read-only shadow mode replay.

Input is a canonical telemetry CSV. Output is an append-only JSONL decision log
with one card per fixed window. No control writes, no network, no telemetry
persistence beyond the explicitly requested output file under artifacts/.

Journal fields support the letter's shadow-mode review loop: model version,
QC, optional plant-alarm passthrough, and empty expert-disposition slots.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from wellguard import __version__
from wellguard.pipeline import run

ARTIFACTS_ROOT = Path("artifacts")


def resolve_output_path(output: str, *, root: Path | None = None) -> Path:
    """Force decision logs under artifacts/ (path traversal resistant)."""
    base = (root or ARTIFACTS_ROOT).resolve()
    raw = Path(output)
    if raw.is_absolute():
        parts = [raw.name]
    else:
        parts = [p for p in raw.parts if p not in ("", ".", "..")]
        if parts and parts[0] == "artifacts":
            parts = parts[1:]
    if not parts:
        parts = ["shadow_decisions.jsonl"]
    candidate = base.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as e:
        raise ValueError(f"output must resolve under {base}") from e
    return candidate


def _window_context(chunk: pd.DataFrame) -> dict:
    ctx: dict = {}
    if "existing_alarm" in chunk.columns:
        alarm = pd.to_numeric(chunk["existing_alarm"], errors="coerce").fillna(0)
        ctx["existing_alarm_rate"] = round(float(alarm.mean()), 4)
        ctx["existing_alarm_any"] = bool(alarm.max() > 0)
    if "esp_start_stop" in chunk.columns:
        ss = pd.to_numeric(chunk["esp_start_stop"], errors="coerce").fillna(0)
        ctx["esp_start_stop_any"] = bool(ss.max() > 0)
    if "operating_mode" in chunk.columns:
        ctx["operating_mode_tail"] = str(chunk["operating_mode"].iloc[-1])
    return ctx


def _json_safe(obj):
    """Convert numpy/pandas scalars so JSONL journaling never crashes."""
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    if obj is None:
        return None
    try:
        if not isinstance(obj, (str, bytes, dict, list, tuple)) and pd.isna(obj):
            return None
    except (ValueError, TypeError):
        pass
    return obj


def replay(csv: str, output: str, *, window: int = 720, step: int = 60) -> dict:
    if window < 30 or step < 1:
        raise ValueError("window must be >= 30 and step >= 1")
    df = pd.read_csv(csv)
    out = resolve_output_path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    quality = 0
    decisions = []
    with out.open("w", encoding="utf-8") as f:
        for end in range(window, len(df) + 1, step):
            chunk = df.iloc[end - window:end].copy()
            card = run(chunk)
            record = _json_safe({
                "model_version": __version__,
                "window_end_row": end,
                "window_rows": len(chunk),
                "window_context": _window_context(chunk),
                # Expert disposition slots (filled during pilot review, not by the model)
                "expert_disposition": None,
                "expert_useful": None,
                "expert_notes_code": None,
                **card,
            })
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            n += 1
            quality += int(card["event_class"] == "sensor_quality_issue")
            decisions.append(card["event_class"])
    return {
        "windows": n,
        "quality_windows": quality,
        "output": str(out),
        "unique_classes": sorted(set(decisions)),
        "model_version": __version__,
        "read_only": True,
        "actuation": "never",
        "advisory_only": True,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv")
    p.add_argument("--output", default="shadow_decisions.jsonl")
    p.add_argument("--window", type=int, default=720)
    p.add_argument("--step", type=int, default=60)
    a = p.parse_args()
    print(json.dumps(replay(a.csv, a.output, window=a.window, step=a.step), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
