"""
config.py
=========

"""

from __future__ import annotations
from pathlib import Path

# Project root = two levels up from this file (src/cpi_study/config.py -> repo root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"

DEFAULT_MINUTE_CSV = RAW_DATA_DIR / "Dataset_NQ_1min_2022_2025.csv"
DEFAULT_HOURLY_CSV = RAW_DATA_DIR / "NQ_in_1_hour.csv"

NQ_TICK_SIZE = 0.25

# CPI releases are always 8:30 AM Eastern Time.
CPI_RELEASE_HOUR_ET = 8
CPI_RELEASE_MINUTE_ET = 30
