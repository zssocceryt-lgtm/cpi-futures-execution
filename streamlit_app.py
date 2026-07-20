from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="NQ Futures CPI Execution Study",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parent
FIGURES_ROOT = PROJECT_ROOT / "results" / "figures"
TABLES_ROOT = PROJECT_ROOT / "results" / "tables"


@st.cache_data
def load_csv(relative_path: str) -> pd.DataFrame:
    """Load a repository CSV and cache it between Streamlit reruns."""
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Missing repository file: {relative_path}")
    return pd.read_csv(path)


def show_figure(relative_path: str, caption: str) -> None:
    """Display a figure committed to the repository."""
    path = PROJECT_ROOT / relative_path
    if path.exists():
        st.image(str(path), caption=caption, width="stretch")
    else:
        st.warning(f"Figure not found: `{relative_path}`")


def show_download_button(df: pd.DataFrame, filename: str, label: str) -> None:
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def format_cost_table(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "delay_minutes",
        "mean_slippage_bps",
        "mean_spread_cost_bps",
        "mean_total_cost_bps",
        "median_total_cost_bps",
        "p90_total_cost_bps",
        "n",
    ]
    formatted = df[columns].copy()
    formatted.columns = [
        "Delay (minutes)",
        "Mean slippage (bps)",
        "Mean spread cost (bps)",
        "Mean total cost (bps)",
        "Median total cost (bps)",
        "90th percentile cost (bps)",
        "Events",
    ]
    numeric_columns = [column for column in formatted.columns if "bps" in column]
    formatted[numeric_columns] = formatted[numeric_columns].round(2)
    return formatted


st.sidebar.title("NQ CPI Study")
st.sidebar.caption("NASDAQ-100 futures execution timing around U.S. CPI releases")

page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Summary",
        "Minute-Level Results",
        "Execution Timing",
        "Hourly Cross-Check",
        "Synthetic Validation",
        "Methodology & Data",
    ],
)

st.sidebar.divider()
st.sidebar.markdown(
    """
**Primary sample**  
34 CPI releases  
December 2022–December 2025  
1-minute CME NQ futures bars
"""
)


if page == "Executive Summary":
    st.title("NQ Futures Execution Timing Around CPI Releases")
    st.markdown(
        """
This market-microstructure event study examines how NASDAQ-100 futures behave
around U.S. Consumer Price Index releases and translates the results into a
trading-operations question:

> **How long should a trader wait after the CPI print before executing, and what does that delay cost?**
"""
    )

    aligned = load_csv(
        "results/tables/real_minute/execution_cost_by_delay_aligned.csv"
    )
    volatility = load_csv(
        "results/tables/real_minute/realized_volatility_by_minute.csv"
    )
    spread = load_csv("results/tables/real_minute/spread_by_minute.csv")

    peak_vol_row = volatility.loc[volatility["realized_vol_bps"].idxmax()]
    cost_1 = aligned.loc[aligned["delay_minutes"] == 1, "mean_total_cost_bps"].iloc[0]
    cost_2 = aligned.loc[aligned["delay_minutes"] == 2, "mean_total_cost_bps"].iloc[0]
    immediate_cost = aligned.loc[
        aligned["delay_minutes"] == 0, "mean_total_cost_bps"
    ].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CPI releases", "34")
    col2.metric(
        "Peak 1-minute volatility",
        f"{peak_vol_row['realized_vol_bps']:.1f} bps",
        f"at +{int(peak_vol_row['event_minute'])} minutes",
    )
    col3.metric("Immediate execution cost", f"{immediate_cost:.2f} bps")
    col4.metric("Cost at +2 minutes", f"{cost_2:.1f} bps")

    st.subheader("Headline finding")
    st.success(
        f"The execution-cost curve has a sharp knee between +1 and +2 minutes. "
        f"Mean reactive-trade cost rises from {cost_1:.2f} bps at +1 minute to "
        f"{cost_2:.2f} bps at +2 minutes. If execution cannot occur within the "
        "first 60–90 seconds, most of the sampled cost of not being first has "
        "already been incurred."
    )

    left, right = st.columns([1.35, 1])
    with left:
        show_figure(
            "results/figures/real_minute/04_execution_cost_curve_aligned.png",
            "Reactive/momentum execution cost by delay",
        )
    with right:
        st.markdown(
            """
### What the evidence suggests

- **Volatility spikes immediately.** It peaks near 51 bps at +2 minutes, compared with an approximately 1.8 bps pre-release baseline.
- **Waiting cost is nonlinear.** The major increase occurs between the first and second minute rather than accumulating gradually.
- **Spread normalization does not compensate for slippage.** Estimated spreads widen temporarily, but the change is modest relative to the price move.
- **Price impact does not cleanly reverse.** The initial reaction is only partially retained, but waiting for a full reversal is not supported by the sample.
"""
        )

    st.subheader("Study workflow")
    st.markdown(
        """
`Raw futures data` → `bar-close timestamp adjustment` → `CPI event-window alignment`
→ `volatility, spread, and impact metrics` → `execution-delay simulation`
→ `trading-operations interpretation`
"""
    )


elif page == "Minute-Level Results":
    st.title("Minute-Level Market Response")
    st.caption(
        "Primary analysis: 34 U.S. CPI releases using genuine 1-minute NQ futures data."
    )

    tab1, tab2, tab3 = st.tabs(
        ["Volatility", "Liquidity Proxy", "Price-Impact Decay"]
    )

    with tab1:
        st.subheader("Volatility profile")
        show_figure(
            "results/figures/real_minute/01_volatility_profile.png",
            "Cross-event realized volatility by minute relative to the CPI release",
        )
        st.markdown(
            """
Volatility rises from an approximately **1.8 bps pre-release baseline** to
roughly **17 bps one minute after the release**, then peaks near **51 bps at
+2 minutes**. It declines materially over the next 15–20 minutes, although it
remains above normal levels for part of the post-release window.
"""
        )
        vol_df = load_csv(
            "results/tables/real_minute/realized_volatility_by_minute.csv"
        )
        with st.expander("View volatility data"):
            st.dataframe(vol_df.round(4), width="stretch", hide_index=True)
            show_download_button(
                vol_df,
                "realized_volatility_by_minute.csv",
                "Download volatility table",
            )

    with tab2:
        st.subheader("Estimated spread profile")
        show_figure(
            "results/figures/real_minute/02_spread_profile.png",
            "Corwin–Schultz high-low spread estimate around CPI releases",
        )
        st.markdown(
            """
Because the real datasets do not contain quoted bid and ask prices, the study
uses the **Corwin–Schultz high-low estimator** as a liquidity proxy. Estimated
spreads rise to roughly 3–4 bps shortly after the release, compared with an
approximately 0.5–1.3 bps baseline, and move back toward normal within about
15 minutes.
"""
        )
        spread_df = load_csv("results/tables/real_minute/spread_by_minute.csv")
        with st.expander("View spread data"):
            st.dataframe(spread_df.round(4), width="stretch", hide_index=True)
            show_download_button(
                spread_df, "spread_by_minute.csv", "Download spread table"
            )

    with tab3:
        st.subheader("Price-impact decay")
        show_figure(
            "results/figures/real_minute/03_price_impact_decay.png",
            "Fraction of the eventual peak move present at each event minute",
        )
        st.markdown(
            """
The holding-ratio curve generally remains in the 0.10–0.20 range. The initial
move is therefore neither fully permanent nor followed by a clean, rapid
reversal. The later portion of the window also includes the 9:30 a.m. ET cash
equity open, which can add a separate volatility effect beginning 60 minutes
after an 8:30 a.m. CPI release.
"""
        )
        decay_df = load_csv(
            "results/tables/real_minute/price_impact_decay.csv"
        )
        with st.expander("View price-impact data"):
            st.dataframe(decay_df.round(4), width="stretch", hide_index=True)
            show_download_button(
                decay_df, "price_impact_decay.csv", "Download impact table"
            )


elif page == "Execution Timing":
    st.title("Execution-Delay Cost Simulation")
    st.markdown(
        """
The simulation compares execution at the release with execution after a chosen
delay. Total realized cost is decomposed into **price slippage** and the
estimated **spread paid at execution**.
"""
    )

    framing = st.radio(
        "Execution framing",
        [
            "Reactive / momentum trade",
            "Direction-blind hedge or rebalance",
        ],
        horizontal=True,
    )

    if framing == "Reactive / momentum trade":
        table_path = "results/tables/real_minute/execution_cost_by_delay_aligned.csv"
        curve_path = "results/figures/real_minute/04_execution_cost_curve_aligned.png"
        component_path = "results/figures/real_minute/05_cost_components_aligned.png"
        description = (
            "The trade direction is aligned with the post-release move—for example, "
            "selling NQ after a hotter-than-expected CPI print. Waiting creates "
            "one-way slippage as the trader chases the reaction."
        )
    else:
        table_path = "results/tables/real_minute/execution_cost_by_delay_agnostic.csv"
        curve_path = "results/figures/real_minute/06_execution_cost_curve_agnostic.png"
        component_path = "results/figures/real_minute/07_cost_components_agnostic.png"
        description = (
            "The trade must occur regardless of market direction, as with a scheduled "
            "hedge or rebalance. Price movement is treated symmetrically rather than "
            "as directional chasing cost."
        )

    st.info(description)
    cost_df = load_csv(table_path)

    selected_delay = st.select_slider(
        "Inspect an execution delay",
        options=cost_df["delay_minutes"].astype(int).tolist(),
        value=2,
        format_func=lambda value: "Immediate" if value == 0 else f"+{value} min",
    )
    selected = cost_df.loc[cost_df["delay_minutes"] == selected_delay].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Mean total cost", f"{selected['mean_total_cost_bps']:.2f} bps")
    col2.metric("Mean slippage", f"{selected['mean_slippage_bps']:.2f} bps")
    col3.metric("Mean spread cost", f"{selected['mean_spread_cost_bps']:.2f} bps")

    chart1, chart2 = st.tabs(["Total Cost Curve", "Cost Decomposition"])
    with chart1:
        show_figure(curve_path, f"{framing}: total execution cost by delay")
    with chart2:
        show_figure(component_path, f"{framing}: slippage and spread components")

    st.subheader("Execution-cost table")
    st.dataframe(format_cost_table(cost_df), width="stretch", hide_index=True)
    show_download_button(
        cost_df,
        Path(table_path).name,
        "Download execution-cost table",
    )

    if framing == "Reactive / momentum trade":
        st.warning(
            "Operational interpretation: the sample favors speed. Spread improvement "
            "after the print is too small to offset the slippage accumulated while "
            "waiting, particularly across the +1 to +2 minute interval."
        )


elif page == "Hourly Cross-Check":
    st.title("Hourly Resolution Cross-Check")
    st.markdown(
        """
The independent hourly dataset covers 21 CPI releases from January 2024 through
September 2025. It is directionally consistent with the primary study—volatility
rises and waiting is costly—but it cannot identify the sharp sub-hour timing
patterns visible in 1-minute data.
"""
    )

    figure_options = {
        "Volatility profile": "01_volatility_profile.png",
        "Spread profile": "02_spread_profile.png",
        "Price-impact decay": "03_price_impact_decay.png",
        "Reactive execution cost": "04_execution_cost_curve_aligned.png",
        "Reactive cost components": "05_cost_components_aligned.png",
        "Direction-blind execution cost": "06_execution_cost_curve_agnostic.png",
        "Direction-blind cost components": "07_cost_components_agnostic.png",
    }
    selected_figure = st.selectbox("Select an hourly result", figure_options.keys())
    show_figure(
        f"results/figures/real_hourly/{figure_options[selected_figure]}",
        f"Hourly cross-check: {selected_figure}",
    )

    aligned_hourly = load_csv(
        "results/tables/real_hourly/execution_cost_by_delay_aligned.csv"
    )
    with st.expander("View hourly reactive execution-cost data"):
        st.dataframe(
            format_cost_table(aligned_hourly), width="stretch", hide_index=True
        )


elif page == "Synthetic Validation":
    st.title("Synthetic-Data Methodology Validation")
    st.markdown(
        """
The calibrated synthetic generator provides a known data-generating process.
Running the same pipeline on designed data helps verify that event alignment,
metric construction, execution simulation, and visualization behave as intended
before interpreting the real-market results.
"""
    )

    figure_options = {
        "Volatility profile": "01_volatility_profile.png",
        "Spread profile": "02_spread_profile.png",
        "Price-impact decay": "03_price_impact_decay.png",
        "Reactive execution cost": "04_execution_cost_curve_aligned.png",
        "Reactive cost components": "05_cost_components_aligned.png",
        "Direction-blind execution cost": "06_execution_cost_curve_agnostic.png",
        "Direction-blind cost components": "07_cost_components_agnostic.png",
        "CPI surprise vs. reaction": "08_surprise_vs_reaction.png",
    }
    selected_figure = st.selectbox("Select a synthetic result", figure_options.keys())
    show_figure(
        f"results/figures/demo/{figure_options[selected_figure]}",
        f"Synthetic validation: {selected_figure}",
    )

    event_summary = load_csv("results/tables/demo/event_summary.csv")
    st.subheader("Synthetic event summary")
    st.dataframe(event_summary.round(3), width="stretch", hide_index=True)
    show_download_button(
        event_summary, "synthetic_event_summary.csv", "Download synthetic summary"
    )


elif page == "Methodology & Data":
    st.title("Methodology and Repository Structure")

    st.subheader("Data")
    st.markdown(
        """
| Dataset | Resolution | Coverage | CPI events | Role |
|---|---:|---|---:|---|
| `Dataset_NQ_1min_2022_2025.csv` | 1 minute | Dec. 2022–Dec. 2025 | 34 | Primary analysis |
| `NQ_in_1_hour.csv` | 1 hour | Jan. 2024–Oct. 2025 | 21 | Independent cross-check |
| 15- and 30-minute files | Coarser | 2025 only | Limited | Not used in final analysis |
| Short 1-minute file | 1 minute | Oct. 5–10, 2025 | 0 | Insufficient history |
"""
    )

    st.subheader("Core methods")
    st.markdown(
        """
1. **Timestamp normalization:** raw bar-open timestamps are shifted to bar-close timestamps.
2. **Event alignment:** each observation is indexed by minutes relative to the 8:30 a.m. ET CPI release.
3. **Volatility:** cross-event standard deviation of 1-minute log returns.
4. **Liquidity:** quoted spread when available; otherwise the Corwin–Schultz high-low spread estimator.
5. **Price impact:** fraction of the eventual peak move already present at each event minute.
6. **Execution simulation:** nearest available bar at each candidate delay, with cost split into slippage and spread.
"""
    )

    st.subheader("Repository layout")
    st.code(
        """nasdaq_cpi_execution_study/
├── streamlit_app.py
├── requirements.txt
├── setup.py
├── data/
│   └── raw/
├── scripts/
│   └── run_analysis.py
├── src/
│   └── cpi_study/
├── tests/
└── results/
    ├── figures/
    │   ├── real_minute/
    │   ├── real_hourly/
    │   └── demo/
    └── tables/
        ├── real_minute/
        ├── real_hourly/
        └── demo/
""",
        language="text",
    )

    st.subheader("Important limitation")
    st.warning(
        "The analysis is an event-study and execution-cost simulation, not a live "
        "trading system. Results are sample-dependent, use bar data rather than "
        "full depth-of-book data, and do not include commissions, queue position, "
        "market impact from the trader's own order, or production latency."
    )


st.divider()
st.caption(
    "NQ Futures CPI Execution Study · Real minute data, hourly cross-check, and synthetic validation"
)
