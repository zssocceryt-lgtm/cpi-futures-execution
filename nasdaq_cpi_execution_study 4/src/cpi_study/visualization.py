"""
visualization.py
=================
Plotting functions for the CPI event-study pipeline. Uses matplotlib only
(no seaborn dependency) so the repo has a minimal footprint.
"""

from __future__ import annotations
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.grid": True,
    "grid.color": "#e0e0e0",
    "grid.linewidth": 0.6,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
})

ACCENT = "#1f5fbf"
ACCENT2 = "#c0392b"
ACCENT3 = "#2e8b57"


def plot_volatility_profile(vol_df: pd.DataFrame, save_path: str | None = None):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(vol_df["event_minute"], vol_df["realized_vol_bps"], color=ACCENT, lw=1.8, label="Realized vol (stdev, bps)")
    ax.plot(vol_df["event_minute"], vol_df["mean_abs_ret_bps"], color=ACCENT3, lw=1.2, ls="--", label="Mean |return| (bps)")
    ax.axvline(0, color=ACCENT2, lw=1.2, ls=":")
    ax.text(0.5, ax.get_ylim()[1] * 0.95, "CPI release", color=ACCENT2, fontsize=9, ha="left")
    ax.set_xlabel("Minutes relative to CPI release")
    ax.set_ylabel("1-minute return volatility (bps)")
    ax.set_title("NQ Futures Volatility Around CPI Releases")
    ax.legend(frameon=False)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_spread_profile(spread_df: pd.DataFrame, save_path: str | None = None,
                         title: str = "Liquidity (Spread Proxy) Around CPI Releases"):
    fig, ax = plt.subplots(figsize=(9, 5))
    if "mean" in spread_df.columns:
        y = spread_df["mean"]
        ylabel = "Estimated spread (bps)"
    else:
        y = spread_df["spread_ticks_mean"]
        ylabel = "Modeled spread (ticks)"
    ax.plot(spread_df["event_minute"], y, color=ACCENT, lw=1.8)
    ax.axvline(0, color=ACCENT2, lw=1.2, ls=":")
    ax.set_xlabel("Minutes relative to CPI release")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_price_impact_decay(decay_df: pd.DataFrame, save_path: str | None = None):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(decay_df["event_minute"], decay_df["mean_holding_ratio"], color=ACCENT, lw=1.8)
    ax.axhline(1.0, color="#888888", lw=1, ls="--")
    ax.set_xlabel("Minutes since release")
    ax.set_ylabel("Fraction of peak move retained")
    ax.set_title("Price Impact Decay: Does the Initial Move Hold or Revert?")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_execution_cost_curve(cost_summary: pd.DataFrame, save_path: str | None = None,
                               title: str = "Execution Cost vs. Post-Release Delay"):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(cost_summary["delay_minutes"], cost_summary["mean_total_cost_bps"],
            color=ACCENT, lw=2, marker="o", label="Mean total execution cost")
    ax.plot(cost_summary["delay_minutes"], cost_summary["p90_total_cost_bps"],
            color=ACCENT2, lw=1.5, marker="o", ls="--", label="90th percentile (tail risk)")
    ax.fill_between(cost_summary["delay_minutes"],
                     cost_summary["mean_slippage_bps"],
                     cost_summary["mean_total_cost_bps"],
                     alpha=0.08, color=ACCENT3)
    ax.set_xlabel("Execution delay after release (minutes)")
    ax.set_ylabel("Estimated execution cost (bps)")
    ax.set_title(title)
    ax.legend(frameon=False)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_cost_components(cost_summary: pd.DataFrame, save_path: str | None = None,
                          title: str = "Execution Cost Decomposition: Waiting Cost vs. Spread Cost"):
    fig, ax = plt.subplots(figsize=(9, 5))
    width = 0.35
    x = np.arange(len(cost_summary))
    ax.bar(x - width / 2, cost_summary["mean_slippage_bps"], width,
           label="Slippage from waiting", color=ACCENT)
    ax.bar(x + width / 2, cost_summary["mean_spread_cost_bps"], width,
           label="Spread cost at execution", color=ACCENT3)
    ax.set_xticks(x)
    ax.set_xticklabels(cost_summary["delay_minutes"])
    ax.set_xlabel("Execution delay after release (minutes)")
    ax.set_ylabel("Cost component (bps)")
    ax.set_title(title)
    ax.legend(frameon=False)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig


def plot_surprise_vs_reaction(events_summary: pd.DataFrame, save_path: str | None = None):
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(events_summary["surprise_bps"], events_summary["release_minute_ret_bps"],
               color=ACCENT, alpha=0.75, edgecolor="white", s=60)
    ax.axhline(0, color="#999999", lw=0.8)
    ax.axvline(0, color="#999999", lw=0.8)
    ax.set_xlabel("CPI surprise (bps, actual vs. consensus proxy)")
    ax.set_ylabel("Release-minute NQ return (bps)")
    ax.set_title("CPI Surprise Magnitude vs. Immediate Futures Reaction")
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=150)
    return fig
