from __future__ import annotations
import pandas as pd
from .classify import classify
from .recommend import operator_card
from .schema import coerce_telemetry


def run(df: pd.DataFrame) -> dict:
    """End-to-end: coerce/QC -> physics features -> detect/classify -> governed card."""
    cls = classify(coerce_telemetry(df))
    return operator_card(cls)
