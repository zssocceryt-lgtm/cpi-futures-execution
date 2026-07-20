"""
Bare-minimum tests for metrics.py — focused on corwin_schultz_spread, since
it's the one non-obvious piece of math in the module (a published formula,
not something obviously "correct by construction" the way a groupby is).
"""
import numpy as np
import pandas as pd

from cpi_study.metrics import corwin_schultz_spread


def test_corwin_schultz_returns_one_value_per_row():
    df = pd.DataFrame({
        "high": [101.0, 102.0, 100.5, 103.0],
        "low": [99.0, 100.0, 99.5, 101.0],
    })
    result = corwin_schultz_spread(df)
    assert len(result) == len(df)
    assert np.isnan(result[0])  # first row has no prior bar to pair with


def test_corwin_schultz_is_never_negative():
    """The paper recommends flooring negative estimates at zero — a real
    (if noisy) failure mode when volatility is very low."""
    df = pd.DataFrame({
        "high": [100.01, 100.02, 100.01, 100.03, 100.02],
        "low": [100.00, 100.00, 100.00, 100.00, 100.00],
    })
    result = corwin_schultz_spread(df)
    valid = result[~np.isnan(result)]
    assert (valid >= 0).all()


def test_corwin_schultz_wider_range_gives_wider_spread():
    tight = pd.DataFrame({"high": [100.1, 100.1, 100.1], "low": [100.0, 100.0, 100.0]})
    wide = pd.DataFrame({"high": [105.0, 105.0, 105.0], "low": [100.0, 100.0, 100.0]})
    tight_spread = np.nanmean(corwin_schultz_spread(tight))
    wide_spread = np.nanmean(corwin_schultz_spread(wide))
    assert wide_spread > tight_spread
