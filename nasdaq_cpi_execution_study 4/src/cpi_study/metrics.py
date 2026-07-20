"""
metrics.py
==========
Core measures of price discovery, liquidity, and adverse selection used to
characterize NQ futures behavior around CPI releases.

Metric definitions (standard microstructure literature):

  - Realized volatility (per event-minute, cross-event): stdev of 1-min log
    returns, bucketed by event_minute. Captures the speed/violence of price
    discovery as a function of time-since-release.

  - Quoted spread (bps): (ask - bid) / mid * 10000. Proxy for the cost of
    demanding immediacy; widens when market makers face elevated adverse
    selection risk and pull back size (Glosten & Milgrom, 1985; Kyle, 1985).

  - Price impact / "adverse selection decay": how much of the initial
    release-minute move persists vs. reverts over subsequent minutes.
    A move that partially reverts suggests the initial print overshot on
    thin liquidity; a move that holds suggests genuine price discovery.

  - Order-flow imbalance persistence: autocorrelation of signed order flow
    post-release, a standard adverse-selection signature (informed flow
    tends to be directionally persistent immediately after news).
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def realized_vol_by_event_minute(panel: pd.DataFrame) -> pd.DataFrame:
    """Cross-event realized volatility (stdev of 1-min log returns) for each
    minute relative to the release, plus the mean absolute return (a more
    outlier-robust companion measure)."""
    g = panel.dropna(subset=["ret_1m"]).groupby("event_minute")["ret_1m"]
    out = g.agg(
        realized_vol=lambda s: s.std(),
        mean_abs_ret=lambda s: s.abs().mean(),
        n_obs="count",
    ).reset_index()
    out["realized_vol_bps"] = out["realized_vol"] * 10000
    out["mean_abs_ret_bps"] = out["mean_abs_ret"] * 10000
    return out.sort_values("event_minute")


def spread_by_event_minute(panel: pd.DataFrame) -> pd.DataFrame | None:
    """Average quoted spread (bps) by event minute. Returns None if the
    panel has no bid/ask columns and no estimated-spread column."""
    if {"bid", "ask"}.issubset(panel.columns):
        p = panel.copy()
        mid = (p["bid"] + p["ask"]) / 2
        p["spread_bps"] = (p["ask"] - p["bid"]) / mid * 10000
        return (
            p.groupby("event_minute")["spread_bps"]
            .agg(["mean", "median", "std"])
            .reset_index()
        )
    if "spread_bps_est" in panel.columns:
        return (
            panel.groupby("event_minute")["spread_bps_est"]
            .agg(["mean", "median", "std"])
            .reset_index()
        )
    if "spread_ticks" in panel.columns:
        return (
            panel.groupby("event_minute")["spread_ticks"]
            .agg(["mean", "median", "std"])
            .reset_index()
            .rename(columns={"mean": "spread_ticks_mean",
                              "median": "spread_ticks_median",
                              "std": "spread_ticks_std"})
        )
    return None


def price_impact_decay(panel: pd.DataFrame, horizon_minutes: int = 30) -> pd.DataFrame:
    """
    For each event, measure the cumulative return from release (minute 0) to
    each subsequent minute, expressed as a fraction of the peak absolute
    move reached within the horizon. A ratio near 1.0 at minute k means the
    move has fully "held"; a ratio well below 1.0 means significant reversion
    (overshoot/adverse-selection unwind).
    """
    rows = []
    for eid, g in panel.groupby("event_id"):
        g = g.sort_values("event_minute")
        post = g[(g["event_minute"] >= 0) & (g["event_minute"] <= horizon_minutes)]
        if post.empty or post["cum_ret_from_release"].isna().all():
            continue
        peak_abs = post["cum_ret_from_release"].abs().max()
        if peak_abs == 0 or np.isnan(peak_abs):
            continue
        for _, r in post.iterrows():
            rows.append({
                "event_id": eid,
                "event_minute": r["event_minute"],
                "cum_ret": r["cum_ret_from_release"],
                "holding_ratio": r["cum_ret_from_release"] / peak_abs
                                  if np.sign(r["cum_ret_from_release"]) == np.sign(
                                      post.loc[post["cum_ret_from_release"].abs().idxmax(),
                                               "cum_ret_from_release"])
                                  else np.nan,
            })
    detail = pd.DataFrame(rows)
    if detail.empty:
        return detail
    summary = (
        detail.groupby("event_minute")["holding_ratio"]
        .agg(mean_holding_ratio="mean", median_holding_ratio="median", n="count")
        .reset_index()
    )
    return summary


def order_flow_persistence(panel: pd.DataFrame, max_lag: int = 10) -> pd.DataFrame | None:
    """
    Post-release autocorrelation of order_flow_imbalance at lags 1..max_lag,
    averaged across events. Only available if the panel carries an
    'order_flow_imbalance' column (present in simulated data; would need to
    be derived from trade-and-quote data for real feeds, e.g. via the
    Lee-Ready algorithm).
    """
    if "order_flow_imbalance" not in panel.columns:
        return None

    rows = []
    for eid, g in panel.groupby("event_id"):
        g = g.sort_values("event_minute")
        post = g[g["event_minute"] >= 0]["order_flow_imbalance"].reset_index(drop=True)
        if len(post) <= max_lag + 1:
            continue
        for lag in range(1, max_lag + 1):
            corr = post.autocorr(lag=lag)
            rows.append({"event_id": eid, "lag": lag, "autocorr": corr})
    detail = pd.DataFrame(rows)
    if detail.empty:
        return None
    return (
        detail.groupby("lag")["autocorr"]
        .agg(mean_autocorr="mean", median_autocorr="median", n="count")
        .reset_index()
    )


def corwin_schultz_spread(df: pd.DataFrame, high_col: str = "high", low_col: str = "low") -> np.ndarray:
    """
    Corwin & Schultz (2012) high-low bid-ask spread estimator.
    "A Simple Way to Estimate Bid-Ask Spreads from Daily High and Low Prices",
    Journal of Finance, 67(2), 719-760.

    Estimates the proportional quoted spread using only two consecutive
    bars' high/low prices — no bid/ask data required. Designed for daily
    bars originally, but is commonly applied at intraday frequencies as a
    liquidity proxy when true quote data isn't available (as is the case
    for most free/Kaggle-distributed futures OHLCV data).

    Returns an array the same length as df, spread estimate in proportional
    terms (multiply by 10000 for bps); first element is NaN (needs a pair).
    Negative raw estimates (an artifact of the method under low volatility)
    are floored at zero, per the original paper's recommendation.
    """
    H = df[high_col].to_numpy(dtype=float)
    L = df[low_col].to_numpy(dtype=float)
    n = len(df)
    spread = np.full(n, np.nan)

    k = 3 - 2 * np.sqrt(2)
    valid = (H > 0) & (L > 0) & (H >= L)

    for i in range(1, n):
        if not (valid[i - 1] and valid[i]):
            continue
        H1, L1, H2, L2 = H[i - 1], L[i - 1], H[i], L[i]
        beta = np.log(H1 / L1) ** 2 + np.log(H2 / L2) ** 2
        gamma = np.log(max(H1, H2) / min(L1, L2)) ** 2
        alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
        s = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
        spread[i] = max(s, 0.0) if np.isfinite(s) else np.nan

    return spread


def add_estimated_spread(df: pd.DataFrame) -> pd.DataFrame:
    """Attach a 'spread_bps_est' column using the Corwin-Schultz estimator.
    Use this for real OHLCV data that lacks bid/ask quotes."""
    df = df.copy()
    est = corwin_schultz_spread(df)
    df["spread_bps_est"] = est * 10000
    return df


def event_summary_table(events: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:



    """One row per CPI event with headline stats: surprise magnitude,
    release-minute return, and realized vol in the first 5 minutes post
    vs. a calm baseline (minutes -60 to -10)."""
    rows = []
    for eid, g in panel.groupby("event_id"):
        g = g.sort_values("event_minute")
        baseline = g[(g["event_minute"] >= -60) & (g["event_minute"] <= -10)]["ret_1m"]
        post5 = g[(g["event_minute"] >= 0) & (g["event_minute"] <= 5)]["ret_1m"]
        release_ret = g.loc[g["event_minute"] == 0, "ret_1m"]
        rows.append({
            "event_id": eid,
            "baseline_vol_bps": baseline.std() * 10000 if len(baseline) > 1 else np.nan,
            "post_5min_vol_bps": post5.std() * 10000 if len(post5) > 1 else np.nan,
            "release_minute_ret_bps": release_ret.iloc[0] * 10000 if len(release_ret) else np.nan,
        })
    stats = pd.DataFrame(rows)
    out = events.merge(stats, on="event_id", how="left")
    out["vol_ratio_post_vs_baseline"] = out["post_5min_vol_bps"] / out["baseline_vol_bps"]
    return out
