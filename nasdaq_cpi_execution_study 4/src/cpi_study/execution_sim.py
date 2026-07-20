"""
execution_sim.py
=================
Translates the price/liquidity dynamics into a concrete trading-ops
question: "If I need to establish a position around a CPI print, how does
my expected execution cost change depending on how long I wait after the
release before sending the order?"

Methodology
-----------
For each event and each candidate delay d (minutes after release), we
simulate a simple marketable order:
  - Entry price = the mid/close price at event_minute == d
  - Slippage vs. arrival price = |price(d) - price(0)| in bps
    (captures cost of having *waited*, i.e. the market moving away from you)
  - Spread cost at time d = half the quoted/modeled spread in bps
    (captures cost of demanding immediacy at that moment)
  - Total estimated execution cost = slippage_from_waiting + spread_cost

This is intentionally a simple, transparent model — not a full limit-order-
book simulation — designed to make the *tradeoff* legible: waiting reduces
spread cost (liquidity has recovered) but increases the chance the market
has already moved against you (adverse selection / price discovery has
partially completed without you).
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from .config import NQ_TICK_SIZE


def simulate_execution_delays(
    panel: pd.DataFrame,
    delays_minutes: list[int] = (0, 1, 2, 3, 5, 10, 15, 30, 60),
    direction: str = "aligned",  # "aligned" = trade in direction of eventual move
) -> pd.DataFrame:
    """
    For each event and each delay, compute realized slippage-from-waiting
    and spread cost at execution.

    direction:
      "aligned"  -> assumes the trader is trying to trade in the direction
                    the market ultimately moves (a momentum/reaction trade,
                    e.g. "CPI hot -> sell NQ"). This is the setting where
                    waiting cost is most punishing, since you're chasing.
      "agnostic" -> reports unsigned slippage magnitude only, no directional
                    assumption.
    """
    has_bidask = {"bid", "ask"}.issubset(panel.columns)
    has_spread_est = "spread_bps_est" in panel.columns
    has_spread_ticks = "spread_ticks" in panel.columns

    rows = []
    for eid, g in panel.groupby("event_id"):
        g = g.sort_values("event_minute").set_index("event_minute")

        post_release_minutes = sorted(m for m in g.index if m >= 0)
        if not post_release_minutes:
            continue
        # "Arrival" = earliest bar at or after the release. For minute-level
        # data this is exactly event_minute 0; for coarser bars (e.g. hourly
        # data where the release falls mid-bar) this is the nearest bar
        # available, and delays are measured relative to it rather than to
        # an exact (and possibly nonexistent) minute-0 timestamp.
        arrival_minute = post_release_minutes[0]
        arrival_price = g.loc[arrival_minute, "close"]

        # map each requested delay to the nearest available post-release bar
        available_delays = []
        seen_minutes = set()
        for d in delays_minutes:
            target = arrival_minute + d
            actual = min(post_release_minutes, key=lambda m: abs(m - target))
            if actual in seen_minutes:
                continue
            seen_minutes.add(actual)
            available_delays.append((d, actual))

        if not available_delays:
            continue
        terminal_d, terminal_minute = available_delays[-1]
        terminal_move = g.loc[terminal_minute, "close"] - arrival_price
        move_sign = np.sign(terminal_move) if terminal_move != 0 else 1.0

        for d, actual_minute in available_delays:
            exec_price = g.loc[actual_minute, "close"]
            raw_slippage_bps = (exec_price - arrival_price) / arrival_price * 10000

            if direction == "aligned":
                # cost of waiting = how much the price moved *in the direction
                # you'd be chasing* before you executed
                slippage_cost_bps = move_sign * raw_slippage_bps
            else:
                slippage_cost_bps = abs(raw_slippage_bps)

            if has_bidask:
                mid = (g.loc[actual_minute, "bid"] + g.loc[actual_minute, "ask"]) / 2
                half_spread_bps = (g.loc[actual_minute, "ask"] - g.loc[actual_minute, "bid"]) / mid / 2 * 10000
            elif has_spread_est:
                half_spread_bps = g.loc[actual_minute, "spread_bps_est"] / 2
            elif has_spread_ticks:
                # tick size is a shared project constant (config.py) rather
                # than a magic number, since it's used in more than one place
                half_spread_bps = (g.loc[actual_minute, "spread_ticks"] * NQ_TICK_SIZE / 2) / exec_price * 10000
            else:
                half_spread_bps = np.nan

            total_cost_bps = slippage_cost_bps + half_spread_bps

            rows.append({
                "event_id": eid,
                "delay_minutes": d,
                "actual_bar_minute": actual_minute,
                "slippage_from_waiting_bps": slippage_cost_bps,
                "half_spread_cost_bps": half_spread_bps,
                "total_execution_cost_bps": total_cost_bps,
            })

    return pd.DataFrame(rows)


def summarize_execution_costs(exec_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate execution cost simulation across events, by delay."""
    summary = (
        exec_df.groupby("delay_minutes")
        .agg(
            mean_slippage_bps=("slippage_from_waiting_bps", "mean"),
            median_slippage_bps=("slippage_from_waiting_bps", "median"),
            mean_spread_cost_bps=("half_spread_cost_bps", "mean"),
            mean_total_cost_bps=("total_execution_cost_bps", "mean"),
            median_total_cost_bps=("total_execution_cost_bps", "median"),
            p90_total_cost_bps=("total_execution_cost_bps", lambda s: s.quantile(0.90)),
            std_total_cost_bps=("total_execution_cost_bps", "std"),
            n=("total_execution_cost_bps", "count"),
        )
        .reset_index()
        .sort_values("delay_minutes")
    )
    return summary


def find_optimal_delay(cost_summary: pd.DataFrame, cost_col: str = "mean_total_cost_bps") -> dict:
    """Return the delay minimizing expected total execution cost, plus
    context (cost at t=0 for comparison, and the 'safe' 90th-percentile-
    minimizing delay for risk-averse execution)."""
    best_mean = cost_summary.loc[cost_summary[cost_col].idxmin()]
    best_p90 = cost_summary.loc[cost_summary["p90_total_cost_bps"].idxmin()]
    at_zero = cost_summary.loc[cost_summary["delay_minutes"] == 0]
    return {
        "best_mean_delay_minutes": int(best_mean["delay_minutes"]),
        "best_mean_cost_bps": float(best_mean[cost_col]),
        "best_p90_delay_minutes": int(best_p90["delay_minutes"]),
        "best_p90_cost_bps": float(best_p90["p90_total_cost_bps"]),
        "immediate_execution_cost_bps": float(at_zero[cost_col].iloc[0]) if not at_zero.empty else np.nan,
    }
