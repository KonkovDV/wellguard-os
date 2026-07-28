"""Strict intake contract for a Gazprom Neft archive.

No customer archive is bundled. This module validates an exported, anonymized
CSV/Parquet file after the asset owner supplies the tag dictionary and units.
Contract fields mirror the INDUSTRIX application letter (required / conditional /
optional extras) without inventing field performance claims.
"""
from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
from ..schema import qc_report, coerce_telemetry

REQUIRED_METADATA = ["asset_id_hash", "well_id_hash", "timezone", "sampling_interval_s", "unit_system"]
CONTRACT_PATH = Path(__file__).resolve().parents[2] / "data" / "contracts" / "gpn_archive_schema.json"


def load_contract(path: str | Path | None = None) -> dict:
    p = Path(path) if path else CONTRACT_PATH
    return json.loads(p.read_text(encoding="utf-8"))


def validate_metadata(metadata: dict) -> list[str]:
    return [k for k in REQUIRED_METADATA if k not in metadata or metadata[k] in (None, "")]


def validate_against_contract(df: pd.DataFrame, contract: dict | None = None) -> dict:
    """Check required/conditional/optional channel presence against the frozen contract."""
    c = contract or load_contract()
    required = list(c.get("required_channels") or [])
    conditional = list(c.get("conditional_channels") or [])
    optional = list(c.get("optional_channels") or [])
    missing_required = [x for x in required if x not in df.columns]
    missing_conditional = [x for x in conditional if x not in df.columns]
    present_optional = [x for x in optional if x in df.columns]
    unknown = [
        col for col in df.columns
        if col not in set(required + conditional + optional)
    ]
    return {
        "contract_version": c.get("version"),
        "missing_required": missing_required,
        "missing_conditional": missing_conditional,
        "present_optional": present_optional,
        "unknown_columns": unknown,
        "contract_ok": len(missing_required) == 0,
    }


def load_archive(path: str | Path, mapping: dict[str, str], metadata: dict,
                 *, pressure_unit: str,
                 contract_path: str | Path | None = None) -> tuple[pd.DataFrame, dict]:
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
    out = coerce_telemetry(out)
    contract = load_contract(contract_path)
    contract_report = validate_against_contract(out, contract)
    if not contract_report["contract_ok"]:
        raise ValueError(
            f"archive missing required channels: {contract_report['missing_required']}"
        )
    qc = qc_report(out)
    return out, {
        "metadata": metadata,
        "qc": qc,
        "mapping": mapping,
        "contract": contract_report,
        "pressure_unit": pressure_unit,
        "read_only": True,
    }
