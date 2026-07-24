from __future__ import annotations
import numpy as np
import pandas as pd

EPS = 1e-6


def robust_baseline(x: np.ndarray, warmup: int, start: int = 0):
    """Median and MAD from a contiguous warmup window (assumed-normal history)."""
    w = np.asarray(x[start:start + warmup], dtype=float)
    w = w[np.isfinite(w)]
    if len(w) == 0:
        return 0.0, 1.0
    med = np.median(w)
    mad = np.median(np.abs(w - med))
    iqr = np.subtract(*np.nanpercentile(w, [75, 25])) if len(w) > 1 else 0.0
    scale = max(1.4826 * mad, iqr / 1.349, 1e-3)
    return med, scale


def stable_warmup_start(x: np.ndarray, warmup: int, search_end: int | None = None) -> int:
    """Optional helper: lowest-MAD contiguous window (kept for experiments / tests)."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n <= warmup:
        return 0
    search_end = n // 2 if search_end is None else search_end
    search_end = min(max(warmup, search_end), n)
    best_i, best_mad = 0, float("inf")
    last = max(1, search_end - warmup + 1)
    for i in range(0, last):
        w = x[i:i + warmup]
        w = w[np.isfinite(w)]
        if len(w) < max(5, warmup // 3):
            continue
        med = np.median(w)
        mad = float(np.median(np.abs(w - med)))
        if mad < best_mad:
            best_mad, best_i = mad, i
    return int(best_i)


def zscore(x: np.ndarray, warmup: int, baseline_start: int = 0) -> np.ndarray:
    med, scale = robust_baseline(x, warmup, start=baseline_start)
    x = np.asarray(x, dtype=float)
    return np.nan_to_num((x - med) / scale, nan=0.0, posinf=0.0, neginf=0.0)


def cusum(z: np.ndarray, k: float = 0.5, positive: bool = True) -> np.ndarray:
    """One-sided CUSUM accumulator on a z-score signal."""
    s = np.zeros_like(z, dtype=float)
    acc = 0.0
    for i in range(len(z)):
        val = (z[i] - k) if positive else (-z[i] - k)
        acc = max(0.0, acc + val)
        s[i] = acc
    return s


def first_sustained(cond: np.ndarray, hold: int) -> int:
    """First index where a boolean condition stays true for `hold` samples."""
    run = 0
    for i, c in enumerate(cond):
        run = run + 1 if c else 0
        if run >= hold:
            return i - hold + 1
    return -1
