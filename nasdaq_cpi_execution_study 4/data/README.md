# data/

## Where the data come from

`raw/` is **not committed to this repository** (see repo-root `.gitignore`)
— the files are 2-70+ MB each, well past the "small, text-based" threshold
where committing raw data to git makes sense. To reproduce, download these
into `data/raw/` yourself:

| File | Source | Notes |
|---|---|---|
| `Dataset_NQ_1min_2022_2025.csv` | Kaggle: search "NQ 1 minute 2022 2025" futures dataset | **Primary dataset.** ~1.05M rows, Dec 2022–Dec 2025, genuine 1-minute CME NQ futures bars. Timestamps pre-labeled America/New_York. Row count sits suspiciously close to Excel's 1,048,576-row cap — the source file may have been truncated at the tail; doesn't affect any of the 34 CPI events analyzed here, but a fresher pull may extend further. |
| `NQ_in_1_hour.csv`, `NQ_in_30_minute.csv`, `NQ_in_15_minute.csv`, `NQ_in_1_minute.csv` | Kaggle: `youneseloiarm/nasdaq-cme-future-nq` (CC0-1.0) | Secondary dataset, used for the hourly cross-check. Timestamps in UTC. Only the hourly file has enough history to cover a useful number of CPI events (21) — the finer files in this bundle only span a few days in Oct 2025 with zero CPI releases in them, which is why they're present but unused. |

CPI release dates/times themselves are not a downloaded file — they're
hardcoded as real historical values in
`src/cpi_study/cpi_calendar.py`, sourced from the BLS release schedule
and cross-checked against ALFRED (Federal Reserve Bank of St. Louis). See
that module's docstring for the exact sources.

## What transforms what

`scripts/run_analysis.py` is the only thing that reads `raw/`. It does not
write anything back into `data/` — all derived output (tables, figures)
goes to `results/`, not `data/processed/`. Concretely, for each dataset:

1. `cpi_study.data_loader.load_raw_csv` reads a raw CSV and normalizes it
   to a common schema (`timestamp, open, high, low, close, volume[, bid,
   ask]`), converting timestamps to `America/New_York`.
2. Bar-open timestamps are shifted to bar-close time (see
   `run_analysis.run_real_mode`), so that "N minutes after release" labels
   reflect when a bar's information actually became available.
3. `cpi_study.event_windows.build_event_panel` slices the continuous series
   into ±window event-time panels around each real CPI release from
   `cpi_calendar.py`.
4. `cpi_study.metrics` and `cpi_study.execution_sim` compute everything
   that ends up in `results/`.

`data/processed/` exists as a landing spot for any future intermediate
artifact worth caching between pipeline steps (e.g. a pre-aligned event
panel, if re-computing it from the raw 1-minute file becomes slow enough to
be annoying). It's currently empty — the pipeline is fast enough
end-to-end that this hasn't been needed yet.

## Why (nothing under `cleaned/`)

This project doesn't have a `cleaned/` tier distinct from `processed/`:
the raw data is clean enough (no timestamp duplicates, no negative prices,
no OHLC violations — see the quality report `run_analysis.py` prints on
load) that "processed" and "cleaned" would be the same thing. If that
changes (e.g. a future dataset needs outlier removal before use), split
`processed/` into `processed/` (mechanical transforms) and `cleaned/`
(judgment calls, documented in this file) rather than silently combining
them.
