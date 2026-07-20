"""
cpi_study
=========
A market-microstructure event-study toolkit for analyzing NASDAQ (NQ)
futures behavior around U.S. CPI releases, and translating the results
into execution-timing guidance.

See the project README for the full write-up and results. This package
provides the reusable building blocks; scripts/run_analysis.py is the
end-to-end pipeline entrypoint that ties them together.
"""

from . import config
from .cpi_calendar import load_cpi_calendar, releases_between, CPIRelease
from .data_loader import load_raw_csv, basic_quality_report
from .simulate_data import simulate_cpi_event_panel
from .event_windows import build_event_panel, add_event_returns, summarize_event_coverage
from .metrics import (
    realized_vol_by_event_minute,
    spread_by_event_minute,
    price_impact_decay,
    order_flow_persistence,
    event_summary_table,
    corwin_schultz_spread,
    add_estimated_spread,
)
from .execution_sim import simulate_execution_delays, summarize_execution_costs, find_optimal_delay

__version__ = "0.1.0"

__all__ = [
    "config",
    "load_cpi_calendar",
    "releases_between",
    "CPIRelease",
    "load_raw_csv",
    "basic_quality_report",
    "simulate_cpi_event_panel",
    "build_event_panel",
    "add_event_returns",
    "summarize_event_coverage",
    "realized_vol_by_event_minute",
    "spread_by_event_minute",
    "price_impact_decay",
    "order_flow_persistence",
    "event_summary_table",
    "corwin_schultz_spread",
    "add_estimated_spread",
    "simulate_execution_delays",
    "summarize_execution_costs",
    "find_optimal_delay",
]
