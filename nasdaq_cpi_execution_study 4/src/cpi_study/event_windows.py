"""
event_windows.py
=================
Aligns continuous intraday price data to CPI release events, producing an
"event-time" panel (minutes relative to release) that is the backbone of
the whole analysis. This is standard event-study methodology adapted from
finance (cf. MacKinlay, 1997, "Event Studies in Economics and Finance")
to a high-frequency, single-day-per-event macro-announcement setting.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

from .cpi_calendar import CPIRelease


def build_event_panel(
    price_df: pd.DataFrame,
    releases: list[CPIRelease],
    window_minutes: int = 120,
    price_freq: str = "1min",
) -> pd.DataFrame:
    """
    Slice a continuous minute-bar price_df (must have tz-aware 'timestamp'
    column, ET) into event-time windows around each CPI release.

    Returns a long panel with columns:
      event_id, release_date, reference_month, event_minute, timestamp,
      open, high, low, close, volume, [bid, ask]
    """
    price_df = price_df.sort_values("timestamp").reset_index(drop=True)
    price_df = price_df.set_index("timestamp")

    frames = []
    for i, rel in enumerate(releases):
        start = rel.release_dt_et - pd.Timedelta(minutes=window_minutes)
        end = rel.release_dt_et + pd.Timedelta(minutes=window_minutes)

        window = price_df.loc[start:end].copy()
        if window.empty:
            continue

        window["event_minute"] = (
            (window.index - rel.release_dt_et).total_seconds() / 60.0
        ).round().astype(int)
        window["event_id"] = i
        window["release_date"] = rel.release_date
        window["reference_month"] = rel.reference_month
        window = window.reset_index()
        frames.append(window)

    if not frames:
        raise ValueError(
            "No overlap found between price_df timestamps and any CPI "
            "release window. Check that your price data's date range "
            "actually covers CPI release days, and that timestamps are "
            "correctly localized to America/New_York."
        )

    panel = pd.concat(frames, ignore_index=True)
    cols_front = ["event_id", "release_date", "reference_month", "event_minute", "timestamp"]
    other_cols = [c for c in panel.columns if c not in cols_front]
    return panel[cols_front + other_cols]


def add_event_returns(panel: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
    """
    Add log-return columns computed within each event:
      - ret_1m: minute-over-minute log return
      - cum_ret_from_release: cumulative log return since the release baseline

    Note: this deliberately avoids groupby(...).apply() for the cumulative-
    return calculation. pandas (observed on 3.0.2) can mishandle apply() on
    a *single*-group DataFrame — a per-row Series comes back reshaped into
    a DataFrame instead of concatenated properly, corrupting the result
    without raising an error. Caught by tests/test_event_windows.py. The
    vectorized groupby+merge approach below sidesteps the issue entirely
    and is also faster.
    """
    panel = panel.sort_values(["event_id", "event_minute"]).copy()
    panel["ret_1m"] = panel.groupby("event_id")[price_col].transform(
        lambda s: np.log(s).diff()
    )

    # Baseline bar per event = the one closest to the release. For fine-
    # grained (minute-level) data this is exactly event_minute == 0; for
    # coarser bars (e.g. hourly, where the release falls mid-bar) no bar
    # lands exactly on 0, so fall back to the nearest available bar,
    # preferring the post-release side on ties.
    abs_minute = panel["event_minute"].abs()
    min_dist = abs_minute.groupby(panel["event_id"]).transform("min")
    candidates = panel.loc[abs_minute == min_dist]
    baseline_idx = candidates.groupby("event_id")["event_minute"].idxmax()
    baseline = (
        panel.loc[baseline_idx, ["event_id", price_col]]
        .rename(columns={price_col: "_baseline_price"})
    )
    panel = panel.merge(baseline, on="event_id", how="left")
    panel["cum_ret_from_release"] = np.log(panel[price_col]) - np.log(panel["_baseline_price"])
    panel = panel.drop(columns=["_baseline_price"])
    return panel


def summarize_event_coverage(panel: pd.DataFrame) -> pd.DataFrame:
    """One row per event: how many minutes of data we actually have,
    useful as a QA check before trusting aggregate stats."""
    return (
        panel.groupby(["event_id", "release_date"])
        .agg(n_minutes=("event_minute", "count"),
             min_minute=("event_minute", "min"),
             max_minute=("event_minute", "max"))
        .reset_index()
    )
