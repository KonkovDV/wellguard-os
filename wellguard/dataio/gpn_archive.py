"""Strict intake contract for a Gazprom Neft archive.

No customer archive is bundled. This module validates an exported, anonymized
CSV/Parquet file after the asset owner supplies the tag dictionary and units.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from ..schema import CHANNELS, qc_report

REQUIRED_METADATA = ["asset_id_hash", "well_id_hash", "timezone", "sampling_interval_s", "unit_system"]

def validate_metadata(metadata: dict) -> list[str]:
    return [k for k in REQUIRED_METADATA if k not in metadata or metadata[k] in (None, "")]

def load_archive(path: str | Path, mapping: dict[str, str], metadata: dict,
                 *, pressure_unit: str) -> tuple[pd.DataFrame, dict]:
    missing_meta = validate_metadata(metadata)
    if missing_meta:
        raise ValueError(f"archive metadata incomplete: {missing_meta}")
    p = Path(path)
    if p.suffix.lower() == ".parquet":
        raw = pd.read_parquet(p)
    elif p.suffix.lower() in (".csv", ".tsv"):
        raw = pd.read_csv(p, sep="\t" if p.suffix.lower() == ".tsv" else ",")
    else:
        raise ValueError("archive must be CSV, TSV or Parquet")
    out = raw.rename(columns=mapping).copy()
    if pressure_unit == "psi":
        for c in ("whp_bar", "intake_p_bar", "casing_p_bar"):
            if c in out:
                out[c] = pd.to_numeric(out[c], errors="coerce") * 0.0689475729
    elif pressure_unit != "bar":
        raise ValueError("pressure_unit must be explicitly 'bar' or 'psi'")
    qc = qc_report(out)
    return out, {"metadata": metadata, "qc": qc, "mapping": mapping}
