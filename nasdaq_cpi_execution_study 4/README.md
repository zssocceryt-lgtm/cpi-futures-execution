# NQ Futures Execution Timing Around CPI Releases

A market-microstructure event study of how NASDAQ (NQ) futures behave in the
minutes surrounding U.S. CPI releases, translated into a concrete
trading-operations question: **given that price discovery accelerates,
liquidity is temporarily impaired, and adverse selection risk is elevated
right after the print, how long should a trader wait before executing —
and what does that delay actually cost?**

This project builds the full pipeline: data cleaning → event-window
alignment → volatility/liquidity/adverse-selection metrics → an execution-
delay cost simulation → visualizations. It runs on **real CME NQ futures
data at genuine 1-minute resolution** across 34 real CPI releases, plus two
lower-resolution real datasets for comparison, plus a calibrated synthetic
mode for methodology validation.

## Data used

| Dataset | Resolution | Coverage | CPI events | Role |
|---|---|---|---|---|
| `Dataset_NQ_1min_2022_2025.csv` | **1 min** | Dec 2022 – Dec 2025 | **34** | **primary analysis** |
| `NQ_in_1_hour.csv` | 1 hour | Jan 2024 – Oct 2025 | 21 | coarser cross-check |
| `NQ_in_30_minute.csv` / `NQ_in_15_minute.csv` | 30/15 min | 2025 only | 9 / 3 | too little history, unused |
| `NQ_in_1_minute.csv` | 1 min | Oct 5–10, 2025 only | 0 | too little history, unused |

The first (minute-resolution, ~3 years, ~1.05M rows) is now the primary
dataset — it's the one dense and long enough to answer the sub-minute
execution-timing question the project set out to answer. **Its timestamps
are pre-labeled in America/New_York**, which was verified rather than
trusted blindly: at the Jan 11, 2024 release, volume jumps from 223
contracts at 8:29 ET to 5,890 at 8:31 ET — the CPI print landing exactly
where the label says it should.

As with the hourly file, raw timestamps are bar-*open* times; the pipeline
shifts to bar-close before building event windows so time-since-release
labels reflect when a bar's information actually became available.

*(Note: the 1-minute file's row count lands suspiciously close to Excel's
1,048,576-row cap, suggesting the master file may have been truncated at
the tail when originally exported. This doesn't affect the analysis below
— all 34 CPI events fall well inside the surviving range with full
before/after windows — but a fresher copy of the source dataset may extend
further into 2025/2026.)*

## Results — 1-minute resolution (34 CPI events, Dec 2022–Dec 2025)

**Volatility spikes ~28x baseline within two minutes, then decays over
roughly 15-20 minutes.** Baseline 1-minute realized volatility (60-10
minutes pre-release) is ~1.8 bps. It jumps to ~17 bps one minute after the
release and peaks at **~51 bps two minutes after** — then decays to
~5-8 bps within 15-20 minutes. This is the textbook macro-announcement
volatility signature (Andersen & Bollerslev, 1998), now observed directly
rather than assumed. (See `results/tables/real_minute/realized_volatility_by_minute.csv`
and `results/figures/real_minute/01_volatility_profile.png`.)

**The execution-cost curve has a sharp knee at minute 2, not a smooth
ramp.** This is the headline trading-ops finding:

| Delay after release | Mean execution cost (reactive/momentum trade) |
|---|---|
| Immediate (arrival bar) | 0.66 bps |
| +1 minute | **2.85 bps** |
| +2 minutes | **36.7 bps** |
| +3 minutes | 38.5 bps |
| +5 minutes | 36.1 bps |
| +10 minutes | 42.9 bps |
| +15 minutes | 43.3 bps |
| +30 minutes | 45.0 bps |
| +60 minutes | 46.1 bps |

Cost is nearly flat from minute 3 onward — almost all of the "cost of
waiting" in this sample is incurred in the **single minute between +1 and
+2**, not spread evenly across the post-release period. Practically: if you
can't act within the first ~60-90 seconds, the data suggests you've already
paid most of the cost of not being first, and further delay adds
comparatively little on top. (`results/figures/real_minute/04_execution_cost_curve_aligned.png`,
`results/tables/real_minute/execution_cost_by_delay_aligned.csv`)

**Liquidity impairment (Corwin-Schultz spread proxy) is real but modest
and short-lived** — roughly 3-4 bps in the few minutes after release vs.
~0.5-1.3 bps baseline, back near baseline within ~15 minutes. It is far too
small to offset the slippage cost above; this is why the execution
recommendation favors speed over waiting for spreads to normalize.
(`results/figures/real_minute/02_spread_profile.png`)

**Price-impact decay is muted, not a clean overshoot-and-revert.** The
holding-ratio curve sits mostly in the 0.10-0.20 range through the full
2-hour window — the initial 2-minute move is neither fully retained nor
mostly reversed; it's a modest fraction of whatever the eventual larger
move (over the full window) turns out to be. Note this window also
contains the 9:30 AM ET cash-equity open (60 minutes after an 8:30 release),
which is itself a volatility event — some of the elevated activity at
+60-90 minutes is plausibly equity-open effects layered on top of the CPI
reaction, not CPI alone. (`results/figures/real_minute/03_price_impact_decay.png`)

## Results — hourly resolution (21 CPI events, Jan 2024–Sep 2025)

Kept as a cross-check using an independent dataset and independent
timestamp convention (UTC vs. this file's ET). Directionally consistent —
volatility spikes and stays elevated for hours, waiting is costly — but
necessarily blind to the sub-hour dynamics the minute-level data reveals
above. See `results/figures/real_hourly/` and `results/tables/real_hourly/`.
Full discussion in the code comments of `run_analysis.py`.

## Results — synthetic demo data (methodology validation)

`results/figures/demo/` and `results/tables/demo/` contain the same
pipeline run on a calibrated synthetic generator (`src/cpi_study/simulate_data.py`),
included so the methodology can be checked against a known, designed-in
ground truth independent of any one dataset's quirks.

## Methodology

**Event window construction.** Every CPI release date/time in
`src/cpi_study/cpi_calendar.py` is a real historical BLS publication date (8:30 AM
ET), sourced from the BLS release schedule and cross-checked against
ALFRED (Federal Reserve Bank of St. Louis archival release-date database).
Price data is sliced into a window around each release and re-indexed to
"event time" (minutes relative to the print, shifted to bar-close), the
standard event-study approach (MacKinlay, 1997) adapted to high-frequency,
single-day macro announcements.

**Metrics.**
- *Realized volatility by event-minute*: cross-event stdev of 1-minute log
  returns, bucketed by time-since-release.
- *Liquidity proxy*: quoted spread in bps if bid/ask is available;
  otherwise the Corwin & Schultz (2012) high-low spread estimator, which
  derives an implied bid-ask spread from consecutive bars' high/low prices
  alone. Neither real dataset here has bid/ask, so this estimator is doing
  real work, not just filling a gap.
- *Price impact decay*: for each event, what fraction of the eventual peak
  move is already present at each subsequent minute.
- *Order-flow persistence*: post-release autocorrelation of signed order
  flow imbalance (only available in the synthetic demo data, which
  generates this signal directly; real trade-direction data would be
  needed to compute this on actual market data).

**Execution-cost simulation.** For a set of candidate delays, the pipeline
finds the *nearest available bar* to each target delay (matters for coarse
data, irrelevant here since 1-minute data has an exact bar for every
target) and decomposes realized cost into (a) slippage from the market
having moved before you traded and (b) the spread paid at that moment. Two
framings are computed — reactive/momentum and direction-blind — because
the "should I wait" answer depends on whether you already know which way
you want to trade.

## Project structure

This follows the project-layout convention described in
[goodresearch.dev's "Set up your project"](https://goodresearch.dev/setup)
and [Eric Ma's "How to organize your Python data science
project"](https://gist.github.com/ericmjl/27e50331f24db3e8f957d1fe7bbbe510)
— a pip-installable `src/` package (no `sys.path` hacks), a thin
`scripts/` entrypoint that imports from it, real tests, and a `data/`
folder that documents its own provenance rather than assuming you'll
remember where the CSVs came from.

```
nasdaq_cpi_execution_study/
├── src/
│   └── cpi_study/                # pip-installable package (`pip install -e .`)
│       ├── __init__.py           # exposes the pipeline building blocks
│       ├── config.py             # shared paths & constants (PROJECT_ROOT, tick size, ...)
│       ├── cpi_calendar.py       # real BLS CPI release dates/times, 2019-2026
│       ├── simulate_data.py      # calibrated synthetic NQ futures generator (demo/validation)
│       ├── data_loader.py        # flexible loader, pre-configured for the 1-min Kaggle dataset
│       ├── event_windows.py      # event-time alignment (bar-close shifted)
│       ├── metrics.py            # volatility, liquidity (incl. Corwin-Schultz), price-impact, order-flow
│       ├── execution_sim.py      # execution-delay cost simulation (nearest-bar matching)
│       └── visualization.py      # all plotting functions
├── scripts/
│   └── run_analysis.py           # end-to-end pipeline entrypoint (imports cpi_study)
├── tests/                        # bare-minimum tests per module, not exhaustive coverage
│   ├── test_cpi_calendar.py
│   ├── test_event_windows.py
│   ├── test_metrics.py
│   └── test_execution_sim.py
├── data/
│   ├── README.md                 # provenance: where each file comes from, what transforms what
│   ├── raw/                      # NOT committed (see .gitignore) — download per data/README.md
│   └── processed/                # empty; landing spot for future cached intermediate artifacts
├── results/                      # committed — small, browsable without rerunning anything
│   ├── figures/{real_minute,real_hourly,demo}/
│   └── tables/{real_minute,real_hourly,demo}/
├── setup.py                      # src-layout package install
├── environment.yml               # conda spec
├── requirements.txt              # pip spec
├── .gitignore
└── README.md
```

**Why a package instead of a script that reaches into `src/` via
`sys.path`:** it's what let `scripts/run_analysis.py` drop its path hack
entirely — `pip install -e .` once, then `from cpi_study.metrics import
...` works from anywhere, in tests, in a notebook, or in a second script,
without re-deriving the repo root each time. It also means `tests/` can
import the package the same way real code does, instead of testing a
different import path than the one users actually hit.

## Running it

```bash
# Option A: conda
conda env create --file environment.yml
conda activate cpi_study

# Option B: pip / venv
pip install -r requirements.txt

# Either way, install the local package in editable mode so `cpi_study`
# is importable and scripts/run_analysis.py doesn't need path hacks:
pip install -e .

# Sanity-check the package + a few key behaviors (fast, no data required):
pytest tests/ -v

# Primary analysis — 1-minute resolution, the results shown above
python scripts/run_analysis.py --mode real \
    --csv data/raw/Dataset_NQ_1min_2022_2025.csv \
    --start 2022-12-26 --end 2025-12-11 \
    --window-minutes 120 --delays 0 1 2 3 5 10 15 30 60 \
    --run-name real_minute

# Hourly cross-check (different dataset, different timezone convention)
python scripts/run_analysis.py --mode real --csv data/raw/NQ_in_1_hour.csv \
    --start 2024-01-01 --end 2025-09-11 \
    --window-minutes 240 --delays 0 60 120 180 \
    --run-name real_hourly \
    --timestamp-col datetime --source-tz UTC --timestamp-format none

# Synthetic demo mode — methodology validation, no data required
python scripts/run_analysis.py --mode simulate --start 2023-01-01 --end 2025-12-31
```

The two real-data commands need the corresponding CSVs in `data/raw/`
first — see `data/README.md` for where to get them (they're not committed
to the repo; see [Data note](#data-note-and-known-limitations)).

To point the loader at a different NQ futures CSV, edit `COLUMN_MAP`,
`SOURCE_TZ`, and `TIMESTAMP_FORMAT` at the top of
`src/cpi_study/data_loader.py`, or pass `--timestamp-col`/`--source-tz`/
`--timestamp-format` on the command line — the rest of the pipeline is
schema-agnostic either way. `--run-name` controls which
`results/figures/<name>/` and `results/tables/<name>/` subfolder a run
writes to, so different datasets don't overwrite each other.

## Engineering notes

`tests/` is deliberately small — one focused test file per module, each
covering the one thing in that module that isn't "obviously correct by
construction" (per the bare-minimum-testing philosophy in the [gist
linked above](#project-structure)). One of them earned its keep
immediately: `test_event_windows.py` caught a real bug where pandas 3.0.2's
`groupby(...).apply()` silently corrupts its result on a *single*-group
DataFrame (a per-row Series comes back reshaped into a malformed
DataFrame instead of concatenated properly — no exception raised). It
happened not to affect the multi-event production runs above, but it was
a live landmine for anyone re-running this on a single CPI event. Fixed
with a vectorized `groupby` + `merge` approach that sidesteps the pandas
edge case entirely (see the docstring in
`src/cpi_study/event_windows.py::add_event_returns`), and it's now a
permanent regression test.

## Data note and known limitations

- **The 9:30 AM ET equity open falls inside the analysis window** for an
  8:30 AM release (60 minutes later), and is itself a volatility event.
  Some of what shows up as "still elevated at +60-90 minutes" in the
  minute-level results is plausibly a mix of CPI drift and ordinary equity-
  open activity, not CPI alone. Isolating the two would need a control
  sample of non-CPI days at the same times, which this project doesn't yet
  build.
- **No bid/ask in either real dataset.** The Corwin-Schultz estimator is a
  published, real method, but was originally designed for daily bars; the
  spread profile should be read as a genuine but imprecise signal, not a
  substitute for real quoted spreads.
- **The execution simulation is a simplified two-component cost model**
  (waiting-slippage + half-spread), not a full limit-order-book or
  market-impact model.
- **The 1-minute file's tail may be truncated** (see note above) —
  functionally irrelevant to the 34 events analyzed, but worth knowing if
  you extend the analysis toward the most recent data.
- **Order-flow persistence** is only available in synthetic mode; neither
  real dataset carries trade-direction information.
- This is a research/portfolio project, not investment advice, and none of
  its output should be used to size or time real trades without independent
  validation.

## References

- Andersen, T. & Bollerslev, T. (1998). *Deseasonalizing the Volatility
  Persistence Process*.
- Balduzzi, P., Elton, E. & Green, T. C. (2001). *Economic News and Bond
  Prices*. Journal of Financial and Quantitative Analysis.
- Corwin, S. & Schultz, P. (2012). *A Simple Way to Estimate Bid-Ask
  Spreads from Daily High and Low Prices*. Journal of Finance, 67(2).
- Glosten, L. & Milgrom, P. (1985). *Bid, Ask and Transaction Prices in a
  Specialist Market with Heterogeneously Informed Traders*.
- Kyle, A. (1985). *Continuous Auctions and Insider Trading*. Econometrica.
- Lucca, D. & Moench, E. (2015). *The Pre-FOMC Announcement Drift*. Journal
  of Finance.
- MacKinlay, A. C. (1997). *Event Studies in Economics and Finance*.
  Journal of Economic Literature.
- U.S. Bureau of Labor Statistics, CPI Release Schedule —
  https://www.bls.gov/schedule/news_release/cpi.htm
- ALFRED, Federal Reserve Bank of St. Louis, CPI release dates —
  https://alfred.stlouisfed.org/release?rid=10
- Kaggle dataset: *Nasdaq-CME-Future-NQ* (youneseloiarm), CC0-1.0 —
  https://www.kaggle.com/datasets/youneseloiarm/nasdaq-cme-future-nq
