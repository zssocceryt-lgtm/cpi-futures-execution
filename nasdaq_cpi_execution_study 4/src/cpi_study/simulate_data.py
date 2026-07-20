"""
simulate_data.py
=================
Generates synthetic NASDAQ (NQ) futures minute-bar data around CPI release
events, calibrated to stylized facts documented in the market-microstructure
literature on macro-announcement effects (e.g. volatility spikes at release,
rapid decay over 15-30 minutes, transient spread widening, and a brief
adverse-selection window where informed order flow dominates):

  - Andersen & Bollerslev (1998), "Deseasonalizing the Volatility Persistence..."
  - Balduzzi, Elton & Green (2001), "Economic News and Bond Prices"
  - Lucca & Moench (2015), "The Pre-FOMC Announcement Drift" (analogous
    pre-announcement stylized facts apply to scheduled macro releases)
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import timedelta

from .cpi_calendar import load_cpi_calendar

RNG_SEED = 42


def _simulate_single_event_day(
    release_dt_et,
    rng: np.random.Generator,
    window_minutes: int = 120,
    base_price: float = 18000.0,
    base_minute_vol_bps: float = 3.0,   # "normal" 1-min return stdev, bps
    spike_vol_bps: float = 28.0,        # release-minute return stdev, bps
    decay_halflife_min: float = 6.0,    # vol decay half-life post release
    base_spread_ticks: float = 1.0,
    spike_spread_ticks: float = 6.0,
    spread_decay_halflife_min: float = 4.0,
    tick_size: float = 0.25,
    drift_surprise_bps: float = 0.0,    # signed jump from "surprise" magnitude
) -> pd.DataFrame:
    """
    Build one event-day minute-bar panel spanning
    [release - window_minutes, release + window_minutes].
    Event time 0 = the minute the CPI print hits the tape.
    """
    minutes = np.arange(-window_minutes, window_minutes + 1)
    timestamps = [release_dt_et + timedelta(minutes=int(m)) for m in minutes]

    # --- volatility profile: flat pre-release, spike at t=0, exponential decay ---
    vol_bps = np.full(len(minutes), base_minute_vol_bps, dtype=float)
    post_mask = minutes >= 0
    decay = spike_vol_bps * (0.5 ** (minutes[post_mask] / decay_halflife_min))
    vol_bps[post_mask] = np.maximum(base_minute_vol_bps, decay)
    # Small pre-release liquidity-thinning tick (minutes -3..-1): mild vol uptick
    pre_tick_mask = (minutes >= -3) & (minutes < 0)
    vol_bps[pre_tick_mask] *= 1.4

    # --- spread profile (proxy for liquidity / execution cost) ---
    spread_ticks = np.full(len(minutes), base_spread_ticks, dtype=float)
    spread_decay = spike_spread_ticks * (0.5 ** (minutes[post_mask] / spread_decay_halflife_min))
    spread_ticks[post_mask] = np.maximum(base_spread_ticks, spread_decay)
    spread_ticks[pre_tick_mask] *= 1.3

    # --- simulate log returns ---
    returns = rng.normal(loc=0.0, scale=vol_bps / 10000.0, size=len(minutes))
    # inject the release-minute "surprise" jump (signed, drawn once per event)
    release_idx = np.where(minutes == 0)[0][0]
    returns[release_idx] += drift_surprise_bps / 10000.0

    log_price = np.log(base_price) + np.cumsum(returns)
    mid_price = np.exp(log_price)

    # --- synthetic order-flow imbalance / adverse-selection proxy ---
    # Elevated immediately post-release, decaying similarly to vol; captures the
    # idea that informed flow dominates briefly after the number hits the tape.
    ofi_signal = np.zeros(len(minutes))
    ofi_signal[post_mask] = np.sign(drift_surprise_bps + 1e-9) * (
        0.8 * (0.5 ** (minutes[post_mask] / decay_halflife_min))
    )
    ofi_noise = rng.normal(0, 0.15, size=len(minutes))
    order_flow_imbalance = np.clip(ofi_signal + ofi_noise, -1, 1)

    # --- volume profile: surges at release, decays ---
    base_vol = rng.gamma(shape=4.0, scale=50.0, size=len(minutes))
    vol_multiplier = np.ones(len(minutes))
    vol_multiplier[post_mask] = 1 + 9 * (0.5 ** (minutes[post_mask] / 4.0))
    volume = (base_vol * vol_multiplier).round().astype(int)

    half_spread = (spread_ticks * tick_size) / 2.0
    bid = mid_price - half_spread
    ask = mid_price + half_spread

    # OHLC per minute bar (simple: open=prev close-ish, synthesize with noise)
    intraminute_noise = rng.normal(0, vol_bps / 10000.0 / 2, size=len(minutes))
    high = mid_price * (1 + np.abs(intraminute_noise))
    low = mid_price * (1 - np.abs(intraminute_noise))
    open_ = np.roll(mid_price, 1)
    open_[0] = mid_price[0]

    df = pd.DataFrame({
        "timestamp": timestamps,
        "event_minute": minutes,
        "open": open_,
        "high": high,
        "low": low,
        "close": mid_price,
        "bid": bid,
        "ask": ask,
        "spread_ticks": spread_ticks,
        "volume": volume,
        "order_flow_imbalance": order_flow_imbalance,
    })
    return df


def simulate_cpi_event_panel(
    start: str = "2023-01-01",
    end: str = "2025-12-31",
    window_minutes: int = 120,
    seed: int = RNG_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simulate minute-bar NQ futures data around every CPI release in [start, end].

    Returns
    -------
    panel : DataFrame
        Long-format minute bars, one row per (event, minute), tagged with
        event_id and release metadata.
    events : DataFrame
        One row per CPI release event with metadata (surprise magnitude, etc).
    """
    rng = np.random.default_rng(seed)
    releases = [r for r in load_cpi_calendar() if start <= str(r.release_date) <= end]

    panels = []
    event_rows = []
    running_price = 18000.0

    for i, rel in enumerate(releases):
        # Simulate a CPI "surprise" (actual - consensus, in bps of index price
        # reaction) — heavy-ish tails to mimic occasional large surprises.
        surprise_bps = rng.standard_t(df=4) * 6.0

        day_df = _simulate_single_event_day(
            release_dt_et=rel.release_dt_et,
            rng=rng,
            window_minutes=window_minutes,
            base_price=running_price,
            drift_surprise_bps=surprise_bps,
        )
        day_df.insert(0, "event_id", i)
        day_df.insert(1, "release_date", rel.release_date)
        day_df.insert(2, "reference_month", rel.reference_month)
        panels.append(day_df)

        event_rows.append({
            "event_id": i,
            "release_date": rel.release_date,
            "reference_month": rel.reference_month,
            "release_dt_et": rel.release_dt_et,
            "surprise_bps": surprise_bps,
            "abs_surprise_bps": abs(surprise_bps),
        })

        # carry price forward (small persistent drift between events) so the
        # series looks like a continuous, non-stationary futures price path
        running_price = day_df["close"].iloc[-1] * (1 + rng.normal(0, 0.01))

    panel = pd.concat(panels, ignore_index=True)
    events = pd.DataFrame(event_rows)
    return panel, events


if __name__ == "__main__":
    panel, events = simulate_cpi_event_panel(start="2024-01-01", end="2024-12-31")
    print(panel.shape, events.shape)
    print(events.head())
    print(panel[panel.event_minute.between(-2, 2)].head(10))
