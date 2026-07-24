"""Pinned, local-only loader for Petrobras 3W Dataset 2.0.0.

The loader never downloads data. It reads a user-provided local 3W checkout,
checks dataset.ini version, discovers parquet instances, maps only documented
aliases, and preserves source labels. It fails closed on ambiguous mappings.

Pressure channels in 3W 2.0.0 are documented in Pascals (Pa). Canonical WellGuard
channels are bar, so pressures are converted with an explicit Pa→bar factor.
"""
from __future__ import annotations
from configparser import ConfigParser
from pathlib import Path
import hashlib
import json
import pandas as pd

PINNED_DATASET = "2.0.0"
PINNED_REPOSITORY = "https://github.com/petrobras/3W"
PA_TO_BAR = 1e-5

# 3W names vary by release. Keep aliases explicit and conservative.
ALIASES = {
    "timestamp": ["timestamp"],
    "whp_bar": ["P-TPT", "P-MON-SURF"],
    "intake_p_bar": ["P-PDG"],
    "motor_t_c": ["T-TPT"],
    "casing_p_bar": ["P-MON-CKP"],
    "quality_ok": ["quality_ok"],
}

PRESSURE_TARGETS = ("whp_bar", "intake_p_bar", "casing_p_bar")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def assert_pinned(root: str | Path) -> dict:
    root = Path(root)
    ini = root / "dataset" / "dataset.ini"
    if not ini.exists():
        raise FileNotFoundError(f"pinned 3W checkout missing {ini}")
    cfg = ConfigParser(); cfg.read(ini, encoding="utf-8")
    version = cfg.get("VERSION", "DATASET", fallback="")
    if version != PINNED_DATASET:
        raise ValueError(f"3W dataset version {version!r} != pinned {PINNED_DATASET!r}")
    return {"dataset_version": version, "repository": PINNED_REPOSITORY,
            "dataset_ini_sha256": sha256_file(ini),
            "pressure_unit_source": "Pa",
            "pressure_unit_canonical": "bar"}


def discover_parquet(root: str | Path) -> list[Path]:
    root = Path(root)
    files = sorted((root / "dataset").rglob("*.parquet"))
    if not files:
        raise FileNotFoundError("no parquet instances found under <root>/dataset")
    return files


def _map_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for target, aliases in ALIASES.items():
        found = [a for a in aliases if a in df.columns]
        if len(found) > 1:
            raise ValueError(f"ambiguous mapping for {target}: {found}")
        if found:
            out[target] = df[found[0]]
    for c in PRESSURE_TARGETS:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce") * PA_TO_BAR
    # Preserve source label columns exactly, without pretending they are target labels.
    for c in ("class", "label", "well", "instance", "id"):
        if c in df.columns:
            out[f"source_{c}"] = df[c]
    return out


def load_instance(path: str | Path, *, require_channels: bool = False) -> tuple[pd.DataFrame, dict]:
    path = Path(path)
    df = pd.read_parquet(path)
    mapped = _map_frame(df)
    meta = {"path": str(path), "rows": int(len(df)),
            "source_columns": list(df.columns),
            "sha256": sha256_file(path),
            "pressure_conversion": "Pa_to_bar"}
    if require_channels:
        missing = [c for c in ("timestamp", "whp_bar", "intake_p_bar") if c not in mapped]
        if missing:
            raise ValueError(f"3W instance missing required mapped channels: {missing}")
    return mapped, meta


def manifest(root: str | Path) -> dict:
    pin = assert_pinned(root)
    files = discover_parquet(root)
    return {**pin, "n_files": len(files),
            "files": [{"path": str(p.relative_to(Path(root))),
                       "sha256": sha256_file(p)} for p in files]}


def write_manifest(root: str | Path, output: str | Path) -> Path:
    out = Path(output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest(root), ensure_ascii=False, indent=2), encoding="utf-8")
    return out
