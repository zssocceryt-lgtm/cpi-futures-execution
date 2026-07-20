"""
run_analysis.py
================
End-to-end pipeline: load data -> build event windows -> compute metrics ->
simulate execution delays -> save figures and summary tables.

Usage
-----
Demo mode (synthetic data, works immediately, no data required):
    python scripts/run_analysis.py --mode simulate

Real data mode (see data/README.md for how to obtain the datasets):
    1. Put your CSV in data/raw/
    2. Either edit COLUMN_MAP/SOURCE_TZ/TIMESTAMP_FORMAT at the top of
       src/cpi_study/data_loader.py, or pass --timestamp-col/--source-tz/
       --timestamp-format on the command line to override without editing
       source (useful for switching between datasets with different schemas)
    3. python scripts/run_analysis.py --mode real --csv data/raw/your_file.csv
"""

from __future__ import annotations
import argparse

import pandas as pd

from cpi_study.config import PROJECT_ROOT, FIGURES_DIR, TABLES_DIR
from cpi_study.cpi_calendar import releases_between
from cpi_study.simulate_data import simulate_cpi_event_panel
from cpi_study.data_loader import load_raw_csv, basic_quality_report, COLUMN_MAP as DEFAULT_COLUMN_MAP
from cpi_study.event_windows import build_event_panel, add_event_returns, summarize_event_coverage
from cpi_study.metrics import (
    realized_vol_by_event_minute,
    spread_by_event_minute,
    price_impact_decay,
    order_flow_persistence,
    event_summary_table,
    add_estimated_spread,
)
from cpi_study.execution_sim import simulate_execution_delays, summarize_execution_costs, find_optimal_delay
from cpi_study import visualization as viz

FIG_DIR_ROOT = FIGURES_DIR
TABLE_DIR_ROOT = TABLES_DIR


def run_simulate_mode(start: str, end: str, window_minutes: int):
    print(f"[simulate] Generating synthetic NQ futures data around CPI releases "
          f"{start} to {end} ...")
    panel, events = simulate_cpi_event_panel(start=start, end=end, window_minutes=window_minutes)
    panel = add_event_returns(panel)
    return panel, events


def run_real_mode(csv_path: str, start: str, end: str, window_minutes: int,
                   column_map: dict | None = None, source_tz: str | None = None,
                   timestamp_format: str | None = "__default__"):
    print(f"[real] Loading {csv_path} ...")
    load_kwargs = {}
    if column_map is not None:
        load_kwargs["column_map"] = column_map
    if source_tz is not None:
        load_kwargs["source_tz"] = source_tz
    if timestamp_format != "__default__":
        load_kwargs["timestamp_format"] = timestamp_format
    price_df = load_raw_csv(csv_path, **load_kwargs)
    report = basic_quality_report(price_df)
    print("[real] Data quality report:")
    for k, v in report.items():
        print(f"    {k}: {v}")


    bar_span = report["modal_bar_spacing"]
    if bar_span is not None and bar_span > pd.Timedelta(0):
        print(f"[real] Shifting timestamps by +{bar_span} (bar close) for "
              f"event-time labeling ...")
        price_df = price_df.copy()
        price_df["timestamp"] = price_df["timestamp"] + bar_span

    if not report["has_bid_ask"]:
        print("[real] No bid/ask columns found — deriving a spread proxy from "
              "high/low prices (Corwin & Schultz, 2012) ...")
        price_df = add_estimated_spread(price_df)

    releases = releases_between(start, end)
    print(f"[real] Aligning {len(releases)} CPI release events to price data ...")
    panel = build_event_panel(price_df, releases, window_minutes=window_minutes)
    panel = add_event_returns(panel)

    coverage = summarize_event_coverage(panel)
    thin = coverage[coverage["n_minutes"] < (window_minutes)]
    if not thin.empty:
        print(f"[real] WARNING: {len(thin)} events have thin data coverage "
              f"(<{window_minutes} minutes). Results for these events may be noisy.")

    events = pd.DataFrame({
        "event_id": [r.reference_month for r in releases]
    })  # minimal events table; real mode has no ground-truth "surprise" data
    events = coverage[["event_id", "release_date"]].drop_duplicates()
    return panel, events


def main():
    parser = argparse.ArgumentParser(description="NQ futures CPI event-study pipeline")
    parser.add_argument("--mode", choices=["simulate", "real"], default="simulate")
    parser.add_argument("--csv", type=str, default=None, help="Path to real CSV (required for --mode real)")
    parser.add_argument("--start", type=str, default="2023-01-01")
    parser.add_argument("--end", type=str, default="2025-12-31")
    parser.add_argument("--window-minutes", type=int, default=120)
    parser.add_argument("--delays", type=int, nargs="+",
                         default=[0, 1, 2, 3, 5, 10, 15, 30, 60])
    parser.add_argument("--run-name", type=str, default=None,
                         help="Output subfolder name under results/figures and "
                              "results/tables (default: 'real' or 'demo' based on --mode)")
    parser.add_argument("--timestamp-col", type=str, default=None,
                         help="Override: name of the timestamp column in --csv")
    parser.add_argument("--source-tz", type=str, default=None,
                         help="Override: timezone of --csv timestamps if naive (e.g. UTC, America/New_York)")
    parser.add_argument("--timestamp-format", type=str, default="__default__",
                         help="Override: strptime format for --csv timestamps, or 'none' to auto-parse")
    args = parser.parse_args()

    subdir = args.run_name or ("real" if args.mode == "real" else "demo")
    FIG_DIR = FIG_DIR_ROOT / subdir
    TABLE_DIR = TABLE_DIR_ROOT / subdir
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    if args.mode == "simulate":
        panel, events = run_simulate_mode(args.start, args.end, args.window_minutes)
    else:
        if not args.csv:
            raise SystemExit("--csv is required for --mode real")
        col_map_override = None
        if args.timestamp_col is not None:
            col_map_override = dict(DEFAULT_COLUMN_MAP)
            col_map_override["timestamp"] = args.timestamp_col
        ts_format = None if args.timestamp_format == "none" else args.timestamp_format
        panel, events = run_real_mode(
            args.csv, args.start, args.end, args.window_minutes,
            column_map=col_map_override, source_tz=args.source_tz,
            timestamp_format=ts_format,
        )

    n_events = panel["event_id"].nunique()
    print(f"\nBuilt event panel: {len(panel):,} rows across {n_events} CPI events.")

    # metrics
    print("Computing realized volatility profile ...")
    vol_df = realized_vol_by_event_minute(panel)
    vol_df.to_csv(TABLE_DIR / "realized_volatility_by_minute.csv", index=False)

    print("Computing liquidity (spread) profile ...")
    spread_df = spread_by_event_minute(panel)
    if spread_df is not None:
        spread_df.to_csv(TABLE_DIR / "spread_by_minute.csv", index=False)

    print("Computing price-impact decay ...")
    decay_df = price_impact_decay(panel, horizon_minutes=args.window_minutes)
    if not decay_df.empty:
        decay_df.to_csv(TABLE_DIR / "price_impact_decay.csv", index=False)

    print("Computing order-flow persistence (if available) ...")
    ofi_df = order_flow_persistence(panel)
    if ofi_df is not None:
        ofi_df.to_csv(TABLE_DIR / "order_flow_persistence.csv", index=False)

    if args.mode == "simulate":
        summary_events = event_summary_table(events, panel)
        summary_events.to_csv(TABLE_DIR / "event_summary.csv", index=False)

    # ---- execution simulation ----
    # Two framings, because "should I wait?" has a different answer depending
    # on whether you already know which way you want to trade:
    #
    #  "aligned"  = reactive/momentum execution (e.g. "CPI hot -> sell NQ").
    #  "agnostic" = direction-blind execution (e.g. a scheduled rebalance or
    #               hedge that must transact regardless of which way price
    #               moves)
    print("Simulating execution costs across delay intervals (aligned/momentum framing) ...")
    exec_aligned = simulate_execution_delays(panel, delays_minutes=args.delays, direction="aligned")
    cost_summary = summarize_execution_costs(exec_aligned)
    cost_summary.to_csv(TABLE_DIR / "execution_cost_by_delay_aligned.csv", index=False)

    print("Simulating execution costs across delay intervals (agnostic/hedger framing) ...")
    exec_agnostic = simulate_execution_delays(panel, delays_minutes=args.delays, direction="agnostic")
    cost_summary_agnostic = summarize_execution_costs(exec_agnostic)
    cost_summary_agnostic.to_csv(TABLE_DIR / "execution_cost_by_delay_agnostic.csv", index=False)

    optimum = find_optimal_delay(cost_summary)
    print("\n=== Execution timing recommendation: reactive/momentum trade ===")
    for k, v in optimum.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")

    optimum_agnostic = find_optimal_delay(cost_summary_agnostic)
    print("\n=== Execution timing recommendation: direction-blind (hedge/rebalance) trade ===")
    for k, v in optimum_agnostic.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")

    # ---- figures ----
    print("\nSaving figures to", FIG_DIR)
    viz.plot_volatility_profile(vol_df, save_path=str(FIG_DIR / "01_volatility_profile.png"))
    if spread_df is not None:
        viz.plot_spread_profile(spread_df, save_path=str(FIG_DIR / "02_spread_profile.png"))
    if not decay_df.empty:
        viz.plot_price_impact_decay(decay_df, save_path=str(FIG_DIR / "03_price_impact_decay.png"))
    viz.plot_execution_cost_curve(
        cost_summary, save_path=str(FIG_DIR / "04_execution_cost_curve_aligned.png"),
        title="Execution Cost vs. Delay — Reactive/Momentum Trade")
    viz.plot_cost_components(
        cost_summary, save_path=str(FIG_DIR / "05_cost_components_aligned.png"),
        title="Cost Decomposition — Reactive/Momentum Trade")
    viz.plot_execution_cost_curve(
        cost_summary_agnostic, save_path=str(FIG_DIR / "06_execution_cost_curve_agnostic.png"),
        title="Execution Cost vs. Delay — Direction-Blind (Hedge/Rebalance) Trade")
    viz.plot_cost_components(
        cost_summary_agnostic, save_path=str(FIG_DIR / "07_cost_components_agnostic.png"),
        title="Cost Decomposition — Direction-Blind (Hedge/Rebalance) Trade")
    if args.mode == "simulate":
        viz.plot_surprise_vs_reaction(summary_events, save_path=str(FIG_DIR / "08_surprise_vs_reaction.png"))

    print(f"\nDone. Tables in {TABLE_DIR.relative_to(PROJECT_ROOT)}/, "
          f"figures in {FIG_DIR.relative_to(PROJECT_ROOT)}/.")


if __name__ == "__main__":
    main()
