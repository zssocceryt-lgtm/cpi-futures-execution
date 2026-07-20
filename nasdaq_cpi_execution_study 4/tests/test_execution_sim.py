"""
Bare-minimum tests for execution_sim.py — specifically the nearest-available-
bar matching logic, since that's the part that silently produced wrong
results (assumed an exact event_minute==0 bar) before being fixed for
coarse-resolution (hourly) data.
"""
import pandas as pd

from cpi_study.execution_sim import simulate_execution_delays


def _toy_panel_exact_minutes():
    """One event, price rises 1 point per minute, exact minute-0 bar exists."""
    minutes = list(range(-2, 6))
    prices = [100.0 + m for m in minutes]  # monotonic rise through release
    return pd.DataFrame({
        "event_id": [0] * len(minutes),
        "event_minute": minutes,
        "close": prices,
    })


def _toy_panel_offset_minutes():
    """One event, no bar lands on minute 0 (mimics hourly data where the
    release falls mid-bar) — bars sit at -30, +30, +90 instead."""
    minutes = [-30, 30, 90]
    prices = [100.0, 105.0, 110.0]
    return pd.DataFrame({
        "event_id": [0] * len(minutes),
        "event_minute": minutes,
        "close": prices,
    })


def test_exact_minute_zero_used_as_arrival():
    panel = _toy_panel_exact_minutes()
    result = simulate_execution_delays(panel, delays_minutes=[0, 1, 2], direction="agnostic")
    row0 = result.loc[result["delay_minutes"] == 0].iloc[0]
    assert row0["actual_bar_minute"] == 0
    assert row0["slippage_from_waiting_bps"] == 0.0


def test_nearest_bar_used_when_no_exact_match():
    """This is the regression test for the hourly-data bug: arrival should
    fall back to the nearest available post-release bar, not silently
    produce an empty result."""
    panel = _toy_panel_offset_minutes()
    result = simulate_execution_delays(panel, delays_minutes=[0, 60], direction="agnostic")
    assert not result.empty
    row0 = result.loc[result["delay_minutes"] == 0].iloc[0]
    assert row0["actual_bar_minute"] == 30  # nearest available bar to release
