# NQ Futures Execution Timing Around CPI Releases

A market-microstructure event study of how NASDAQ (NQ) futures behave in the
minutes surrounding U.S. CPI releases, translated into a concrete
trading-operations question: **given that price discovery accelerates,
liquidity is temporarily impaired, and adverse selection risk is elevated
right after the print, how long should a trader wait before executing
and what does that delay actually cost?**

This project builds the full pipeline: 1) data cleaning 2) event-window
alignment 3) volatility/liquidity/adverse-selection metrics 4) an execution-
delay cost simulation 5) visualizations. It runs on **real CME NQ futures
data at genuine 1-minute resolution** across 34 real CPI releases, plus two
lower-resolution real datasets for comparison, plus a calibrated synthetic
mode for methodology validation.


## Why I built this project

I began trading in the stock market when I was around 14 or 15 years old. At that age, I understood basic ideas such as buying shares, following company news, and tracking price movements, but I had very little knowledge of macroeconomics. I did not yet know what the Consumer Price Index was or why an inflation report could move the entire market.

As I continued trading, I noticed that roughly once a month, volatility would suddenly increase in the morning. Since NQ futures are 
traded roughly 23 hours out the day and is very closely tied to the Nasdaq and the broader equity market, I expected markets to remain steady up until 30 minutes of market open. Seeing the prices could move sharply within minutes, even when there did not appear to be any major company-specific news, was very confusing to me at first. Initially, I did not understand what was causing these movements. But, after seeing the pattern repeatedly month after month, I began researching the economic calendar and learned about CPI releases and the effect that changing interest-rate expectations can have on financial markets.

I became particularly interested in NQ futures because technology and other growth-oriented companies are highly sensitive to changes in interest-rate expectations. A hotter or cooler than expected CPI report can quickly change how investors think about Federal Reserve policy, discount rates, and the value of future corporate earnings.

That experience led to the main question behind this project: once CPI is released and the market begins reacting, how quickly does price discovery occur, and how costly is it for a trader to wait before executing? I built this project to study a market pattern that I had first noticed as a young and inexperienced trader, but did not have the knowledge or technical skills to properly investigate at the time.

## Key concepts in plain English

Before explaining the data and results, it helps to define the main terms used throughout this project. This section is written for someone with little or no background in trading, economics, or futures markets. If main concepts are understood, feel free to skip past this section.

### What is the Nasdaq-100?

The Nasdaq-100 is an index that tracks 100 of the largest nonfinancial companies listed on the Nasdaq stock exchange. It includes many well-known technology and growth-oriented companies such as NVIDIA (NVAD), Apple (APPL), Microsoft (MSFT), Amazon (AMZN), etc. An index is not a company or a stock by itself. Instead, it acts like a scorecard that summarizes how a group of companies is performing. When many of the largest Nasdaq-100 companies rise, the index usually rises. When they fall, the index usually falls. Because the Nasdaq-100 contains many technology and growth companies, it can react strongly to changes in interest rates and expectations about the economy.

### What are NQ futures?

NQ is the ticker symbol for the E-mini Nasdaq-100 futures contract traded through CME Group. A futures contract is an agreement whose value is linked to the future level of an underlying asset or index. In this case, the contract follows the Nasdaq-100. A trader who expects the Nasdaq-100 to rise can buy an NQ futures contract. A trader who expects it to fall can sell one. Futures therefore allow traders to take a position on the direction of the Nasdaq-100 without buying shares in all 100 companies individually. NQ futures are closely related to the Nasdaq-100, but they are not exactly the same thing. The Nasdaq-100 is the index being tracked, while NQ is a tradable futures contract whose price is based on that index.

### Why can NQ move before the stock market opens?

The regular U.S. stock-market session begins at 9:30 AM Eastern Time. However, NQ futures trade electronically for nearly 23 hours per day from Sunday evening through Friday afternoon, with a daily maintenance break. This means NQ can react to news long before the regular stock market opens. For example, a company listed in the Nasdaq-100 may not begin regular trading until 9:30 AM, but NQ futures can already be moving at 8:30 AM in response to an economic announcement. This is one reason futures are useful for studying major announcements. They provide a nearly continuous view of how market expectations change.

### What is CPI?

CPI stands for the Consumer Price Index. The CPI measures how the prices paid by consumers change over time. The Bureau of Labor Statistics constructs it using a broad basket of goods and services, including categories such as:

* Food
* Housing
* Clothing
* Transportation
* Medical care
* Recreation
* Education
* Other everyday expenses

A simple way to understand CPI is to imagine filling the same shopping cart every month. If the cart becomes more expensive, consumer prices have increased. If the cost rises persistently across the economy, that is inflation. The CPI does not measure the exact spending experience of every household. It is an estimate of how prices are changing across a large representative basket of consumer purchases.

### Why does CPI matter to financial markets?

Investors care about CPI because inflation affects interest rates, borrowing costs, consumer spending, and the value of future cash flows.
The Federal Reserve is responsible for promoting stable prices and maximum employment. When inflation is too high, investors may expect the Federal Reserve to keep interest rates higher or raise them further. When inflation is cooling, investors may expect lower interest rates sooner. Those changing expectations can move financial markets immediately.

### What does “actual versus expected” mean?

Professional investors usually do not react only to whether inflation is high or low. They react to whether the reported number differs from what the market expected.

Suppose economists expect monthly CPI to rise by 0.2%:

* If CPI rises by 0.2%, the result matches expectations.
* If CPI rises by 0.4%, inflation is hotter than expected.
* If CPI rises by 0.0%, inflation is cooler than expected.

The difference between the reported value and the expected value is called the surprise. Markets often move most strongly when the surprise is large because traders must rapidly revise their assumptions.

### What is volatility?

Volatility measures how much prices move. A calm market with small price changes has low volatility. A market that moves sharply up and down has high volatility. Volatility does not tell us the direction of the market. A rapid rise and a rapid fall can both represent high volatility. In this project, realized volatility is calculated from the actual one-minute returns observed around CPI releases. It measures how dispersed those returns were across the events in the sample.

### What is a basis point (bps)?

A basis point, usually abbreviated as bps, is one-hundredth of one percentage point.

* 1 basis point = 0.01%
* 10 basis points = 0.10%
* 100 basis points = 1.00%

This project reports volatility, spread estimates, and execution costs in basis points because the relevant price changes are often much smaller than one full percentage point.

### What is the cash-market open?

The term cash market refers here to the regular market where the underlying Nasdaq-listed stocks trade. The regular opening occurs at 9:30 AM Eastern Time. Because CPI is usually released at 8:30 AM, the cash-market open appears at approximately +60 minutes on the project’s event-time graphs. That matters when interpreting the results. A second increase in volatility around +60 minutes may reflect the opening of the stock market rather than a delayed CPI reaction.

### What is the question this project is trying to answer?

The project asks a practical question:

After CPI is released, should a trader execute an NQ trade immediately, or wait for volatility and liquidity conditions to settle?

The answer is not obvious. Executing immediately may mean trading during the most chaotic part of the reaction. Waiting may provide a calmer market, but it may also mean missing much of the price adjustment.

The rest of the project uses historical NQ data to measure that tradeoff.



## Data used

I tested several NQ futures datasets before deciding which one should serve as the main source for the project. The most important requirement was having enough history and enough intraday detail to study what happens in the first few minutes after a CPI release.

| Dataset | Resolution | Coverage | CPI events | Role |
|---|---|---|---|---|
| `Dataset_NQ_1min_2022_2025.csv` | **1 min** | Dec 2022 – Dec 2025 | **34** | **primary analysis** |
| `NQ_in_1_hour.csv` | 1 hour | Jan 2024 – Oct 2025 | 21 | coarser cross-check |
| `NQ_in_30_minute.csv` / `NQ_in_15_minute.csv` | 30/15 min | 2025 only | 9 / 3 | too little history, unused |
| `NQ_in_1_minute.csv` | 1 min | Oct 5–10, 2025 only | 0 | too little history, unused |

The first (minute-resolution, ~3 years, ~1.05M rows) is the primary
dataset that was used. It is  dense and long enough to answer the sub-minute
execution-timing question the project set out to answer. **Its timestamps
are pre-labeled in America/New_York**, which was verified rather than
trusted blindly: at the Jan 11, 2024 release, volume jumps from 223
contracts at 8:29 ET to 5,890 at 8:31 ET. The CPI print lands exactly
where the label says it should.

As with the hourly file, raw timestamps are bar-*open* times; the pipeline
shifts to bar-close before building event windows so time-since-release
labels reflect when a bar's information actually became publicly available.

*(Note: the 1-minute file's row count lands really close to Excel's
1,048,576-row cap, suggesting the master file may have been truncated at
the tail when originally exported. This doesn't affect the analysis below
. All 34 CPI events fall well inside the surviving range with full
before/after windows, but a fresher copy of the source dataset may extend
further into 2025/2026.)*

## Results — 1-minute resolution (34 CPI events, Dec 2022–Dec 2025)

**Volatility spikes ~28x baseline within two minutes, then decays over
roughly 15-20 minutes.** Baseline 1-minute realized volatility (60-10
minutes pre-release) is ~1.8 bps. It jumps to ~17 bps one minute after the
release and peaks at **~51 bps two minutes after** — then decays to
~5-8 bps within 15-20 minutes. Mean absolute returns follow a similar pattern,
confirming that the increase reflects unusually large price movements across the event sample. The smaller rise around +60 minutes likely reflects the 9:30 AM equity-market open rather than the CPI release alone. This is the textbook macro-announcement
volatility signature (Andersen & Bollerslev, 1998), now observed directly
rather than assumed. (See `results/tables/real_minute/realized_volatility_by_minute.csv`
and `results/figures/real_minute/01_volatility_profile.png`.)

<p align="center">
  <img
    src="./nasdaq_cpi_execution_study%204/results/figures/real_minute/01_volatility_profile.png"
    alt="Realized volatility around CPI releases"
    width="800"
  />
</p>

<p align="center">
  <em>Realized volatility around 34 CPI releases at one-minute resolution.</em>
</p>


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

Cost is nearly flat from minute 3 onward. Almost all of the "cost of
waiting" in this sample is incurred in the **single minute between +1 and
+2**, not spread evenly across the post-release period. Practically: if you
can't act within the first ~60-90 seconds after the release, the data suggests you've already
paid most of the cost of not being first, and further delay adds
comparatively little on top. (`results/figures/real_minute/04_execution_cost_curve_aligned.png`,
`results/tables/real_minute/execution_cost_by_delay_aligned.csv`)

<p align="center">
  <img
    src="./nasdaq_cpi_execution_study%204/results/figures/real_minute/04_execution_cost_curve_aligned.png"
    alt="Execution cost by delay after CPI releases"
    width="800"
  />
</p>

<p align="center">
  <em>Estimated execution cost at different delays after CPI releases under the reactive-trade assumption. The largest increase occurs between one and two minutes after the release, after which the cost curve becomes relatively flat.</em>
</p>

This graph shows that the cost of waiting rises very quickly during the first few minutes after a CPI release. The blue line represents the average estimated execution cost across the 34 events, while the red dashed line shows the 90th-percentile cost, which captures the more extreme outcomes. The average cost is very small at the release and after a one-minute delay, but it jumps to roughly 37 basis points by minute two and remains near 40–46 basis points for the rest of the hour. This suggests that most of the average cost of waiting is incurred almost immediately. After the first few minutes, additional delay adds relatively little compared with the initial jump. The red line shows that the downside can be much larger during the most volatile CPI releases. By roughly two to three minutes after the announcement, the 90th-percentile cost rises to around 85–100 basis points and continues increasing gradually afterward. This means that although the average trader in the sample may face a cost of around 40 basis points, a trader caught in one of the largest reactions could face a move of approximately 1% or more before executing. The gap between the mean and the 90th percentile is also important. It shows that CPI reactions are not uniform: some releases generate moderate moves, while a smaller number create much more severe execution risk. Under the reactive or momentum assumption used here, the graph suggests that acting within the first minute matters far more than choosing between a five-, ten-, or thirty-minute delay.


**Liquidity impairment (Corwin-Schultz spread proxy) is real but modest
and short-lived**, roughly 3-4 bps in the few minutes after release vs.
~0.5-1.3 bps baseline, back near baseline within ~15 minutes. It is far too
small to offset the slippage cost above; this is why the execution
recommendation favors speed over waiting for spreads to normalize.
(`results/figures/real_minute/02_spread_profile.png`)

<p align="center">
  <img
    src="./nasdaq_cpi_execution_study%204/results/figures/real_minute/02_spread_profile.png"
    alt="Estimated bid-ask spread around CPI releases"
    width="800"
  />
</p>

<p align="center">
  <em>Estimated liquidity conditions around CPI releases using the Corwin–Schultz spread proxy. The implied spread widens immediately after the announcement, indicating temporarily worse liquidity, before moving back toward its pre-release level over the following minutes.</em>
</p>


**Price-impact decay is muted, not a clean overshoot-and-revert.** The
holding-ratio curve sits mostly in the 0.10-0.20 range through the full
2-hour window. The initial 2-minute move is neither fully retained nor
mostly reversed; it's a modest fraction of whatever the eventual larger
move (over the full window) turns out to be. Note this window also
contains the 9:30 AM ET cash-equity open (60 minutes after an 8:30 release),
which is itself a volatility event, meaning some of the elevated activity at
+60-90 minutes is plausibly equity-open effects layered on top of the CPI
reaction, not CPI alone. (`results/figures/real_minute/03_price_impact_decay.png`)

<p align="center">
  <img
    src="./nasdaq_cpi_execution_study%204/results/figures/real_minute/03_price_impact_decay.png"
    alt="Price-impact decay after CPI releases"
    width="800"
  />
</p>

<p align="center">
  <em>Price-impact persistence following CPI releases. The chart shows how much of the initial post-release movement remains over time, helping distinguish between temporary price reactions and information that becomes more permanently incorporated into NQ futures prices.</em>
</p>

## Results — hourly resolution (21 CPI events, Jan 2024–Sep 2025)

Kept as a cross-check using an independent dataset and independent
timestamp convention (UTC vs. this file's ET). Directionally consistent,
volatility spikes and stays elevated for hours, waiting is costly, but
necessarily blind to the sub-hour dynamics the minute-level data reveals
above. See `results/figures/real_hourly/` and `results/tables/real_hourly/`.
Full discussion in the code comments of `run_analysis.py`.

<p align="center">
  <img
    src="./nasdaq_cpi_execution_study%204/results/figures/real_hourly/01_volatility_profile.png"
    alt="Hourly NQ volatility profile around CPI releases"
    width="800"
  />
</p>

<p align="center">
  <em>Hourly NQ volatility around CPI releases. The graph provides a lower-frequency cross-check of the minute-level results by showing how volatility changes across the hours surrounding the announcement.</em>
</p>

Why this is a genuine independent cross-check, not just a second chart.

This hourly analysis does not use the same data as the primary 1-minute findings above. It comes from a separately sourced Kaggle dataset (youneseloiarm/nasdaq-cme-future-nq), compiled by a different provider, with its own raw timestamp convention (UTC, vs. the primary dataset's pre-labeled America/New_York), its own date range (Jan 2024–Sep 2025, vs. Dec 2022–Dec 2025), and its own resolution (hourly bars, vs. genuine 1-minute bars). Nothing here was derived by resampling the primary dataset. If it had been, agreement between the two would be close to tautological, since downsampling the same series into coarser bars is guaranteed to preserve its broad shape. Instead, this is two independently compiled records of the same underlying market, checked against each other.

That independence is what makes the agreement meaningful:

Two different timezone conventions, verified two different ways, agreeing on the same event. The primary dataset's ET label and this dataset's UTC label were each validated separately against the same real CPI release (Jan 11, 2024) using the same method. Checking that trading volume spikes at exactly the minute/hour the 8:30 AM ET print should land. Both pass, independently, which rules out a shared timestamp bug being the source of the pattern in both.

A resolution-robustness check. If the volatility spike-and-decay pattern were an artifact of how one specific vendor constructs 1-minute bars (a bad tick filter, a rounding convention, a synchronization issue), coarsening the data to hourly bars from an entirely different source should make that artifact disappear or look different. It doesn't! The qualitative shape (a sharp jump at the release, staying elevated afterward, gradual decay) survives the change in both data lineage and granularity.

Partial overlap in underlying events. The hourly dataset's date range sits entirely inside the minute dataset's range, so roughly 21 of the same real CPI releases are represented in both; effectively two different measuring instruments pointed at the same set of real-world events.

What this check does and doesn't establish. It supports the existence and direction of the effect. CPI releases produce a real, sustained volatility and execution-cost impact that isn't specific to one dataset's construction. It does not validate the precise magnitudes in the minute-level results: hourly bars mechanically produce different numbers than minute bars (coarser bars average over more post-release drift, can misattribute the following equity-market open, etc.), so the two datasets' exact bps figures aren't meant to match. Only the underlying pattern is. Treat this figure as confirmation that the phenomenon is real, and the 1-minute analysis as the source of any specific number you'd actually act on.


## Results — synthetic demo data (methodology validation)

`results/figures/demo/` and `results/tables/demo/` contain the same
pipeline run on a calibrated synthetic generator (`src/cpi_study/simulate_data.py`),
included so the methodology can be checked against a known, designed-in
ground truth independent of any one dataset's quirks.

Purpose: proving the pipeline is correct, independent of whether any real dataset is correct.

This demo's results come from simulate_data.py, a synthetic NQ futures generator — not real market data, and not meant to be read as one. Its job is different from the two real-data analyses above: it exists to answer "does this code correctly implement event-study methodology?" separately from "is this real dataset telling us something true?" Those are two different questions, and conflating them makes debugging much harder.

<p align="center">
  <img
    src="./nasdaq_cpi_execution_study%204/results/figures/demo/01_volatility_profile.png"
    alt="Simulated Data of realized volatility around CPI releases"
    width="800"
  />
</p>

<p align="center">
  <em>Simulated Data of realized volatility around CPI releases.</em>
</p>

How it works. The generator builds minute-bar price paths around each real CPI release date, with a volatility spike, spread-widening, and order-flow-imbalance shape designed in by construction, calibrated to stylized facts documented in the macro-announcement literature (Andersen & Bollerslev, 1998; Balduzzi, Elton & Green, 2001; Lucca & Moench, 2015) rather than fit to any actual dataset. Critically, the answer is known in advance. We set the spike size and decay half-life ourselves, so running the full pipeline (event alignment → volatility/liquidity metrics → execution-cost simulation → figures) on this data and checking that it recovers the pattern we designed in is a genuine end-to-end correctness check, the same way a unit test checks known input against known output.

When the hourly dataset returned an empty execution-cost table, testing against the synthetic ground truth first is what made it obvious the bug was an indexing assumption (event_minute == 0 not existing), not a problem with the hourly data itself. When the 1-minute real data showed the price-impact "holding ratio" rising instead of decaying (the opposite of the textbook overshoot-and-revert pattern) having already confirmed the pipeline reproduces textbook decay correctly on synthetic data gave confidence that this was a genuine finding about markets, not a computation error.

What it adds beyond validation. The synthetic generator is also the only place order_flow_persistence (post-release autocorrelation of signed order flow) can be demonstrated at all. Neither real dataset carries trade-direction information, so this metric exists in the codebase but is otherwise silent. Including it here shows the full capability of the pipeline rather than only the subset that both real datasets happen to support. It also means the entire project runs immediately after cloning, with zero data download required, which matters for anyone evaluating the code itself rather than the market conclusions.

## Methodology

### Part 1: Getting the Timing Right
Why we need to know exactly when releases happened

You can't study "what happens around CPI releases" without knowing precisely when each one happened. So the first building block is a calendar of every real CPI release date and time, going back to 2019 — pulled from the Bureau of Labor Statistics' own published schedule and cross-checked against a Federal Reserve archive (ALFRED), not estimated or guessed. Every release happens at 8:30 AM Eastern Time, without exception.

Verifying the data actually lines up with that calendar

Here's a subtlety that's easy to get wrong: price data files often don't say what timezone their timestamps are in, or they lie about it. If you get this wrong, your entire analysis is looking at the wrong minute, almost like trying to study a solar eclipse by looking at the wrong day.

So instead of trusting a label, we proved the timezone was correct using a simple, undeniable check: on a real CPI release day, trading volume should spike enormously in the exact minute the report drops, because that's when everyone reacts at once. We looked for that spike. On January 11, 2024, volume jumped from about 223 contracts traded in the minute before the release to nearly 5,900 contracts in the minute after. A roughly 26x jump, landing exactly where 8:30 AM Eastern Time should be. That's not a coincidence; it's the market itself confirming the clock is right.

A subtler timing trap: when does a "bar" of data actually happen?

Price data doesn't come as a continuous stream. It comes in chunks called bars (e.g., "everything that happened between 1:00 and 2:00"), each bar labeled with a single timestamp. But which timestamp: the start of that hour, or the end?

This matters more than it sounds. Imagine an hourly bar that starts at 1:00 PM. If the CPI release happens at 1:30 PM, that bar actually contains the release in its second half, but if you only look at the label ("1:00"), you'd wrongly think that bar was entirely before the news came out. To fix this, every bar's timestamp was shifted forward to represent when the bar closed (i.e., when its information was actually fully known), not when it opened. This ensures "5 minutes after the release" really means 5 minutes after, not sometimes before.

### Part 2: Turning Many Different Days Into One Shared Picture

CPI releases happen on totally different calendar days, months apart. You can't just average "January 11th" with "March 14th" directly; they're different days with different starting prices. The standard technique for solving this (used broadly in finance research, going back to a well-known 1997 paper by MacKinlay) is called an event study.

The idea: instead of measuring time as "January 11th, 1:32 PM," we re-measure time relative to the release itself, "2 minutes after the release." Do this for every single CPI event, and suddenly they're all speaking the same clock. You can stack 34 completely different days on top of each other and ask, "on average, what does minute +2 look like across all of them?" That's the entire trick that makes this kind of analysis possible.

### Part 3: What We Actually Measure

Once every event is aligned on the same clock, we compute four things at each point in that shared timeline:

#### 1. Realized volatility — "how much is the price shaking?"

This is simply: across all 34 events, how much did the price typically move in each 1-minute window, at each point in event-time? Before the release, prices barely move minute to minute (this is the calm "baseline"). Right after the release, they swing wildly. We measure this using the standard statistical deviation of minute-to-minute price changes; a bigger number means bigger, more unpredictable swings.

What we found: volatility jumps to roughly 28 times its normal level within 2 minutes of the release, then gradually calms down over the following 15–20 minutes.

#### 2. Liquidity / spread — "how expensive is it to trade right now?"

Every tradable market has a bid-ask spread: the gap between the highest price a buyer is currently willing to pay and the lowest price a seller is currently willing to accept. That gap is effectively a toll. The cost of trading immediately instead of waiting for a better match. When a market gets nervous (like right after unexpected news), that gap tends to widen because nobody wants to commit to a price when they're not sure what the "right" price even is anymore.

The problem: our datasets don't actually record that gap directly. We only have the four standard price points per bar (open, high, low, close), not live bid/ask quotes. So we use a published technique called the Corwin-Schultz estimator (2012), which reverse-engineers an estimate of the spread just from how wide the high-low range is across two consecutive bars. The intuition: pure random noise makes a price wiggle a little within a bar; a widening bid-ask gap makes it wiggle more than pure noise would explain, and that extra wiggle is mathematically detectable and separable from the noise. It's not as good as a real recorded spread, but it's a legitimate, peer-reviewed way to estimate one when you don't have quote data, which is most free/inexpensive market data.

What we found: spreads widen modestly (roughly 3–4x) for a few minutes after the release, then fade back within about 15 minutes — real, but far too small on its own to explain the execution costs discussed below.

#### 3. Price impact decay — "does the initial move stick, or bounce back?"

When the price jumps right after a release, there are two very different things that could be happening:

Overshoot: traders overreact in the heat of the moment, and the price partially bounces back once things calm down.
Genuine repricing: the market correctly and permanently re-prices based on real new information, and the move holds.

We check which one is happening by tracking, at every point after the release, what fraction of the eventual biggest move is already "locked in." If that fraction starts high and shrinks over time, that's overshoot-and-revert. If it stays low and grows, that means the real move built up gradually rather than snapping into place immediately.

What we found: in the data, it's the second pattern: the fraction starts near zero and rises over the following couple of hours. The market doesn't overreact and settle down; it keeps drifting in the same direction for a while. This is actually a well-documented real phenomenon called post-announcement drift.

#### 4. Order flow persistence — "does buying/selling pressure keep going the same direction?"

This measures whether the direction of trading (more buyers vs. more sellers) right after a release tends to keep pointing the same way for several minutes afterward, which would be a sign that informed traders are dominating the order flow for a while (rather than it being scattered noise). This one is only available in the synthetic demo data; real trade-by-trade buy/sell direction isn't in either real dataset we have, so this metric exists in the code to show the full capability of the pipeline, but currently has nothing real to measure it against.

### Part 4: Turning All of This Into a Trading Decision

This is the actual "so what" of the whole project. The execution cost simulation.

#### Step 1: pick a reference "arrival" moment

For each event, we find the earliest bar at or after the release — that's our reference point, as if you're standing there deciding whether to trade right now or wait.

#### Step 2: for each candidate waiting time, find what actually happened

We check a list of possible delays (like waiting 1 minute, 2 minutes, 5 minutes, 30 minutes, etc.) and, for each one, find the price at that point in time.

#### Step 3: add up two separate costs
Cost of waiting (slippage): how much the price already moved before you got there. If you're trying to sell right as the price is falling, every minute you wait, you're chasing a lower price.
Cost of trading right now (spread): half the bid-ask spread at that moment (using the real spread if we have it, or the Corwin-Schultz estimate otherwise) — the toll for demanding immediacy.

Add these two together and you get an estimate of the total real-world cost, in basis points (hundredths of a percent), of executing at that particular delay.

#### Step 4: two different versions of "cost," because it depends on what you're trying to do
If you're chasing the move (e.g., "CPI came in hot, I want to sell"): every minute you wait, the market runs further away from you in the direction you're trying to trade. This is the worst-case scenario for patience. If you have to trade regardless of direction (e.g., you're rebalancing a portfolio or hedging on a schedule): the cost is just how much the price randomly moved, with no assumption about which way is "bad" for you.

We computed both, because the honest answer to "should I wait?" depends entirely on which kind of trader you are.

#### Step 5: average it all together, honestly

We do this for every one of the 34 real events, then look at the average cost at each delay, the median (less sensitive to one crazy outlier event), and the 90th percentile: a way of asking "how bad does this get on a rough day, not just on average?"

What we found: on real minute-level data, cost is low (under 3 basis points) if you act within the first minute, but jumps sharply, to over 35 basis points, if you wait even 2 minutes. After that, costs keep climbing only slowly. In plain terms: almost the entire cost of hesitating happens in that single minute between +1 and +2. If you miss that window, you've already paid most of the price of not being first.

### Part 5: Why There Are Three Separate Versions of This Analysis

We didn't run this once. We ran it three times, on purpose, because each version answers a different question:

The 1-minute real data (34 events, 2022–2025) is the main result. Genuine minute-by-minute trading data, giving us the fine-grained answer to "how many minutes matter."

The hourly real data (21 events, 2024–2025) is a completely independently sourced dataset (different vendor, different timezone label, different date range) used purely as a sanity check. If the same broad pattern (volatility spike, cost of waiting) showed up in data that has nothing to do with the first dataset, that's strong evidence the pattern is real and not some quirk of one specific data provider. It agreed.

The synthetic demo data contains completely made-up prices, generated by us, with a known pattern built in on purpose. This is a way of testing whether our code correctly reproduces a known, designed answer, completely separate from whether any real dataset is "correct." This is exactly how we caught a real bug: a testing tool (pytest) run against this synthetic ground truth caught a case where a common data-analysis library (pandas) was silently producing wrong numbers under one specific condition. We would have never would have noticed this by staring at real-world results, since we wouldn't know what the "right" answer was supposed to look like.

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

To sturtcure this project, I followed the project-layout convention described in
[goodresearch.dev's "Set up your project"](https://goodresearch.dev/setup). 

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
DataFrame instead of concatenated properly). It
happened not to affect the multi-event production runs above, but it would cause a problem for anyone re-running this on a single CPI event. Fixed
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
