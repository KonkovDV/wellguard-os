import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from wellguard.detect import zscore, cusum, first_sustained

def test_zscore_baseline_zero_mean():
    x = np.concatenate([np.zeros(50), np.ones(50)])
    z = zscore(x, warmup=50)
    assert abs(np.median(z[:50])) < 1e-6

def test_cusum_accumulates_on_shift():
    z = np.concatenate([np.zeros(50), 5*np.ones(50)])
    c = cusum(z, k=0.5, positive=True)
    assert c[-1] > c[49]

def test_first_sustained_requires_hold():
    cond = np.array([1,1,0,1,1,1,1,0], dtype=bool)
    assert first_sustained(cond, 3) == 3
    assert first_sustained(np.array([1,1,0,0], dtype=bool), 3) == -1
