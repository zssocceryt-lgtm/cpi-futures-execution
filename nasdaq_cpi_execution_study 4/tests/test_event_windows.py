"""
Bare-minimum tests for event_windows.py — verifies event-time alignment
on a tiny hand-built price series, independent of any real dataset.
"""
from datetime import datetime, timedelta
import zoneinfo

import pandas as pd

from cpi_study.cpi_calendar import CPIRelease
from cpi_study.event_windows import build_event_panel, add_event_returns

ET = zoneinfo.ZoneInfo("America/New_York")


def _toy_release(day="2024-01-11"):
    dt = datetime.strptime(day, "%Y-%m-%d").replace(hour=8, minute=30, tzinfo=ET)
    return CPIRelease(reference_month="2023-12", release_date=dt.date(), release_dt_et=dt)


def _toy_minute_prices(release_dt, n_before=5, n_after=5, start_price=100.0):
    """One bar per minute, price ticks up by 1 every minute for traceability."""
    timestamps = [release_dt + timedelta(minutes=m) for m in range(-n_before, n_after + 1)]
    prices = [start_price + i for i in range(len(timestamps))]
    return pd.DataFrame({
        "timestamp": timestamps,
        "open": prices, "high": prices, "low": prices, "close": prices,
        "volume": [100] * len(timestamps),
    })


def test_event_minute_alignment_is_exact_for_minute_bars():
    release = _toy_release()
    prices = _toy_minute_prices(release.release_dt_et)
    panel = build_event_panel(prices, [release], window_minutes=5)

    # The bar exactly at the release timestamp should be labeled event_minute == 0
    row = panel.loc[panel["event_minute"] == 0]
    assert len(row) == 1
    assert row.iloc[0]["close"] == 105.0  # 5th bar after start_price=100


def test_cumulative_return_baseline_is_release_bar():
    release = _toy_release()
    prices = _toy_minute_prices(release.release_dt_et)
    panel = build_event_panel(prices, [release], window_minutes=5)
    panel = add_event_returns(panel)

    base_row = panel.loc[panel["event_minute"] == 0].iloc[0]
    assert abs(base_row["cum_ret_from_release"]) < 1e-9
