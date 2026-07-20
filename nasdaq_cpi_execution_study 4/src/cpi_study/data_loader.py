"""
data_loader.py
===============
Loads NASDAQ futures intraday data from a local CSV (e.g. a Kaggle dataset)
and normalizes it to the schema used throughout this project:

    timestamp (tz-aware, America/New_York), open, high, low, close, volume
    [bid], [ask]   -- optional, enables spread-based liquidity metrics

Kaggle NQ/NASDAQ-futures datasets vary a lot in column naming and timestamp
format, so this loader is intentionally configurable rather than hardcoded
to one schema. Point COLUMN_MAP at your file's actual column names.
"""

from __future__ import annotations
import pandas as pd
import zoneinfo
from pathlib import Path

ET = zoneinfo.ZoneInfo("America/New_York")

# ---------------------------------------------------------------------------
# EDIT THIS to match your Kaggle CSV's column names.
# Only 'timestamp', 'open', 'high', 'low', 'close', 'volume' are required.
# 'bid'/'ask' are optional but unlock true spread/liquidity metrics; if
# absent (as with most free OHLCV data), metrics.add_estimated_spread()
# derives a spread proxy from high/low prices instead (Corwin & Schultz,
# 2012), so you don't need bid/ask to get liquidity metrics.
#
# Default below matches "Dataset_NQ_1min_2022_2025.csv" — genuine 1-minute
# CME NQ futures bars, Dec 2022-Dec 2025, timestamps pre-labeled in
# America/New_York (verified against a real CPI-release volume spike: at
# the Jan 11, 2024 release, volume jumps from ~223 contracts at 8:29 ET to
# 5,890 at 8:31 ET). This is the primary dataset used by the pipeline.
#
# A second, coarser dataset is also included in data/raw/ for comparison:
# the "Nasdaq-CME-Future-NQ" hourly file (NQ_in_1_hour.csv, UTC timestamps,
# columns: datetime, symbol, open, high, low, close, volume). Swap
# COLUMN_MAP/SOURCE_TZ below to use it instead, and set TIMESTAMP_FORMAT to
# None (its timestamps are ISO-formatted and parse fine automatically).
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "timestamp": "timestamp ET",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
    "bid": None,                # this dataset has no bid/ask
    "ask": None,
}

# If your source timestamp has no timezone info, tell us what it is.
# This dataset's timestamps are already America/New_York (local exchange
# time), pre-verified against a known CPI-release volume spike.
SOURCE_TZ = "America/New_York"

# This dataset's timestamp format ("12/26/2022 18:01") needs an explicit
# format string for fast, unambiguous parsing across 1M+ rows.
TIMESTAMP_FORMAT = "%m/%d/%Y %H:%M"


def load_raw_csv(
    path: str | Path,
    column_map: dict = COLUMN_MAP,
    source_tz: str = SOURCE_TZ,
    timestamp_format: str | None = TIMESTAMP_FORMAT,
) -> pd.DataFrame:
    """
    Load and normalize a raw intraday futures CSV into the project's
    standard schema. Raises a clear error if required columns are missing,
    rather than silently producing garbage downstream.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"No file at {path}. Download your Kaggle dataset and update "
            f"the path passed to load_raw_csv()."
        )

    df = pd.read_csv(path)

    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [k for k in required if column_map.get(k) is None or column_map[k] not in df.columns]
    if missing:
        raise ValueError(
            f"COLUMN_MAP is missing or mismatched for: {missing}. "
            f"Available columns in {path.name}: {list(df.columns)}. "
            f"Edit COLUMN_MAP in data_loader.py to match your file."
        )

    out = pd.DataFrame()
    ts_col = column_map["timestamp"]
    out["timestamp"] = pd.to_datetime(df[ts_col], format=timestamp_format, errors="raise")

    if out["timestamp"].dt.tz is None:
        out["timestamp"] = out["timestamp"].dt.tz_localize(source_tz)
    out["timestamp"] = out["timestamp"].dt.tz_convert(ET)

    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(df[column_map[col]], errors="coerce")

    for opt in ["bid", "ask"]:
        col_name = column_map.get(opt)
        if col_name and col_name in df.columns:
            out[opt] = pd.to_numeric(df[col_name], errors="coerce")

    out = out.dropna(subset=["timestamp", "open", "high", "low", "close"])
    out = out.sort_values("timestamp").drop_duplicates(subset="timestamp")
    out = out.reset_index(drop=True)
    return out


def basic_quality_report(df: pd.DataFrame) -> dict:
    """Quick data-quality checks worth eyeballing before running the study."""
    gaps = df["timestamp"].diff().dropna()
    modal_gap = gaps.mode().iloc[0] if not gaps.empty else None
    return {
        "n_rows": len(df),
        "date_range": (df["timestamp"].min(), df["timestamp"].max()),
        "modal_bar_spacing": modal_gap,
        "n_large_gaps": int((gaps > (modal_gap * 3 if modal_gap else pd.Timedelta(0))).sum()) if modal_gap else None,
        "n_zero_or_negative_prices": int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()),
        "n_ohlc_violations": int(((df["high"] < df[["open", "close"]].max(axis=1)) |
                                   (df["low"] > df[["open", "close"]].min(axis=1))).sum()),
        "has_bid_ask": "bid" in df.columns and "ask" in df.columns,
    }


if __name__ == "__main__":
    print(
        "This module is a template loader. Edit COLUMN_MAP and SOURCE_TZ at "
        "the top of the file, then call load_raw_csv('data/raw/your_file.csv')."
    )
