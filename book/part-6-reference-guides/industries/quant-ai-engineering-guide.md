# Quant AI Engineering: A Knowledge Guide

*The engineer's companion to chapter 44.13 and to the [systematic trading and ML guide](systematic-trading-and-ml-guide.md). That guide explains what systematic trading is and how research is done; this one explains how the systems are built, with the mathematics worked by hand and the mechanisms in runnable standard-library Python. Educational only; nothing here is investment advice. Dated October 2026.*

Every Python block in this guide runs on its own with Python 3.11 or newer and no third-party packages, and states its results with `assert`; `python3 tools/run_chapter_examples.py book/part-6-reference-guides/industries/quant-ai-engineering-guide.md` executes them all.

---

## 1. Orientation

**What the job is.** A quant AI engineer builds the machinery between data and trading decisions: the data platform that remembers what was known when, the research environment where hypotheses are tested without fooling their author, the backtester that charges realistic costs, the models that extract small, decaying signals from noisy data, the execution and risk systems that turn a forecast into positions without blowing up, the monitoring that notices when an edge has died, and, since 2025, the language-model and agent tooling that reads text and writes research code under guardrails. The role owns three failures: a backtest that lies, a model that saw the future, and a system that is right too late. Every section of this guide prevents one of the three.

**How to read it.** Sections 2 to 9 are the mechanics, each with code you can run and modify: order books, return mathematics, point-in-time data, labels and validation, features, backtesting, costs and execution, portfolio and risk. Section 10 is the AI layer: language models over financial text, research agents, and the leakage controls both need. Section 11 is model-risk and compliance engineering, which is where a quant AI engineer's work is audited. Section 12 is the platform. Sections 13 and 14 are the interview bank and a study plan. Chapter 44.13 has the role map and the trading-knowledge requirements table; the systematic-trading guide has the strategy families, data types and research workflow in prose.

**Three numbers to carry.** A liquid large-cap US equity trades at a spread of a few basis points (a basis point is one hundredth of one percent); a daily Sharpe ratio annualises by the square root of 252; and a strategy with a true annual Sharpe of 1 has roughly a one-in-six chance of a losing year, which is why nobody trusts a backtest with a Sharpe of 3.

## 2. Market mechanics an engineer must simulate

### 2.1 The limit order book

A market for one instrument is two sorted queues. Bids are buy orders sorted by price descending; asks are sell orders sorted by price ascending; the best bid and best ask bound the **spread**, and the **mid** is their average. A **limit order** rests in the book at its price until matched or cancelled; a **market order** crosses the spread and consumes resting orders from the best price down (or up) until filled. Within one price level, orders are matched in time order (**price-time priority**), so an order's **queue position** decides whether it fills. The **maker** who rested the order is usually paid a small rebate; the **taker** who crossed pays a fee. These facts have three consequences for every model downstream: the mid is not a price you can trade at; a resting order is adversely selected (it fills most readily when the price is about to move against it); and the cost of a large order is not the spread but the **impact** of walking the book.

The toy matching engine below implements price-time priority with partial fills. It is about forty lines and is enough to generate realistic fills in a backtest and to reason about queue position.

```python
import heapq
from dataclasses import dataclass, field
from itertools import count

_seq = count()

@dataclass(order=True)
class Order:
    key: tuple                      # sort key: (price priority, arrival sequence)
    id: int = field(compare=False)
    side: str = field(compare=False)
    price: float = field(compare=False)
    qty: int = field(compare=False)

class Book:
    """A limit order book with price-time priority and partial fills."""
    def __init__(self):
        self.bids, self.asks, self.fills = [], [], []

    def best(self, side):
        book = self.bids if side == "buy" else self.asks
        return book[0].price if book else None

    def submit(self, side, price, qty, oid=None):
        oid = oid if oid is not None else next(_seq)
        opp = self.asks if side == "buy" else self.bids
        crosses = (lambda p: price >= p) if side == "buy" else (lambda p: price <= p)
        while qty and opp and crosses(opp[0].price):
            resting = opp[0]
            traded = min(qty, resting.qty)
            self.fills.append((oid, resting.id, resting.price, traded))   # trade at the resting price
            qty -= traded
            resting.qty -= traded
            if resting.qty == 0:
                heapq.heappop(opp)
        if qty:                                                            # the remainder rests
            prio = -price if side == "buy" else price
            o = Order((prio, next(_seq)), oid, side, price, qty)
            heapq.heappush(self.bids if side == "buy" else self.asks, o)
        return oid

book = Book()
a1 = book.submit("sell", 100.02, 300)        # two asks at the same price: a1 arrived first
a2 = book.submit("sell", 100.02, 500)
b1 = book.submit("buy", 99.98, 400)
assert (book.best("buy"), book.best("sell")) == (99.98, 100.02)
spread_bps = (100.02 - 99.98) / ((100.02 + 99.98) / 2) * 1e4
assert round(spread_bps, 1) == 4.0           # a 4 basis-point spread

m = book.submit("buy", 100.05, 400)          # a marketable buy for 400 walks the ask queue in time order
assert [(f[1], f[3]) for f in book.fills] == [(a1, 300), (a2, 100)]   # a1 fully, then 100 of a2
assert book.asks[0].qty == 400               # a2 has 400 left; queue position decided who filled
assert book.best("sell") == 100.02
```

**What to take from it.** Fills happen at the resting order's price, so a marketable order pays the spread; a large order consumes several levels (walk the book with a bigger quantity and watch `best("sell")` move); and two orders at the same price are not equal, which is why a market-making model cares about queue position and why a backtest that assumes every limit order fills at its price overstates returns. Real engines add order types (stop, iceberg, post-only), auctions, self-trade prevention and tick-size rules; the priority logic is the same.

### 2.2 Market impact: the square-root law

Walking the book is the mechanical form of impact; the statistical form, measured across markets, is that the price moves against an order by an amount proportional to the daily volatility times the square root of the order's size as a fraction of daily volume:

impact ≈ Y · σ_daily · √(Q / V), with Y a constant near 0.5 to 1 in published studies.

A 1% of daily volume order in a stock with 2% daily volatility therefore costs roughly 0.7 × 2% × 0.1 ≈ 14 basis points of impact, more than three times the spread. Impact is the reason capacity exists: doubling the order size raises the impact by 41%, and at some size the impact equals the expected return of the signal. Section 8 turns this into code.

### 2.3 Adverse selection

A resting bid fills when a seller arrives. Sellers who know the price is about to fall arrive more often than those who do not, so the fills a market maker receives are biased toward the losing side. The market maker's spread is compensation for that bias plus inventory risk; a strategy that posts limit orders to "save the spread" collects the same adverse selection without the compensation. In a backtest, modelling limit-order fills as "filled whenever the price touched my level" ignores both queue position and adverse selection and is the second most common source of fictional profits after lookahead.

## 3. Return mathematics, worked by hand

### 3.1 Returns, Sharpe, drawdown

Simple returns compound multiplicatively; log returns add. For daily data the annualised mean is the daily mean times 252, the annualised volatility is the daily volatility times √252, and the annualised Sharpe ratio is their ratio, which is the daily Sharpe times √252. Maximum drawdown is the largest peak-to-trough fall in the cumulative equity curve. Hit rate is the share of positive periods; payoff ratio is the average win over the average loss; together they give expectancy. The code computes all of them on a synthetic series whose true daily Sharpe is known, so you can see how noisy the estimates are even with four years of data.

```python
import math, random, statistics

def metrics(daily_returns):
    n = len(daily_returns)
    mu, sd = statistics.fmean(daily_returns), statistics.stdev(daily_returns)
    sharpe = mu / sd * math.sqrt(252)
    equity, peak, max_dd = 1.0, 1.0, 0.0
    for r in daily_returns:
        equity *= 1 + r
        peak = max(peak, equity)
        max_dd = max(max_dd, 1 - equity / peak)
    wins = [r for r in daily_returns if r > 0]
    losses = [-r for r in daily_returns if r < 0]
    hit = len(wins) / n
    payoff = statistics.fmean(wins) / statistics.fmean(losses)
    return {"ann_return": mu * 252, "ann_vol": sd * math.sqrt(252), "sharpe": sharpe,
            "max_drawdown": max_dd, "hit_rate": hit, "payoff": payoff,
            "sharpe_se": math.sqrt((1 + 0.5 * sharpe**2 / 252) / n) * math.sqrt(252)}

rng = random.Random(7)
true_daily_sharpe = 1.0 / math.sqrt(252)          # an annual Sharpe of 1.0
sd = 0.01                                          # 1% daily volatility (about 16% annual)
rets = [rng.gauss(true_daily_sharpe * sd, sd) for _ in range(4 * 252)]
m = metrics(rets)
assert 0.3 < m["sharpe"] < 1.8                      # four years of data, and the estimate is this loose
assert m["sharpe_se"] > 0.45                        # the standard error of an annual Sharpe over 4 years is about 0.5
assert 0.45 < m["hit_rate"] < 0.6 and 0.05 < m["max_drawdown"] < 0.5
```

The last assertion is the lesson: the standard error of an annualised Sharpe ratio over T years is roughly 1/√T (the formula above, from Lo's 2002 paper, adds a small correction for the Sharpe itself), so four years of daily data cannot distinguish a Sharpe of 1 from a Sharpe of 0.5 with confidence. A desk that asks for "three years of live track record" is asking for a standard error of about 0.6.

### 3.2 The deflated Sharpe ratio

If you try N strategies on noise, the best one has a positive Sharpe by construction. Under independence, the expected maximum of N standard-normal Sharpe estimates is approximately

E[max] ≈ √V · [(1 − γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e))],

where V is the variance of the Sharpe estimates across trials, γ ≈ 0.5772 is the Euler–Mascheroni constant and Φ⁻¹ is the inverse normal distribution. Bailey and López de Prado's **deflated Sharpe ratio** asks: given the number of trials, the backtest length and the skew and kurtosis of returns, what is the probability that the observed Sharpe exceeds this expected maximum of noise? The code implements the expected-maximum benchmark and the deflation test.

```python
import math
from statistics import NormalDist

N01 = NormalDist()
EULER = 0.5772156649

def expected_max_sharpe(n_trials, var_trials):
    """Expected maximum Sharpe among n_trials strategies with no true skill (Bailey & López de Prado)."""
    if n_trials <= 1:
        return 0.0                                   # one trial: nothing was selected
    return math.sqrt(var_trials) * ((1 - EULER) * N01.inv_cdf(1 - 1 / n_trials)
                                    + EULER * N01.inv_cdf(1 - 1 / (n_trials * math.e)))

def deflated_sharpe_probability(observed_sharpe, n_trials, var_trials, n_obs, skew=0.0, kurt=3.0):
    """P(true Sharpe > 0) after deflating for the trials; Sharpe inputs are per observation (not annualised)."""
    sr0 = expected_max_sharpe(n_trials, var_trials)
    z = (observed_sharpe - sr0) * math.sqrt(n_obs - 1) / math.sqrt(
        1 - skew * observed_sharpe + (kurt - 1) / 4 * observed_sharpe**2)
    return N01.cdf(z)

# One year of daily data, observed annual Sharpe 1.5 → daily 0.0945. The researcher tried 50 variants whose
# Sharpe estimates had variance 0.004 (daily units).
daily_sr = 1.5 / math.sqrt(252)
p_one_trial = deflated_sharpe_probability(daily_sr, n_trials=1, var_trials=0.004, n_obs=252)
p_fifty = deflated_sharpe_probability(daily_sr, n_trials=50, var_trials=0.004, n_obs=252)
assert p_one_trial > 0.9                            # looks significant if it were the only trial
assert p_fifty < 0.5                                # after 50 trials, no better than a coin flip
assert round(expected_max_sharpe(50, 0.004) * math.sqrt(252), 2) > 1.4   # noise alone yields ~1.5 annualised
```

The practical rules that follow: log every trial (a research platform keeps a **trial ledger**, section 11), report the deflated probability beside the Sharpe, pre-register the hypothesis and the hold-out period, and treat an economic rationale as a prior that lowers the effective number of trials. The same arithmetic applies to feature selection, hyper-parameter sweeps and the "best of ten seeds" habit.

### 3.3 A losing year at Sharpe 1

With annual Sharpe S, the probability of a negative year under normality is Φ(−S). At S = 1 that is 16%; at S = 2 it is 2.3%; at S = 0.5 it is 31%. Say this when a desk asks how a strategy with a positive edge can lose money for a year; it is the same statistics as the standard error above, from the other side.

## 4. Point-in-time data engineering

### 4.1 Bitemporal tables and as-of joins

A fact about a company has two times: when it was true (the fiscal quarter it describes) and when it became known (the filing date, or the date a vendor loaded it, or the date it was revised). Backtests that join on the first time alone see revised, restated and late-arriving values as if they had been available on time, which is **lookahead bias** in its most common form. The fix is a bitemporal table with a `known_at` column and an **as-of join**: for each decision date, take the latest record whose `known_at` is on or before that date.

```python
import bisect
from datetime import date

# (ticker, period_end, known_at, eps): the Q4 EPS was first reported on 2 Feb and restated on 15 Mar.
facts = [
    ("ACME", date(2025, 12, 31), date(2026, 2, 2), 1.10),
    ("ACME", date(2025, 12, 31), date(2026, 3, 15), 0.95),    # restatement
    ("ACME", date(2026, 3, 31), date(2026, 5, 4), 1.20),
]

def as_of(facts, ticker, decision_date):
    """Latest value known on or before decision_date, by known_at then period_end."""
    known = [f for f in facts if f[0] == ticker and f[2] <= decision_date]
    if not known:
        return None
    return max(known, key=lambda f: (f[2], f[1]))

assert as_of(facts, "ACME", date(2026, 1, 15)) is None              # nothing known yet
assert as_of(facts, "ACME", date(2026, 2, 10))[3] == 1.10           # the first print
assert as_of(facts, "ACME", date(2026, 3, 20))[3] == 0.95           # the restatement, once known
assert as_of(facts, "ACME", date(2026, 5, 10))[3] == 1.20           # the next quarter

# The naive join on period_end alone would hand a 15 February backtest the restated 0.95 that nobody knew.
naive = max((f for f in facts if f[0] == "ACME" and f[1] <= date(2026, 2, 15)), key=lambda f: (f[1], f[2]))
assert naive[3] == 0.95 and as_of(facts, "ACME", date(2026, 2, 15))[3] == 1.10
```

At scale the as-of join is a sorted-merge on `(ticker, known_at)` with a binary search per decision date (`bisect` on a per-ticker list of `known_at` values), or a native as-of join in a time-series database or a dataframe library. The rule of the platform is that **no table without a `known_at` column may be joined into a backtest**.

### 4.2 Universes and survivorship

The set of tradable instruments changes: companies list, delist, merge and go bankrupt. A backtest run on "the current S&P 500" applies today's survivors to the past and inherits their success. The universe is therefore a table of `(instrument, start_date, end_date, reason)` and every backtest draws its candidates from the universe as it stood on the decision date. The same table carries the index-membership and listing-venue history that event-driven strategies need.

### 4.3 Corporate actions

A 2-for-1 split halves the price and doubles the share count; a dividend drops the price by its amount on the ex-date; a spin-off, a rights issue or a reverse split do stranger things. Prices must be adjusted so that returns are continuous across the event, and the adjustment must be applied **as of** the event date, not backfilled, otherwise a pre-split price series looks like it halved overnight. The adjusted series is derived at read time from the raw series and the actions table, so that a corrected action re-derives every dependent series.

```python
from datetime import date

raw = {date(2026, 3, 2): 200.0, date(2026, 3, 3): 202.0, date(2026, 3, 4): 101.5, date(2026, 3, 5): 103.0}
actions = [(date(2026, 3, 4), "split", 2.0)]       # 2-for-1 effective 4 March: prices before it are divided by 2

def adjusted(raw, actions, as_of_date):
    factors = {}
    for d in raw:
        f = 1.0
        for ex_date, kind, ratio in actions:
            if kind == "split" and d < ex_date <= as_of_date:
                f /= ratio
        factors[d] = f
    return {d: p * factors[d] for d, p in raw.items()}

adj = adjusted(raw, actions, date(2026, 3, 5))
assert adj[date(2026, 3, 3)] == 101.0 and adj[date(2026, 3, 4)] == 101.5
daily_return = adj[date(2026, 3, 4)] / adj[date(2026, 3, 3)] - 1
assert abs(daily_return - 0.00495) < 1e-4            # +0.5%, not −50%
# Viewed as of 3 March (before the split was effective), nothing is adjusted: the past does not know the future.
assert adjusted(raw, actions, date(2026, 3, 3))[date(2026, 3, 3)] == 202.0
```

### 4.4 Timestamps, sessions and vendors

Store everything in UTC with the exchange's session calendar beside it; a daily bar's timestamp means "the close of the session that ended at this time", and a signal computed from it is tradable at the next open at the earliest. Vendor data arrives late, gets revised and changes schema; the platform records the vendor's delivery time as `known_at`, keeps every version, and validates each delivery against the previous one (row counts, identifier coverage, distribution shifts) before research can see it. Alternative data adds panel bias (a credit-card panel is not the population), short history (three years is typical) and licensing terms that restrict what may be derived from it; the research platform tags every feature with its source's licence so a strategy's permitted use can be audited.

## 5. Labels and validation

### 5.1 Why standard cross-validation fails here

A label built from a 10-day forward return at date t shares 9 days with the label at date t+1. Randomly assigning dates to folds puts near-duplicates of the test labels into training, and the model's cross-validated score becomes a measure of memorisation. Serial correlation in features does the same more subtly. The fix has two parts: **purging** removes from the training set any observation whose label window overlaps the test fold's label windows; an **embargo** removes a further buffer of training observations immediately after the test fold so features that lag the labels cannot carry information back. Walk-forward validation (train on everything before the test period, roll forward) is the simpler scheme and should be the first you describe; purged k-fold uses the data more efficiently and is the one López de Prado's book made standard.

```python
def purged_kfold(n, k, horizon, embargo):
    """Yield (train_idx, test_idx) with purging of overlapping label windows and an embargo after each test fold.
    Observation i has a label window [i, i + horizon)."""
    fold_size = n // k
    for f in range(k):
        test_start, test_end = f * fold_size, (f + 1) * fold_size if f < k - 1 else n
        test = list(range(test_start, test_end))
        train = []
        for i in range(n):
            if test_start <= i < test_end:
                continue
            overlaps = i < test_end + horizon and i + horizon > test_start   # label windows intersect
            in_embargo = test_end + horizon <= i < test_end + horizon + embargo
            if not overlaps and not in_embargo:
                train.append(i)
        yield train, test

n, k, h, e = 100, 5, 10, 5
folds = list(purged_kfold(n, k, h, e))
train, test = folds[1]                      # test fold covers observations 20..39
assert test[0] == 20 and test[-1] == 39
assert 11 not in train and 19 not in train  # purged: their 10-day windows reach into the test fold
assert 10 in train                          # window [10, 20) ends exactly where the test fold starts
assert 40 not in train and 49 not in train  # purged: the test fold's own windows run to day 48
assert 50 not in train and 54 not in train  # embargoed
assert 55 in train
for tr, te in folds:                        # no training window ever overlaps a test window
    for i in tr:
        assert not any(i < j + h and i + h > j for j in te)
```

Each middle fold loses almost two horizons of training data to purging plus the embargo (here 11 to 19, 40 to 54), which is why the first and last folds keep more; with a long horizon and few folds the purge can remove a large share of the data, which is a signal that the horizon is long relative to the sample and that the number of effectively independent observations is small. The same code, with the test folds taken in combinations, gives combinatorial purged cross-validation, which produces many backtest paths rather than one.

### 5.2 Triple-barrier labels

A fixed-horizon label ("did the price rise over the next 10 days") ignores volatility and ignores how a position is actually run. The triple-barrier method places an upper barrier (profit-take), a lower barrier (stop-loss), both scaled by recent volatility, and a vertical barrier (maximum holding time), and labels the observation by the first barrier touched. The label matches the trade the strategy would make, and the barrier widths are strategy parameters rather than modelling conveniences.

```python
import random

def triple_barrier(prices, t0, vol, up_mult, down_mult, max_hold):
    """Return (label, exit_index): +1 upper barrier, -1 lower, 0 vertical (time) barrier."""
    p0 = prices[t0]
    upper, lower = p0 * (1 + up_mult * vol), p0 * (1 - down_mult * vol)
    for t in range(t0 + 1, min(t0 + max_hold, len(prices) - 1) + 1):
        if prices[t] >= upper:
            return 1, t
        if prices[t] <= lower:
            return -1, t
    return 0, min(t0 + max_hold, len(prices) - 1)

rising = [100 * 1.005 ** t for t in range(30)]           # +0.5% a day
falling = [100 * 0.995 ** t for t in range(30)]
flat = [100 + 0.1 * (t % 2) for t in range(30)]
assert triple_barrier(rising, 0, vol=0.01, up_mult=2, down_mult=2, max_hold=10) == (1, 4)    # +2% hit on day 4
assert triple_barrier(falling, 0, vol=0.01, up_mult=2, down_mult=2, max_hold=10) == (-1, 5)
assert triple_barrier(flat, 0, vol=0.01, up_mult=2, down_mult=2, max_hold=10) == (0, 10)     # time barrier

rng = random.Random(3)
prices = [100.0]
for _ in range(300):
    prices.append(prices[-1] * (1 + rng.gauss(0.0, 0.01)))
labels = [triple_barrier(prices, t, vol=0.01, up_mult=2, down_mult=2, max_hold=10)[0] for t in range(0, 280)]
counts = {l: labels.count(l) for l in (-1, 0, 1)}
assert sum(counts.values()) == 280 and all(counts[l] > 0 for l in counts)   # all three outcomes occur on noise
```

**Meta-labeling** builds on this: a primary model (or a rule) decides the side; a secondary model is trained on whether the primary model's call hit the profit barrier, with features that include the primary model's confidence; the secondary model's probability sizes the bet. Separating "which side" from "how much" lets a high-recall, low-precision primary signal be filtered into a usable one, and the secondary model can be a standard classifier evaluated with standard tools.

### 5.3 Sample uniqueness and weights

Overlapping labels also mean that observations are not equally informative: a label whose window overlaps with nine others carries about a tenth of the information of a label that overlaps with none. The **average uniqueness** of an observation is the mean over its window of one divided by the number of concurrent labels; it is used as a sample weight in training and to shrink the effective sample size when computing confidence intervals. The computation is a counting pass.

```python
def average_uniqueness(n, horizon):
    concurrency = [0] * (n + horizon)
    for i in range(n):
        for t in range(i, i + horizon):
            concurrency[t] += 1
    return [sum(1 / concurrency[t] for t in range(i, i + horizon)) / horizon for i in range(n)]

u = average_uniqueness(50, 10)
assert abs(u[25] - 0.1) < 1e-9             # a label in the middle shares every day with 9 others
assert u[0] > u[25] and u[49] > u[25]      # edges overlap with fewer labels
effective_n = sum(u)
assert 5 < effective_n < 7                  # fifty overlapping labels are worth about six independent ones
```

Fifty daily observations with ten-day labels are worth about six independent observations (the middle thirty contribute a tenth each, the edges a little more). A confidence interval computed with n = 50 is almost three times too narrow.

## 6. Features and models: what is different about markets

**Signal-to-noise.** A model that explains 1% of the variance of next-day returns can run a profitable strategy; a model reporting 60% directional accuracy on liquid daily data has leaked. Expect R² near zero, information coefficients (the rank correlation between forecast and realised return) of 0.02 to 0.05 for a good cross-sectional signal, and ensembles over many weak features rather than one strong one. The breadth of a signal (how many independent bets it makes per year) matters as much as its information coefficient: the fundamental law of active management (Grinold and Kahn) says the information ratio is roughly the information coefficient times the square root of breadth, which is why a weak signal applied to thousands of stocks daily can beat a strong one applied to ten stocks a year.

**Feature families** (the systematic-trading guide lists them in detail): price-derived (returns over several horizons, volatility, volume ratios, distance from moving averages), cross-sectional (ranks and z-scores within the universe on each date, which remove market-wide moves), fundamental (as-of valuation and quality ratios), microstructure (spread, order imbalance, trade-sign autocorrelation for intraday work), and text (section 10). Every feature is computed as of the decision date from point-in-time inputs and stored with the timestamp of the latest input it used; the research platform refuses a feature whose inputs' `known_at` exceeds the decision date.

**Fractional differentiation** is the idea that a price series must be made stationary for most models but that full differencing (taking returns) throws away memory; differencing by a fractional order (0.3 to 0.5 is typical) keeps some level information while passing stationarity tests. It is a standard tool in López de Prado's book and a frequent interview question.

**Feature importance under autocorrelation.** Permutation importance computed with random k-fold is unreliable for the reasons of section 5; compute it inside purged cross-validation (mean decrease accuracy with purging), and treat clustered features (many volatility measures) as a group, otherwise importance is shared among the cluster members and each looks unimportant.

**Models.** Regularised linear models remain the baseline and often the production model for cross-sectional signals because they are stable and auditable; gradient-boosted trees are the workhorse for non-linear tabular signals; sequence models earn their keep on intraday order-flow data and on text; reinforcement learning is used for execution and market making, where the environment can be simulated faithfully, and rarely for alpha, where it cannot. Whatever the model, the deliverable is a calibrated probability or an expected return with an uncertainty, because sizing (section 9) needs both.

## 7. Backtester design

### 7.1 What a backtest must simulate

A backtest is a simulation of the whole trading process, not a multiplication of signals by returns. It needs: the universe as of each date; features and signals as of each date; a portfolio-construction step with constraints; an order-generation step; a fill model (at what price and quantity an order executes, given the spread, the order's size relative to volume and, for limit orders, queue position); a cost model (fees, spread, impact, borrow for shorts, financing); a risk layer that applies the same limits as production; and an accounting layer that marks positions, pays costs and records every event. The output is a ledger of orders, fills, positions and cash from which every metric in section 3 is computed, plus the trial ledger entry (section 11).

### 7.2 A minimal event-driven backtester

The code below is a complete event-driven loop with a fill model (market orders fill at the next open, paying half the spread plus square-root impact) and a cost model. It is small enough to read in full and large enough to show the structure that production backtesters share.

```python
import math, random
from dataclasses import dataclass, field

@dataclass
class Bar:
    day: int; open: float; close: float; volume: float; spread_bps: float; daily_vol: float

@dataclass
class CostModel:
    fee_bps: float = 0.5          # commissions and fees, per side
    impact_coeff: float = 0.7     # Y in the square-root law
    def cost_per_share(self, bar, qty):
        half_spread = bar.open * bar.spread_bps / 2e4
        impact = bar.open * self.impact_coeff * bar.daily_vol * math.sqrt(abs(qty) / bar.volume)
        fee = bar.open * self.fee_bps / 1e4
        return half_spread + impact + fee

@dataclass
class Ledger:
    cash: float
    position: int = 0
    fills: list = field(default_factory=list)
    equity_curve: list = field(default_factory=list)

def run_backtest(bars, signal, cost_model, cash=1_000_000, target_fraction=0.5):
    """signal(bars[:t]) -> desired sign (+1, -1, 0) using data up to the close of day t-1 only."""
    led = Ledger(cash=cash)
    for t in range(1, len(bars)):
        history, today = bars[:t], bars[t]            # the signal sees yesterday's close at most
        side = signal(history)
        if side == (led.position > 0) - (led.position < 0):
            led.equity_curve.append(led.cash + led.position * today.close)
            continue                                   # rebalance only when the signal changes side
        target_value = side * target_fraction * (led.cash + led.position * history[-1].close)
        target_qty = int(target_value / today.open)
        delta = target_qty - led.position
        if delta:
            cps = cost_model.cost_per_share(today, delta)
            price = today.open + math.copysign(cps, delta)    # buys pay up, sells receive less
            led.cash -= delta * price
            led.position += delta
            led.fills.append((today.day, delta, round(price, 4), round(abs(delta) * cps, 2)))
        led.equity_curve.append(led.cash + led.position * today.close)
    return led

rng = random.Random(11)
bars, price = [], 100.0
for d in range(260):
    o = price * (1 + rng.gauss(0, 0.002))
    c = o * (1 + rng.gauss(0.0003, 0.012))
    bars.append(Bar(d, o, c, volume=2_000_000, spread_bps=3.0, daily_vol=0.012))
    price = c

momentum = lambda hist: 1 if len(hist) > 20 and hist[-1].close > hist[-21].close else -1
always_long = lambda hist: 1

led_mom = run_backtest(bars, momentum, CostModel())
led_long = run_backtest(bars, always_long, CostModel())
assert len(led_long.fills) == 1                      # buy once, hold: one fill, costs paid once
turnover_mom = sum(abs(f[1]) for f in led_mom.fills)
assert turnover_mom > 5 * abs(led_long.fills[0][1])   # momentum flips sides: several times the turnover
costs_mom = sum(f[3] for f in led_mom.fills)
assert costs_mom > 5 * led_long.fills[0][3]            # and pays several times the costs
# No lookahead: the signal on day t is a function of bars[:t] only.
assert momentum(bars[:30]) == momentum(bars[:30] + [Bar(999, 1e9, 1e9, 1, 1, 1)][:-1])
```

The two strategies on the same path show the point of a cost model: the signal's turnover is a cost line that a vectorised "signal times return" backtest never pays. Three things the real version adds: fills spread over the day with participation limits (an order larger than a few percent of daily volume cannot fill at the open); limit-order fills with queue-position logic from section 2; and corporate actions, borrow availability and financing from the data platform. **Research and production must share the fill and cost models**: the production simulator is validated monthly against real fills (predicted versus realised implementation shortfall by order size bucket), and the research backtester imports the same model, so that a strategy approved in research is approved under the costs it will actually pay.

### 7.3 Vectorised versus event-driven

A vectorised backtest (positions as a matrix, returns as a matrix, costs as turnover times a constant) is fast and fine for early screening of cross-sectional signals, where thousands of names are traded in small sizes and the path dependence is weak. It cannot represent limit orders, partial fills, intraday risk limits or impact that depends on the order sequence. Event-driven is the one you trust; vectorised is the one you screen with; and the two must agree on simple strategies, which is a unit test the platform runs.

## 8. Costs, impact and execution

### 8.1 Implementation shortfall

The execution benchmark that matters is the **decision price**: the price when the portfolio decided to trade. Everything lost between that moment and the final fill is implementation shortfall, and it decomposes into **delay cost** (price moved before the order reached the market), **execution cost** (the fills were worse than the arrival price: spread and impact), and **opportunity cost** (part of the order never filled and the price kept moving). The decomposition is bookkeeping, and it is how execution algorithms and traders are judged.

```python
def implementation_shortfall(decision_px, arrival_px, fills, intended_qty, final_px, side=+1):
    """fills: list of (price, qty). Returns the shortfall in currency and its three components (buy: side=+1)."""
    filled = sum(q for _, q in fills)
    avg_fill = sum(p * q for p, q in fills) / filled if filled else arrival_px
    delay = side * (arrival_px - decision_px) * filled
    execution = side * (avg_fill - arrival_px) * filled
    opportunity = side * (final_px - decision_px) * (intended_qty - filled)
    total = delay + execution + opportunity
    return total, {"delay": delay, "execution": execution, "opportunity": opportunity, "filled": filled}

# Decide to buy 10,000 at 50.00; by the time the order arrives the price is 50.05; fills average 50.09 for 8,000;
# the remaining 2,000 are never done and the close is 50.30.
total, parts = implementation_shortfall(50.00, 50.05, [(50.08, 5000), (50.10, 3000)], 10_000, 50.30)
assert round(parts["delay"]) == 400 and round(parts["execution"]) == 300 and round(parts["opportunity"]) == 600
assert round(total) == 1300
shortfall_bps = total / (50.00 * 10_000) * 1e4
assert round(shortfall_bps) == 26               # 26 basis points of the decision value
```

Twenty-six basis points on a trade whose expected return might have been 40 is the arithmetic that kills strategies, and the opportunity cost of the unfilled quantity is the term that traders most often leave out.

### 8.2 The square-root law in numbers, and capacity

```python
import math

def impact_bps(order_qty, daily_volume, daily_vol, Y=0.7):
    return Y * daily_vol * math.sqrt(order_qty / daily_volume) * 1e4

assert round(impact_bps(20_000, 2_000_000, 0.02)) == 14          # 1% of ADV in a 2%-vol stock: ~14 bps
assert round(impact_bps(80_000, 2_000_000, 0.02)) == 28          # 4× the size: 2× the impact (square root)

def capacity(expected_bps, daily_volume, daily_vol, Y=0.7, spread_bps=3.0):
    """Largest order (as a fraction of ADV) at which impact plus half the spread equals the expected return."""
    net = expected_bps - spread_bps / 2
    if net <= 0:
        return 0.0
    return (net / 1e4 / (Y * daily_vol)) ** 2

frac = capacity(expected_bps=30, daily_volume=2_000_000, daily_vol=0.02)
assert 0.03 < frac < 0.05                                           # about 4% of daily volume per trade
```

A signal worth 30 basis points per trade in a 2%-volatility stock can be traded at about 4% of daily volume before costs equal the edge, and at half that size if the strategy wants to keep half the edge. Multiply by the number of names and the turnover and you have the strategy's capacity in dollars, which is the number an allocator asks for first.

### 8.3 Optimal execution: Almgren–Chriss

Trading fast pays more impact; trading slowly bears more price risk. Almgren and Chriss (2000) solved the trade-off for linear impact and a mean-variance trader: the optimal schedule sells the holding along a hyperbolic-sine curve whose steepness κ rises with risk aversion and volatility and falls with impact. With risk aversion zero the schedule is a straight line (TWAP); with high risk aversion it front-loads.

```python
import math

def almgren_chriss_schedule(X, T, n_steps, kappa):
    """Remaining shares x_k at step k for an order of X shares over T periods; kappa = 0 gives TWAP."""
    tau = T / n_steps
    if kappa == 0:
        return [X * (1 - k / n_steps) for k in range(n_steps + 1)]
    return [X * math.sinh(kappa * (T - k * tau)) / math.sinh(kappa * T) for k in range(n_steps + 1)]

twap = almgren_chriss_schedule(100_000, T=1.0, n_steps=10, kappa=0.0)
urgent = almgren_chriss_schedule(100_000, T=1.0, n_steps=10, kappa=4.0)
assert twap[5] == 50_000 and urgent[0] == 100_000 and round(urgent[-1]) == 0
assert urgent[5] < 20_000                 # a risk-averse trader has done more than 80% by half-time
trades_twap = [twap[k] - twap[k + 1] for k in range(10)]
trades_urgent = [urgent[k] - urgent[k + 1] for k in range(10)]
assert max(trades_twap) - min(trades_twap) < 1e-6 and trades_urgent[0] > 3 * trades_urgent[-1]
```

In production the schedule is the backbone and a tactical layer decides each child order (limit versus market, which venue, how to react to the book); VWAP algorithms follow the historical volume curve instead; participation-rate algorithms cap the share of volume. The engineer's job is the measurement loop: realised shortfall versus the schedule's prediction, by order size, urgency and venue, feeding back into the cost model of section 7.

## 9. Portfolio construction and risk

### 9.1 Sizing: Kelly and its fractions

For a bet with expected excess return μ and variance σ² per period, the growth-optimal fraction of capital is f* = μ/σ². It maximises long-run growth and produces drawdowns no one tolerates, and it assumes μ and σ are known; estimation error makes full Kelly over-bet badly. Practice is half Kelly or less, capped by risk limits, liquidity and the correlation with everything else in the book.

```python
import math, random

def growth_rate(f, mu, sigma):
    """Expected log-growth per period at fraction f (continuous approximation)."""
    return f * mu - 0.5 * f**2 * sigma**2

mu, sigma = 0.0004, 0.01                     # per day: ~10% annual excess return, 16% volatility
f_star = mu / sigma**2
assert f_star == 4.0                          # Kelly says 4× leverage; nobody runs that
assert growth_rate(f_star, mu, sigma) > growth_rate(2.0, mu, sigma) > growth_rate(8.0, mu, sigma)
assert growth_rate(8.0, mu, sigma) == 0.0     # twice Kelly: zero growth, maximal variance

# Estimation error: with mu estimated from 2 years of daily data, the standard error is about sigma/sqrt(504).
se = sigma / math.sqrt(504)
assert se > mu                                # the estimate of mu is noisier than mu itself
rng = random.Random(5)
f_estimates = [(mu + rng.gauss(0, se)) / sigma**2 for _ in range(2000)]
assert sum(f < 0 for f in f_estimates) / 2000 > 0.15   # a sixth of the time the estimate says "go short"
```

The last assertion is why fractional Kelly exists: the input is estimated with a standard error larger than itself. Volatility targeting (scale positions so the portfolio's forecast volatility equals a target) is the operational form; it responds to changing σ even when μ is unknowable.

### 9.2 Factor exposure and residual risk

A portfolio's return is explained partly by common factors (the market, size, value, momentum, sectors) and partly by idiosyncratic residuals. A strategy that claims alpha should show that its returns survive regression on the factors it did not intend to bet on; a market-neutral strategy with a beta of 0.3 is a leveraged index fund with extra steps. The regression is ordinary least squares; the code implements it with normal equations for the two-factor case and shows a "strategy" that is mostly market beta.

```python
import random

def ols(y, xs):
    """Least squares for y = a + b1*x1 + b2*x2 (two regressors) via normal equations."""
    n = len(y)
    X = [[1.0] + [x[i] for x in xs] for i in range(n)]
    k = len(X[0])
    XtX = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(k)] for i in range(k)]
    Xty = [sum(X[r][i] * y[r] for r in range(n)) for i in range(k)]
    # Gaussian elimination
    A = [row[:] + [b] for row, b in zip(XtX, Xty)]
    for i in range(k):
        piv = max(range(i, k), key=lambda r: abs(A[r][i])); A[i], A[piv] = A[piv], A[i]
        for r in range(k):
            if r != i:
                fct = A[r][i] / A[i][i]
                A[r] = [a - fct * b for a, b in zip(A[r], A[i])]
    return [A[i][k] / A[i][i] for i in range(k)]

rng = random.Random(2)
n = 1000
market = [rng.gauss(0.0003, 0.01) for _ in range(n)]
value = [rng.gauss(0.0001, 0.005) for _ in range(n)]
strategy = [0.0002 + 0.6 * m + 0.1 * v + rng.gauss(0, 0.004) for m, v in zip(market, value)]
alpha, beta_mkt, beta_val = ols(strategy, [market, value])
assert 0.5 < beta_mkt < 0.7 and -0.1 < beta_val < 0.3
assert alpha < 0.0005                                # the "alpha" is 2 bps a day; most of the return was beta
residual = [s - (alpha + beta_mkt * m + beta_val * v) for s, m, v in zip(strategy, market, value)]
import statistics
assert statistics.stdev(residual) < 0.7 * statistics.stdev(strategy)   # factors explain about two-thirds of the variance
```

Commercial risk models (Barra and its competitors) do this with dozens of factors and estimated covariances; the engineer's work is the daily pipeline that computes exposures, the pre-trade check that rejects orders breaching an exposure limit, and the attribution report that splits yesterday's profit and loss into factor and residual.

### 9.3 Value at risk, expected shortfall and the limits of both

Value at risk at 99% over one day is the loss exceeded on one day in a hundred; expected shortfall is the average loss on those days. Historical simulation (apply the last 500 days of returns to today's positions) is the common method; parametric VaR assumes normality and understates tails; both assume the future resembles the sample, which is exactly what fails in a crisis when correlations go to one. The code computes both from a fat-tailed sample and shows how much the normal assumption understates the tail.

```python
import random, statistics
from statistics import NormalDist

rng = random.Random(9)
# Daily returns from a mixture: calm days (sd 0.8%) and stress days (sd 3%), 10% of the time.
rets = [rng.gauss(0, 0.03 if rng.random() < 0.1 else 0.008) for _ in range(5000)]
losses = sorted(-r for r in rets)
idx = int(0.99 * len(losses))
var_hist = losses[idx]
es_hist = statistics.fmean(losses[idx:])
var_normal = NormalDist(0, statistics.stdev(rets)).inv_cdf(0.99)
assert var_hist > 1.15 * var_normal           # the normal model understates the 99% loss by a wide margin
assert es_hist > 1.2 * var_hist               # the average tail loss is well beyond the threshold
```

Limits in production are layered: gross and net exposure, per-name and per-sector concentration, factor exposures, VaR and expected shortfall, drawdown-triggered de-risking, and operational limits (order rate, order size, fat-finger price bands). Pre-trade checks are synchronous and deterministic; nothing in the ML stack is allowed to bypass them, and the kill switch (flatten everything, stop trading) is a human control with a documented owner.

## 10. The AI layer: language models and agents in quant research

### 10.1 What language models are good for

Markets price numbers quickly and text slowly, which is where language models earn their place. The productive uses in 2026, in rough order of maturity:

- **Earnings calls and filings.** Tone and hedging in management's prepared remarks and answers; changes in guidance language quarter over quarter; new risk factors in a 10-K; the gap between what analysts asked and what management answered. Features are differences and surprises, not levels: "the word *headwinds* appeared for the first time in eight quarters" carries information; "the call was positive" does not, because every call is.
- **News and events.** Extraction of structured events (a product recall, a management change, a regulatory action, a merger term) with entity resolution to tickers, timestamps to the second, and a confidence; event-driven strategies consume the structured record, not the prose.
- **Alternative data normalisation.** Job postings, app reviews, supplier mentions, patent text: the model turns unstructured sources into panel features with a schema.
- **Research assistance.** Summarising literature, drafting backtest code against the platform's API, proposing hypotheses, writing the documentation that model-risk management requires (section 11), and reviewing another researcher's notebook for leakage patterns.

The common shape is **model as feature extractor, not decision maker**: the language model produces a structured, timestamped, versioned feature; the quant pipeline treats it like any other feature, with the same validation, the same cost model and the same trial ledger.

### 10.2 Leakage controls specific to language models

Two leaks are new with language models and both are fatal to a backtest.

**Knowledge leakage through pretraining.** A model whose training data runs through 2025 knows that a certain company's product failed in 2024 and that another's drug was approved. Ask it to score the "outlook" of a 2023 filing and it will, without meaning to, use the future. There is no prompt that removes this. The controls are: use a model whose documented training cut-off precedes the start of the evaluation period (vendors publish cut-offs; keep a table of them); or restrict the model to extraction tasks whose answer is contained in the input text (which entity, which number, which date) and verify extraction accuracy against human labels, so the model's world knowledge cannot contribute; and run a **canary test**: feed the model a document about a well-known post-cut-off event with the identifying names replaced, and check that its outputs do not reflect the outcome.

**Leakage through the corpus.** A text dataset assembled today contains articles that were edited later, filings that were restated, transcripts that were corrected, and timestamps that record the vendor's load date rather than publication. The same bitemporal discipline as section 4 applies: every document carries its `known_at`, the corpus is queried as-of, and the vendor's delivery lag is measured and added to the decision timestamp.

The code below is the shape of a leakage-safe feature pipeline: a cut-off registry, a corpus query that is as-of by construction, and a decision timestamp that includes the extraction latency, because a feature that takes four hours to compute is not available at the open.

```python
from datetime import datetime, timedelta, timezone

MODEL_CUTOFFS = {"extractor-2026-06": datetime(2026, 3, 31, tzinfo=timezone.utc),
                 "extractor-2024-09": datetime(2024, 6, 30, tzinfo=timezone.utc)}

docs = [  # (doc_id, published_at, known_at (vendor load), text)
    ("d1", datetime(2026, 2, 3, 21, 5, tzinfo=timezone.utc), datetime(2026, 2, 3, 23, 40, tzinfo=timezone.utc), "guidance raised"),
    ("d2", datetime(2026, 2, 3, 21, 5, tzinfo=timezone.utc), datetime(2026, 2, 5, 9, 0, tzinfo=timezone.utc), "transcript corrected"),
]

def eligible_model(model, eval_start):
    return MODEL_CUTOFFS[model] < eval_start

def corpus_as_of(docs, decision_time, extraction_latency):
    """Documents whose vendor load time plus the pipeline's own latency is before the decision time."""
    return [d for d in docs if d[2] + extraction_latency <= decision_time]

eval_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
assert not eligible_model("extractor-2026-06", eval_start)      # trained through March 2026: knows the period
assert eligible_model("extractor-2024-09", eval_start)

open_4feb = datetime(2026, 2, 4, 14, 30, tzinfo=timezone.utc)   # 09:30 New York
lat = timedelta(hours=2)
assert [d[0] for d in corpus_as_of(docs, open_4feb, lat)] == ["d1"]           # the correction is not known yet
assert [d[0] for d in corpus_as_of(docs, open_4feb, timedelta(hours=16))] == []  # a slow pipeline misses the open
```

### 10.3 Research agents under a pre-registration protocol

An agent that proposes hypotheses, writes backtests and ranks results is a trial-generating machine, and section 3.2 says what unlogged trials do to a Sharpe ratio. The protocol that makes such an agent useful rather than dangerous:

1. **Hypotheses are registered before the backtest runs**, with the economic rationale, the universe, the period, the cost model and the primary metric, in a ledger the agent appends to and cannot edit.
2. **The hold-out period is unreachable.** The research environment serves data only up to a cut-off; the final period is evaluated once, by a separate job, with the ledger's trial count applied as a deflation.
3. **The agent's code runs against the platform's backtester**, never its own; fill and cost models are inherited, not reimplemented.
4. **Every run is a ledger entry**: hypothesis id, code hash, data snapshot, metrics, deflated probability. The agent reports the deflated figure beside the raw one.
5. **A human reads the losers.** The value of an agent that tries two hundred variants is in the two hundred, not in the best one; the distribution of results across variants is itself evidence about whether the effect is real.

```python
import hashlib, json, math
from statistics import NormalDist

class TrialLedger:
    """Append-only record of every backtest; the deflated figure uses the running trial count."""
    def __init__(self):
        self.entries = []
    def register(self, hypothesis, rationale, universe, period, cost_model):
        hid = hashlib.sha256(json.dumps([hypothesis, universe, period, cost_model]).encode()).hexdigest()[:12]
        self.entries.append({"id": hid, "hypothesis": hypothesis, "rationale": rationale, "result": None})
        return hid
    def record(self, hid, daily_sharpe, n_obs):
        e = next(e for e in self.entries if e["id"] == hid and e["result"] is None)
        n_trials = sum(1 for x in self.entries if x["result"] is not None) + 1
        var_trials = 0.004                       # variance of Sharpe estimates across trials, estimated from history
        euler = 0.5772156649
        sr0 = 0.0 if n_trials == 1 else math.sqrt(var_trials) * (
            (1 - euler) * NormalDist().inv_cdf(1 - 1 / n_trials) + euler * NormalDist().inv_cdf(1 - 1 / (n_trials * math.e)))
        z = (daily_sharpe - sr0) * math.sqrt(n_obs - 1) / math.sqrt(1 + 0.5 * daily_sharpe**2)
        e["result"] = {"sharpe_annual": daily_sharpe * math.sqrt(252), "n_trials": n_trials,
                       "deflated_p": NormalDist().cdf(z)}
        return e["result"]

ledger = TrialLedger()
results = []
for i in range(40):                               # an agent tries forty variants of one idea
    hid = ledger.register(f"variant {i}", "post-earnings drift", "us-largecap", "2019-2024", "sqrt-impact-v3")
    results.append(ledger.record(hid, daily_sharpe=0.08 + 0.001 * i, n_obs=1500))
best = max(results, key=lambda r: r["sharpe_annual"])
assert round(best["sharpe_annual"], 2) == 1.89 and best["n_trials"] == 40
assert best["deflated_p"] < results[0]["deflated_p"]      # the same raw Sharpe is worth less after forty trials
assert all(e["result"] is not None for e in ledger.entries) and len({e["id"] for e in ledger.entries}) == 40
```

### 10.4 Cost, latency and evaluation of the language-model layer

Text features cost tokens (chapter 63) and time. A 10-K is 100,000 tokens; scoring 4,000 of them per quarter at frontier prices is a four-figure sum, acceptable; scoring every news item in real time on a frontier model is not, so the pipeline tiers: a small classifier or embedding filter first, the large model on the few percent that pass, and caching by document hash. Latency sets what the feature can be used for: a filing feature computed overnight serves a daily strategy; a news feature must be ready in seconds to matter intraday, which pushes it toward smaller models and pre-computed entity tables. Evaluation is the judge discipline of chapter 66 applied to extraction: a labelled set per field, precision and recall per field, an "unknown" exit, a calibration check, drift monitoring on the distribution of extracted values, and a human audit of a sample every week, because a silent change in a vendor's transcript format can zero a feature without an error.

## 11. Model risk management and compliance engineering

### 11.1 SR 11-7 as a system specification

The Federal Reserve's supervisory guidance on model risk management (SR 11-7, 2011) is the vocabulary banks and many funds use, and job descriptions quote it. Its three pillars translate directly into platform artifacts.

| Guidance | What it asks | The artifact the engineer builds |
|---|---|---|
| Conceptual soundness | the model's design, assumptions and limitations are documented and justified | the model card: purpose, data with `known_at` provenance, features and their licences, method, assumptions, known failure modes, the trial ledger summary with the deflated probability |
| Ongoing monitoring | the model is watched in production against its expectations | the monitoring job: realised versus expected returns by period, feature drift, prediction drift, attribution to factors and to the signal, alert thresholds and the retirement rule |
| Independent validation | someone other than the developer tests the model | the reproducibility package: data snapshot, code hash, environment, a one-command rerun that reproduces the backtest to the cent, and the validator's report with its own tests |

Add a **model inventory** (every model in production with owner, version, validation date, limits and dependencies), **change control** (a new version is a new entry with a validation, not an edit), and a **retirement log**. A quant AI engineer who can describe these artifacts is describing most of what a model-risk team asks for.

### 11.2 Monitoring a live strategy

Monitoring answers one question daily: is the strategy behaving as its backtest said it would? The checks, with the mechanism:

- **Return in band.** Realised returns over rolling windows against the backtest's distribution; a sequential test (CUSUM or a Bayesian change-point) rather than a daily z-score, because daily tests false-alarm constantly.
- **Attribution.** Yesterday's profit and loss split into factor exposures, the signal and execution; a strategy making money for the wrong reason is retired as readily as one losing it.
- **Feature and prediction drift.** Distribution distances on each feature and on the model's output against the training window; a vendor schema change shows up here first.
- **Execution quality.** Realised shortfall against the cost model's prediction by size bucket; a persistent gap means the cost model is stale and every backtest is optimistic.
- **Capacity and crowding.** Impact per unit traded rising over months is the signature of a crowded trade.
- **The retirement rule, written down in advance.** For example: retire if the 60-day realised Sharpe is below the backtest's 5th percentile for two consecutive windows after attribution rules out execution, or if the mechanism the signal relies on has demonstrably changed.

### 11.3 Compliance engineering

The rules an engineer enforces in code rather than in policy documents:

- **Material non-public information.** Every data source is reviewed and approved before research can see it; approval, licence and permitted uses are recorded on the source; the pipeline tags every derived feature with its sources so a strategy's inputs can be audited; information barriers are access controls on data and on chat, not reminders.
- **Market manipulation.** Execution algorithms carry controls against spoofing and layering patterns (no placing orders with intent to cancel to move the book), wash trades (no self-matching), and marking the close; order-rate and cancel-ratio limits are enforced pre-trade.
- **Record keeping.** Orders, fills, model versions, the data each decision used and the approvals behind each change are retained for the regulator's horizon (years) in an immutable store; the trial ledger is part of the record.
- **Pre-trade limits** (section 9.3) are deterministic, synchronous and cannot be bypassed by any model.
- **Language-model-specific rules.** Expert-network transcripts and scraped web data pass compliance review before a model may read them; model outputs that could constitute investment advice to clients go through the same review as human research; prompts and outputs are logged.

## 12. The platform

```
                         ┌──────────────────────────────────────────────────────────┐
  vendors, exchanges,    │  Data platform (bitemporal): raw → validated → as-of views │
  filings, news  ───────▶│  universe table · corporate actions · known_at everywhere  │
                         └───────────────┬──────────────────────────────────────────┘
                                         │ as-of reads only
             ┌───────────────────────────▼───────────────────────────┐
             │ Feature store: computed once, timestamped by latest    │
             │ input, shared by research and production (no skew)     │
             └──────────┬───────────────────────────────┬────────────┘
                        │                               │
      ┌─────────────────▼──────────────┐    ┌───────────▼────────────────────────┐
      │ Research environment            │    │ Production                          │
      │ notebooks · trial ledger ·      │    │ signal service → portfolio construction│
      │ purged CV · backtester (shared  │    │ → pre-trade risk (deterministic)      │
      │ fill + cost models) · hold-out  │    │ → execution algos → OMS → venues      │
      │ served by a separate job        │    │ positions · PnL · attribution         │
      └─────────────────┬──────────────┘    └───────────┬────────────────────────┘
                        │ validated model + card          │ fills, realised costs
             ┌──────────▼─────────────────────────────────▼────────────┐
             │ Model risk: inventory · validation · monitoring · retire │
             │ Compliance: source approval · records · limits · audit   │
             └──────────────────────────────────────────────────────────┘
```

**Latency tiers.** Batch research in Python on a cluster; daily and intraday signals as services with budgets from minutes to sub-second; anything faster in C++ with models exported to fixed-cost forms, owned by a low-latency team. The boundary is a design decision: promising machine learning inside a budget that cannot afford a model's inference is the "right too late" failure.

**Storage.** Time-series stores or columnar files partitioned by date for market data; a relational store with bitemporal tables for reference data and fundamentals; an object store for raw vendor deliveries, kept forever; the trial ledger and model inventory in a transactional database with an audit trail. Chapter 40b's storage table applies with one extra column: every table has `known_at`.

**Reproducibility.** A backtest is a function of (code hash, data snapshot id, configuration); the platform can rerun any ledger entry years later and get the same number, which is what independent validation and regulators require and what makes a research result trustworthy.

## 13. Interview bank

Thirty questions with the shape of a strong answer. The first ten are asked of everyone; the rest probe the engineering.

1. *A backtest shows a Sharpe of 3 on daily US equities. First checks?* Lookahead (as-of joins, adjustment dates, vendor lags), survivorship (universe as of each date), the cost model (net or gross; validated against real fills?), the trial count behind the result, and whether the hold-out was ever touched. Say "a Sharpe of 3 is a bug until proven otherwise".
2. *Why not k-fold cross-validation?* Overlapping labels and serial correlation leak the test set; purge, embargo, or walk forward (section 5).
3. *What is a basis point, and what is the spread on a liquid large-cap?* One hundredth of a percent; a few basis points.
4. *Explain implementation shortfall.* Decision price to achieved price: delay, execution, opportunity (section 8.1).
5. *How does impact scale with order size?* Square root; doubling the order raises impact by 41%; capacity follows (section 8.2).
6. *Kelly says 4× leverage. What do you run?* A fraction; the estimate of μ has a standard error larger than μ; volatility targeting operationally (section 9.1).
7. *What is the deflated Sharpe ratio for?* Correcting for the number of trials; the expected maximum of N noise strategies grows like √(2 ln N) (section 3.2).
8. *How would you use an LLM in a strategy?* As a feature extractor over a point-in-time corpus with a model whose cut-off precedes the test period; canary tests; the same validation as any feature (section 10).
9. *When do you retire a model?* By a rule written before deployment, after attribution rules out execution (section 11.2).
10. *What is insider trading, and how does your pipeline avoid it?* Trading on material non-public information; source approval, provenance tags, barriers, records (section 11.3).
11. *Design the as-of join for fundamentals with restatements.* Bitemporal table, `known_at`, latest record on or before the decision date (section 4.1).
12. *A stock split happened last week; the backtest shows a −50% day. What went wrong?* Adjustment applied at the wrong time or not at all; adjust at read time from the actions table (section 4.3).
13. *How do you label for a strategy that uses stops?* Triple barrier (section 5.2); meta-labeling for sizing.
14. *Fifty daily observations with ten-day labels: how many are independent?* About six (section 5.3).
15. *Why do you need both a research backtester and a production simulator, and what must they share?* Screening versus truth; fill and cost models, validated monthly against fills (section 7).
16. *How does a limit order fill in your backtest?* Queue position and adverse selection, not "price touched my level" (section 2).
17. *Describe Almgren–Chriss in one sentence.* A schedule that trades the impact of speed against the risk of delay; κ rises with risk aversion and volatility (section 8.3).
18. *Your market-neutral strategy has a beta of 0.3.* It is not market neutral; regress on factors, hedge, and report residual return (section 9.2).
19. *Historical VaR says 2%; the normal model says 1.5%. Which do you trust?* Neither fully; fat tails make the normal one wrong, the historical one assumes the sample contains the future; stress tests and expected shortfall alongside (section 9.3).
20. *What goes in a model card for a trading model?* Purpose, data provenance, features and licences, method, assumptions, failure modes, trial ledger summary, monitoring plan, retirement rule (section 11.1).
21. *Fractional differentiation: why?* Stationarity without discarding memory (section 6).
22. *Information coefficient 0.03: good or bad?* Good for a cross-sectional daily signal with breadth; the fundamental law says the information ratio is roughly IC times √breadth (section 6).
23. *How would an LLM leak the future?* Pretraining knowledge of post-period events; corpus edits and restatements; vendor timestamps (section 10.2).
24. *An agent proposes two hundred strategy variants overnight. What do you do with them?* Register them, deflate the best, and read the distribution (section 10.3).
25. *What is adverse selection, and who pays it?* Resting orders fill against informed flow; market makers price it into the spread; passive strategies pay it unpriced (section 2.3).
26. *What is the probability of a losing year at Sharpe 1?* About 16% (section 3.3).
27. *Design the pre-trade risk check.* Synchronous, deterministic, outside the ML stack: exposure, concentration, factor, VaR, order-rate and price-band limits; a kill switch with an owner (section 9.3).
28. *How would you validate a cost model?* Predicted versus realised shortfall by order-size bucket, venue and urgency, monthly (sections 7 and 8).
29. *What is the capacity of a 30 basis-point signal in a 2%-volatility stock?* About 4% of daily volume per trade before costs equal the edge (section 8.2).
30. *Which part of this would you build first?* The bitemporal data platform and the trial ledger, because every other number is only as honest as those two.

## 14. A twelve-week study plan and reading list

| Weeks | Focus | Do |
|---|---|---|
| 1–2 | Markets and microstructure | Harris, *Trading and Exchanges*, parts I–III; extend the order book in section 2 with stop orders and an auction; compute spreads and impact from any free trade-and-quote sample |
| 3–4 | Return statistics and overfitting | Lo, *The Statistics of Sharpe Ratios* (2002); Bailey and López de Prado, *The Deflated Sharpe Ratio* (2014); reproduce section 3 on real daily data for ten stocks; write the trial ledger |
| 5–6 | Data engineering | Build a bitemporal fundamentals table from a free filings source with `known_at`; corporate-action adjustment at read time; a universe table; test lookahead with deliberately injected future values |
| 7–8 | Labels, validation, models | López de Prado, *Advances in Financial Machine Learning*, chapters 3–8; triple-barrier labels, purged cross-validation, sample weights, a regularised linear baseline and a tree ensemble; report the deflated probability |
| 9 | Backtesting and costs | Extend section 7's backtester with participation limits and limit-order fills; validate the vectorised and event-driven versions against each other; implement implementation-shortfall accounting |
| 10 | Portfolio and risk | Grinold and Kahn, chapters 1–6; factor regression, volatility targeting, historical VaR and expected shortfall, pre-trade limits as code |
| 11 | The AI layer | A leakage-safe filing-feature pipeline with cut-off registry, canary test, extraction evaluation against 200 hand labels and a cost-per-document figure |
| 12 | Model risk and the write-up | A model card and monitoring plan in SR 11-7 vocabulary; the write-up with the weakness stated first; the interview bank out loud |

**Reading list.** Harris, *Trading and Exchanges: Market Microstructure for Practitioners* (2003). López de Prado, *Advances in Financial Machine Learning* (2018) and *Machine Learning for Asset Managers* (2020). Grinold and Kahn, *Active Portfolio Management* (2nd ed., 2000). Bouchaud, Bonart, Donier and Gould, *Trades, Quotes and Prices* (2018). Lo, *The Statistics of Sharpe Ratios*, Financial Analysts Journal (2002). Bailey, Borwein, López de Prado and Zhu, *Pseudo-Mathematics and Financial Charlatanism* (2014); Bailey and López de Prado, *The Deflated Sharpe Ratio* (2014); Bailey, Borwein, López de Prado and Zhu, *The Probability of Backtest Overfitting* (2017). Almgren and Chriss, *Optimal Execution of Portfolio Transactions* (2000). Kissell, *The Science of Algorithmic Trading and Portfolio Management* (2013). Kelly, *A New Interpretation of Information Rate* (1956). Board of Governors of the Federal Reserve System, SR 11-7, *Supervisory Guidance on Model Risk Management* (2011). Chan, *Quantitative Trading* (2nd ed., 2021) for a practitioner's on-ramp. In this book: chapter 44.13 (the role), the systematic-trading guide (strategies and research workflow), chapters 63 (token costs), 64 (trace-first debugging), 66 (judges for extraction), 40b (the storage and consistency choices behind the platform).
