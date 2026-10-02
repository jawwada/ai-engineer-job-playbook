# Systematic Trading And Machine Learning: A Complete Guide

Prepared for interview preparation and real system design. Updated May 2026.

This guide is educational, not financial advice. It explains how systematic trading systems are researched, built, validated, and operated, with a special focus on machine learning. Nothing here is a recommendation to trade any asset or deploy any strategy with real capital.

The short version:

```text
Systematic trading is the process of turning market hypotheses into rules,
models, portfolios, execution logic, and risk controls that can be tested
and run consistently.

Machine learning can help discover or combine signals, but it also makes
overfitting easier. In trading, validation and risk control matter as much
as model accuracy.
```

## 1. What Systematic Trading Is

Systematic trading uses explicit rules, models, and data pipelines to make trading decisions.

It is different from discretionary trading:

| Discretionary Trading | Systematic Trading |
| --- | --- |
| human judgment makes final decisions | algorithm/model makes decisions |
| harder to reproduce | rules are explicit |
| narrative-driven | data and process-driven |
| often flexible | often more scalable |
| hard to backtest precisely | designed for historical simulation |

Systematic trading does not mean fully automated high-frequency trading. A systematic strategy can rebalance monthly, weekly, daily, intraday, or microsecond-level.

Examples:

- monthly factor portfolio
- daily futures trend following
- intraday equity mean reversion
- statistical arbitrage pairs trading
- market making
- options volatility strategy
- crypto funding-rate strategy
- news sentiment strategy
- execution algorithm

## 2. The Core Trading System Loop

A systematic trading operation has a loop:

```text
research idea
  -> data collection
  -> feature engineering
  -> signal/model
  -> backtest
  -> transaction cost model
  -> portfolio construction
  -> risk controls
  -> paper trading
  -> production deployment
  -> monitoring
  -> post-trade analysis
  -> iteration
```

A trading strategy is not just a predictive model. It is:

```text
prediction + sizing + costs + constraints + execution + risk + monitoring
```

Good interview line:

> A model with good prediction accuracy can still be a bad trading strategy if turnover, costs, capacity, drawdowns, or implementation constraints destroy the edge.

## 3. Core Terminology

| Term | Meaning |
| --- | --- |
| Alpha | Expected excess return from a signal or strategy |
| Signal | Numeric estimate of future return, risk, or trade desirability |
| Feature | Input variable used by a model |
| Label | Target variable the model tries to predict |
| Horizon | Future period being predicted or traded |
| Universe | Set of tradable assets considered |
| Position | Quantity or weight held in an asset |
| Exposure | Sensitivity to asset, sector, factor, country, currency, beta, etc. |
| Leverage | Gross exposure divided by equity |
| Turnover | How much portfolio changes over time |
| Slippage | Difference between expected and actual execution price |
| Spread | Difference between best ask and best bid |
| Market impact | Price movement caused by your own trading |
| Capacity | Maximum capital a strategy can manage before performance degrades |
| Drawdown | Decline from peak equity to trough |
| Sharpe ratio | excess return per unit volatility |
| Information ratio | active return divided by tracking error |
| Backtest | historical simulation of a strategy |
| Walk-forward validation | repeated train/test over time |
| Lookahead bias | using future information accidentally |
| Survivorship bias | ignoring assets that disappeared |
| Regime | market environment with different dynamics |
| OMS | order management system |
| EMS | execution management system |
| Kill switch | emergency shutdown control for trading |

## 4. The Reality Of Financial ML

Financial machine learning is unusually hard because markets are:

- noisy
- nonstationary
- adversarial
- low signal-to-noise
- heavily arbitraged
- affected by costs and liquidity
- prone to regime shifts
- vulnerable to backtest overfitting

Common ML intuition fails:

```text
A tiny predictive edge can be valuable if cheap, scalable, and diversified.
A high-accuracy model can be useless if it trades too much or predicts the wrong tail.
```

In many trading problems, the signal is weak:

```text
R^2 may be tiny.
Hit rate may be barely above 50%.
Profitability comes from sizing, diversification, cost control, and repetition.
```

## 5. Strategy Families

### 5.1 Trend Following / Momentum

Hypothesis:

```text
Assets that have been rising tend to keep rising for some horizon.
Assets that have been falling tend to keep falling.
```

Common features:

- past returns
- moving average crossovers
- breakout signals
- time-series momentum
- cross-sectional momentum
- volatility scaling

Why it can work:

- investor underreaction
- slow information diffusion
- behavioral herding
- risk premia

Risks:

- sharp reversals
- crowding
- high turnover
- poor performance in choppy markets

### 5.2 Mean Reversion

Hypothesis:

```text
Short-term price moves can overshoot and partially reverse.
```

Common features:

- z-score of recent return
- deviation from moving average
- residual from factor model
- order book imbalance
- spread widening

Works best when:

- transaction costs are low
- market is liquid
- horizon is short
- signal is not overwhelmed by trend

Risks:

- catching falling knives
- regime shift
- stale prices
- borrow constraints
- execution costs

### 5.3 Statistical Arbitrage

Uses statistical relationships across assets.

Examples:

- pairs trading
- cointegration baskets
- sector-neutral equity stat arb
- ETF vs constituents
- factor residual mean reversion

Typical structure:

```text
model fair value relationship
compute residual
trade residual convergence
control factor exposures
```

Risks:

- relationship breaks
- crowded exits
- liquidity shock
- hidden factor exposure

### 5.4 Factor Investing

Factors are systematic characteristics associated with return or risk.

Examples:

- value
- momentum
- quality
- low volatility
- size
- carry
- profitability
- investment

ML can combine factors, forecast factor returns, or detect nonlinear interactions.

Risks:

- factor crowding
- decay
- unintended exposures
- data mining

### 5.5 Market Making

Market makers post bids and asks, earning spread while managing inventory risk.

Core problem:

```text
quote prices and sizes
manage inventory
avoid adverse selection
control latency and risk
```

ML use:

- short-term price movement prediction
- order book imbalance
- fill probability
- adverse selection prediction
- dynamic spread setting
- inventory-aware quoting

Risks:

- latency disadvantage
- toxic flow
- inventory accumulation
- exchange outages
- fee/rebate changes

### 5.6 Execution Algorithms

Execution strategies minimize implementation cost for a desired trade.

Examples:

- TWAP
- VWAP
- POV
- implementation shortfall
- adaptive execution
- liquidity-seeking algos

ML use:

- volume prediction
- short-term impact prediction
- fill probability
- venue selection
- child-order scheduling

Execution is often where a paper alpha becomes real or disappears.

### 5.7 Options And Volatility Strategies

Hypotheses:

- implied volatility differs from expected realized volatility
- volatility risk premium exists
- skew/term structure contain information
- hedging flows create predictable effects

ML use:

- realized volatility forecasting
- implied volatility surface modeling
- option mispricing detection
- delta/vega/gamma risk management

Risks:

- tail events
- liquidity
- model risk
- volatility jumps
- margin/funding

### 5.8 Event-Driven And Alternative Data

Events:

- earnings
- M&A
- product launches
- macro announcements
- regulatory decisions
- corporate actions
- supply chain shocks

Alternative data:

- news
- social media
- web traffic
- satellite imagery
- credit card data
- shipping data
- job postings
- app rankings

ML is often useful here, especially NLP and cross-sectional ranking.

Risks:

- data licensing
- privacy/compliance
- short history
- changing data collection process
- false causal stories

## 6. Data Types

### 6.1 Market Data

Common fields:

- open
- high
- low
- close
- volume
- bid/ask
- trades
- quotes
- order book depth
- auction data

Watch out for:

- split/dividend adjustments
- bad ticks
- stale quotes
- exchange holidays
- timezone normalization
- consolidated vs direct feeds
- survivorship bias
- delisted assets

### 6.2 Fundamental Data

Examples:

- revenue
- earnings
- balance sheet
- cash flow
- margins
- debt
- analyst estimates
- guidance

Must be point-in-time:

```text
Use only the value known on that date, not the restated value from later.
```

### 6.3 Corporate Actions

Examples:

- splits
- dividends
- mergers
- spin-offs
- symbol changes
- delistings

Corporate action handling can make or break equity backtests.

### 6.4 Options Data

Fields:

- implied volatility
- delta
- gamma
- vega
- theta
- open interest
- volume
- bid/ask
- strike
- expiry

Need careful handling of:

- surface interpolation
- stale quotes
- early exercise
- dividends
- liquidity filters

### 6.5 Order Book Data

Limit order book data includes bid/ask levels and quantities.

Features:

- spread
- depth
- imbalance
- order flow
- cancellations
- microprice
- queue position

This is useful for high-frequency prediction and execution, but storage and simulation are difficult.

### 6.6 Text And News

Sources:

- news
- filings
- earnings calls
- transcripts
- social media
- central bank statements
- analyst reports

ML use:

- sentiment
- event extraction
- topic modeling
- surprise detection
- summarization
- entity linking

LLMs are useful for text understanding, but the final trading signal still needs point-in-time data, validation, cost modeling, and risk control.

## 7. Data Engineering Pitfalls

### 7.1 Lookahead Bias

Using future data accidentally.

Examples:

- today's close used for a trade assumed at today's open
- financial statement used before release date
- index membership list from today used in 2015
- feature standardization using full-sample mean

Fix:

```text
every feature must have an as-of timestamp
```

### 7.2 Survivorship Bias

If your universe contains only assets that exist today, you exclude bankrupt/delisted assets.

This inflates historical performance.

Fix:

- use survivorship-free databases
- include delisted securities
- model delisting returns

### 7.3 Selection Bias

You test many ideas and only remember the winners.

Fix:

- track all experiments
- adjust for multiple testing
- use deflated Sharpe/probabilistic Sharpe
- require economic rationale
- reserve untouched holdout periods

### 7.4 Data Snooping

Repeatedly tuning on the same backtest creates false discoveries.

Fix:

- walk-forward validation
- purged cross-validation
- combinatorial purged cross-validation
- final holdout
- paper trading

### 7.5 Revision Bias

Some data is revised after first publication.

Examples:

- macroeconomic data
- fundamentals
- analyst estimates
- corporate classifications

Use data vintage known at the time.

### 7.6 Liquidity Bias

A strategy may appear profitable in illiquid assets but cannot execute at assumed prices.

Fix:

- volume constraints
- spread filters
- participation limits
- impact model
- capacity analysis

## 8. Machine Learning Problem Formulation

### 8.1 Predict Returns

Regression target:

```text
future_return = price_{t+h} / price_t - 1
```

Pros:

- direct
- intuitive

Cons:

- noisy
- heavy-tailed
- unstable

### 8.2 Predict Direction

Classification target:

```text
1 if future_return > threshold else 0
```

Pros:

- simple
- aligns with long/short decision

Cons:

- ignores magnitude
- class imbalance
- small positive returns may not beat costs

### 8.3 Rank Assets

Cross-sectional ranking:

```text
rank assets by expected future return
long top decile
short bottom decile
```

Often more stable than predicting exact returns.

Metrics:

- Spearman rank IC
- top-bottom spread
- portfolio return

### 8.4 Predict Risk

Targets:

- volatility
- drawdown risk
- tail risk
- probability of gap
- liquidity risk

Risk prediction is often more stable than return prediction.

### 8.5 Predict Execution Outcomes

Targets:

- fill probability
- market impact
- short-term price movement
- spread capture
- adverse selection

This is a major ML application even when alpha is human-designed.

## 9. Labeling Methods

### 9.1 Fixed-Horizon Labels

Example:

```text
label_t = return from t to t+5 days
```

Simple but may ignore path risk.

### 9.2 Threshold Labels

Example:

```text
buy if future return > 50 bps
sell if future return < -50 bps
hold otherwise
```

Better aligned with costs.

### 9.3 Triple-Barrier Labels

Triple-barrier labeling uses:

- profit-taking barrier
- stop-loss barrier
- time barrier

Label is determined by which barrier is hit first.

Why useful:

- incorporates path
- accounts for asymmetric outcomes
- avoids pretending all fixed-horizon returns are equal

### 9.4 Meta-Labeling

Meta-labeling separates:

```text
primary model: should we consider a trade?
meta model: should we take this trade / how size it?
```

Useful when:

- you have a rule-based signal
- ML is better at filtering false positives than generating trades from scratch

### 9.5 Overlapping Labels

If you label 20-day future returns every day, labels overlap heavily.

This creates dependence and leakage in cross-validation.

Fix:

- purging
- embargo
- non-overlapping samples
- careful standard errors

## 10. Feature Engineering

### 10.1 Price And Return Features

Examples:

- returns over multiple horizons
- volatility
- realized skew/kurtosis
- moving average distance
- breakout distance
- drawdown
- gap size
- intraday range

### 10.2 Cross-Sectional Features

Examples:

- rank of momentum within universe
- sector-relative value
- residual return after factor neutralization
- percentile of volume
- relative volatility

Cross-sectional normalization is common:

```text
for each date:
  z-score feature across assets
```

### 10.3 Liquidity Features

Examples:

- average dollar volume
- bid/ask spread
- turnover
- Amihud illiquidity
- order book depth
- volume participation

### 10.4 Fundamental Features

Examples:

- earnings yield
- book-to-market
- revenue growth
- gross profitability
- leverage
- accruals
- estimate revisions

Need:

- point-in-time values
- reporting lags
- restatement handling

### 10.5 Microstructure Features

Examples:

- order book imbalance
- trade sign imbalance
- queue imbalance
- spread
- microprice
- cancellation rate
- aggressive buy/sell volume

Common at intraday/high-frequency horizons.

### 10.6 Text Features

Examples:

- sentiment
- novelty
- topic
- named entities
- event type
- uncertainty
- management tone
- central-bank hawkish/dovish score

LLM-based text features should be:

- timestamped
- cached
- audited
- evaluated for drift
- checked for data licensing

## 11. Models For Trading

### 11.1 Linear Models

Models:

- linear regression
- logistic regression
- ridge
- lasso
- elastic net

Pros:

- interpretable
- stable
- fast
- less prone to extreme overfit

Good for:

- factor models
- baseline prediction
- exposure control
- sparse features

### 11.2 Tree Ensembles

Models:

- random forest
- XGBoost
- LightGBM
- CatBoost

Pros:

- strong on tabular data
- nonlinear interactions
- handles mixed feature types
- robust baseline

Cons:

- can overfit subtly
- predictions may be unstable across regimes
- not naturally time-aware

### 11.3 Time-Series Models

Models:

- ARIMA/GARCH
- Kalman filters
- hidden Markov models
- state-space models

Use for:

- volatility
- regime detection
- spread modeling
- dynamic hedge ratios

### 11.4 Deep Learning

Models:

- MLPs
- CNNs
- LSTMs/GRUs
- TCNs
- transformers
- temporal fusion transformers
- DeepLOB-style architectures for order books

Pros:

- can learn complex nonlinear patterns
- useful for order book/image-like data
- can model sequences directly

Cons:

- data hungry
- fragile
- hard to validate
- easy to overfit
- expensive to retrain

### 11.5 Graph Neural Networks

Use graphs for:

- company relationships
- supply chains
- sector/industry links
- ownership networks
- correlation networks
- option-underlying relationships

Risk:

- graph construction can leak future information
- relationships change over time

### 11.6 Reinforcement Learning

RL can be used for:

- execution
- market making
- dynamic hedging
- inventory control
- position sizing

It is harder for:

- discovering robust long-horizon alpha from price data

Reasons:

- simulator mismatch
- nonstationary environment
- sparse rewards
- market impact feedback
- exploration is expensive in live markets

Good practical RL use:

```text
constrained control problem with a realistic simulator
```

Not:

```text
let an RL agent discover free money from OHLCV data
```

### 11.7 LLMs In Trading

LLMs are useful for:

- parsing filings/transcripts
- classifying news events
- sentiment extraction
- summarizing risk factors
- normalizing messy text
- analyst workflow automation
- generating research hypotheses
- compliance surveillance support

LLMs are not automatically reliable alpha generators.

Requirements:

- point-in-time text
- no leakage from future articles
- timestamp alignment
- human review for labels
- cost/latency analysis
- robustness checks

## 12. Model Training And Validation

### 12.1 Why Standard ML Cross-Validation Fails

Random k-fold assumes samples are independent and identically distributed.

Financial data is:

- time ordered
- autocorrelated
- overlapping
- regime-dependent
- cross-sectionally correlated

Random splits leak future information.

### 12.2 Walk-Forward Validation

Example:

```text
train 2010-2016 -> test 2017
train 2010-2017 -> test 2018
train 2010-2018 -> test 2019
```

This simulates real deployment.

### 12.3 Rolling Window Validation

Example:

```text
train last 3 years -> test next month
slide forward
```

Useful when old data becomes irrelevant.

### 12.4 Purging And Embargo

Purging removes training samples whose labels overlap the test period.

Embargo removes samples just after the test period to avoid leakage through overlap.

Use when:

- labels have holding periods
- outcomes overlap
- features include rolling windows

### 12.5 Combinatorial Purged Cross-Validation

CPCV tests many train/test splits while respecting temporal leakage constraints.

Why:

- estimates robustness across paths
- helps assess backtest overfitting
- better than one lucky split

### 12.6 Hyperparameter Tuning

Use nested validation when possible:

```text
inner loop: tune model
outer loop: estimate performance
```

Do not tune repeatedly on the final holdout.

### 12.7 Probability Calibration

If model outputs probabilities, check calibration.

Metrics:

- Brier score
- log loss
- reliability curve
- expected calibration error

Trading relevance:

```text
Position sizing depends on probability quality.
A poorly calibrated classifier can size trades badly even with decent ranking.
```

## 13. Backtesting

### 13.1 What A Backtest Must Simulate

At minimum:

- data available at time of decision
- signal computation
- order generation
- execution price
- transaction costs
- slippage
- spread
- market impact
- borrow/funding costs
- cash and margin
- rebalancing
- corporate actions
- risk limits

### 13.2 Vectorized Backtests

Fast array-based simulations.

Pros:

- quick research
- simple strategies
- good first pass

Cons:

- can hide execution assumptions
- weak for intraday/order-level strategies
- easy to leak future data

### 13.3 Event-Driven Backtests

Simulate events:

- market data tick/bar
- signal
- order
- fill
- portfolio update

Pros:

- more realistic
- closer to production
- handles intraday/execution logic

Cons:

- slower
- more engineering

### 13.4 Research Backtest vs Production Simulator

Research backtest:

```text
fast, approximate, idea screening
```

Production simulator:

```text
slower, realistic, used before deployment
```

Do not let a research backtest be the only gate before live trading.

## 14. Transaction Costs And Slippage

Transaction costs include:

- commissions
- exchange fees
- broker fees
- bid/ask spread
- market impact
- borrow cost
- financing
- taxes
- short locate fees

### 14.1 Spread Cost

Crossing the spread costs money.

Example:

```text
mid = 100.00
bid = 99.99
ask = 100.01
market buy likely pays 100.01
```

### 14.2 Market Impact

Your own order moves the price.

Impact depends on:

- order size
- volume
- volatility
- liquidity
- urgency
- participation rate

### 14.3 Implementation Shortfall

Implementation shortfall measures:

```text
actual execution performance vs decision price
```

It includes delay, spread, impact, and opportunity cost.

### 14.4 Capacity

Capacity is the amount of capital a strategy can run before costs degrade edge.

Questions:

- What percent of daily volume do we trade?
- How much turnover?
- How concentrated are positions?
- Does alpha decay with size?
- Does execution create adverse selection?

Many strategies fail not because alpha is false, but because it is too small or crowded after costs.

## 15. Portfolio Construction

Signals must become positions.

### 15.1 Simple Ranking Portfolio

Example:

```text
long top decile by score
short bottom decile by score
equal weight within each side
```

Good baseline.

### 15.2 Score-To-Weight Mapping

Methods:

- sign only
- rank-based weights
- z-score proportional weights
- volatility-adjusted weights
- expected-return / covariance optimization
- constrained optimization

### 15.3 Risk Model

A risk model estimates portfolio variance and exposures.

Components:

- factor exposures
- factor covariance
- idiosyncratic risk
- beta
- sector/country/currency exposure

### 15.4 Mean-Variance Optimization

Classic objective:

```text
maximize expected return - risk penalty - cost penalty
```

Problem:

- expected returns are noisy
- optimizer can create extreme weights

Practical fixes:

- constraints
- shrinkage
- robust covariance
- turnover penalty
- exposure constraints
- weight caps

### 15.5 Risk Parity

Risk parity allocates so assets or strategies contribute similar risk.

Useful when:

- return forecasts are unreliable
- diversification is the main goal

Risk:

- ignores expected returns unless modified
- can over-allocate to low-vol assets
- can use leverage

### 15.6 Kelly Sizing

Kelly maximizes expected log growth when edge and odds are known.

Problem:

```text
in trading, edge estimates are uncertain
```

Practical use:

- fractional Kelly
- caps
- drawdown constraints
- stress tests

Full Kelly is usually too aggressive with noisy estimates.

### 15.7 Volatility Targeting

Adjust exposure to target a volatility level.

Example:

```text
target_vol = 10%
position_scale = target_vol / estimated_vol
```

Useful for:

- stabilizing risk
- comparing strategies
- drawdown control

Risks:

- volatility estimate lag
- deleveraging after losses
- leverage in calm regimes

## 16. Risk Management

Risk management is not optional. It is part of the strategy.

### 16.1 Market Risk

Controls:

- gross exposure
- net exposure
- beta exposure
- sector exposure
- country/currency exposure
- volatility target
- VaR / expected shortfall
- drawdown limit

### 16.2 Liquidity Risk

Controls:

- max percent ADV
- min volume
- max spread
- liquidation horizon
- participation cap

### 16.3 Concentration Risk

Controls:

- max position size
- issuer limits
- sector limits
- strategy limits
- correlated exposure limits

### 16.4 Model Risk

Controls:

- independent review
- challenger models
- sensitivity tests
- stress scenarios
- feature stability checks
- kill criteria

### 16.5 Operational Risk

Controls:

- pre-trade checks
- order throttles
- fat-finger limits
- duplicate order protection
- position reconciliation
- heartbeat monitoring
- kill switch
- disaster recovery

SEC and FINRA guidance for algorithmic trading emphasizes risk controls, testing, supervision, and change management.

## 17. Evaluation Metrics

### 17.1 Prediction Metrics

Use when evaluating ML models before trading:

| Metric | Use |
| --- | --- |
| MSE/MAE | return regression |
| accuracy | direction classification, often insufficient |
| precision/recall | rare event prediction |
| AUC | ranking binary outcomes |
| log loss | probability quality |
| Brier score | probability calibration |
| Spearman rank IC | cross-sectional ranking quality |
| Pearson IC | linear correlation between signal and future returns |
| top-bottom spread | economic separation between ranked groups |

Prediction metrics are not enough. Always test strategy P&L after costs.

### 17.2 Trading Metrics

| Metric | Meaning |
| --- | --- |
| CAGR | annualized compound growth |
| annualized volatility | return variability |
| Sharpe ratio | excess return / volatility |
| Sortino ratio | return / downside volatility |
| Calmar ratio | return / max drawdown |
| max drawdown | worst peak-to-trough loss |
| hit rate | percent profitable trades |
| profit factor | gross profit / gross loss |
| turnover | trading activity |
| average holding period | typical trade duration |
| exposure | capital at risk |
| beta | market sensitivity |
| alpha | residual return after risk factors |
| information ratio | active return / tracking error |
| VaR / expected shortfall | tail risk |

### 17.3 Backtest Robustness Metrics

Use:

- Sharpe t-stat
- probabilistic Sharpe ratio
- deflated Sharpe ratio
- probability of backtest overfitting
- performance by regime
- rolling Sharpe
- drawdown duration
- sensitivity to costs
- sensitivity to delays
- bootstrap confidence intervals

### 17.4 Execution Metrics

Use:

- implementation shortfall
- arrival price slippage
- VWAP slippage
- fill rate
- adverse selection
- market impact
- participation rate
- cancel/replace rate
- venue performance

## 18. Backtest Overfitting

Backtest overfitting is the central disease of systematic trading.

It happens when a strategy is tuned to historical noise.

Symptoms:

- great in-sample, bad out-of-sample
- fragile to parameter changes
- performance concentrated in few trades
- only works on one universe
- collapses after costs
- too many filters
- no economic rationale

Mitigations:

- simple models first
- out-of-sample validation
- walk-forward testing
- purged/embargoed CV
- multiple-testing correction
- deflated Sharpe ratio
- paper trading
- stress costs and delays
- require economic rationale
- track all failed experiments

## 19. Research Workflow

### Step 1: Hypothesis

Good:

```text
Stocks with strong estimate revisions may continue to drift because investors underreact to analyst information.
```

Bad:

```text
XGBoost will find alpha in these 500 indicators.
```

### Step 2: Data Audit

Check:

- point-in-time availability
- survivorship
- missing data
- corporate actions
- universe construction
- timestamp alignment
- data licensing

### Step 3: Baseline

Build simple baselines:

- equal weight
- buy and hold
- simple momentum
- linear model
- seasonal/known factor benchmark

### Step 4: Model

Train model using leakage-safe validation.

### Step 5: Backtest With Costs

Include realistic transaction costs and constraints.

### Step 6: Robustness

Stress:

- costs 2x/3x
- delayed execution
- different universes
- different periods
- different volatility regimes
- parameter perturbations
- capacity scaling

### Step 7: Paper Trade

Run live without capital or with tiny capital.

Measure:

- signal generation
- data latency
- execution assumptions
- slippage
- outages
- monitoring

### Step 8: Controlled Deployment

Deploy gradually:

- small allocation
- tight risk limits
- monitoring
- kill switch
- post-trade review

## 20. Production Architecture

### 20.1 Research Stack

```text
raw data lake
  -> cleaned point-in-time datasets
  -> feature store
  -> model training
  -> backtest engine
  -> experiment tracking
  -> research reports
```

### 20.2 Trading Stack

```text
market data
  -> feature computation
  -> signal/model inference
  -> portfolio optimizer
  -> risk checks
  -> order generation
  -> OMS/EMS
  -> broker/exchange
  -> fills
  -> position/risk reconciliation
  -> monitoring
```

### 20.3 Required Controls

Controls:

- pre-trade risk checks
- max order size
- max notional
- max participation
- price collars
- duplicate order checks
- fat-finger checks
- kill switch
- audit trail
- code review
- model versioning
- data versioning
- production change approval

## 21. Monitoring

Monitor:

- P&L
- exposure
- drawdown
- turnover
- slippage
- fill rate
- borrow cost
- factor exposure
- signal distribution
- feature drift
- model prediction drift
- data feed health
- order rejects
- latency
- reconciliation breaks

Alert on:

- abnormal position
- abnormal order rate
- missing data
- stale model
- feature out of range
- risk limit breach
- strategy P&L beyond expected distribution

## 22. ML-Specific Monitoring

Track:

- feature drift
- label drift
- prediction distribution
- calibration drift
- IC decay
- performance by bucket
- performance by regime
- feature importance stability
- model confidence vs outcome
- live vs backtest slippage

A model can fail even if infrastructure works perfectly.

## 23. LLMs And Alternative Data In Modern Trading

### 23.1 Useful LLM Applications

LLMs can help with:

- extracting structured data from filings
- summarizing earnings calls
- detecting tone changes
- classifying news events
- mapping entities to tickers
- building knowledge graphs
- compliance surveillance
- research assistant workflows
- generating hypotheses for human testing

### 23.2 Risky LLM Applications

Be careful with:

- direct trading recommendations
- unverified sentiment scores
- hallucinated facts
- future leakage through pretrained knowledge
- non-point-in-time datasets
- changing model behavior after provider updates

### 23.3 Safe Pattern

```text
LLM extracts or classifies text
  -> output is timestamped and validated
  -> feature enters normal ML/backtest pipeline
  -> strategy evaluated after costs
```

Do not let an LLM bypass the research and risk framework.

## 24. Reinforcement Learning In Trading

RL is appealing but dangerous.

### 24.1 Good RL Use Cases

Better:

- execution scheduling
- market making inventory control
- dynamic hedging
- order placement under constraints

Why:

- action space can be constrained
- simulator can be built
- objective is operational

### 24.2 Weak RL Use Cases

Risky:

- "learn to trade from price charts"
- unconstrained portfolio trading
- long-horizon alpha discovery

Problems:

- simulator mismatch
- reward hacking
- nonstationary markets
- unrealistic fills
- high variance
- overfit policies

### 24.3 RL Design Requirements

Need:

- realistic simulator
- transaction costs
- market impact
- risk limits
- position constraints
- train/test split over regimes
- out-of-sample paper trading
- safety layer outside the RL policy

## 25. Compliance And Governance

Trading systems operate in regulated environments.

Important governance topics:

- algorithm approval
- code review
- testing evidence
- change management
- audit logs
- supervision
- market access controls
- trade surveillance
- model risk management
- data licensing
- privacy
- insider information controls

In U.S. securities markets, relevant references include SEC market access risk controls, Regulation SCI for certain market entities, and FINRA guidance on algorithmic trading supervision. Exact obligations depend on firm type, jurisdiction, asset class, and role.

## 26. Applications Of ML In Trading

| Area | ML Use |
| --- | --- |
| equity alpha | rank stocks by expected return |
| futures trend | regime detection, volatility scaling |
| stat arb | residual prediction, basket construction |
| options | volatility surface modeling, realized vol forecasting |
| market making | fill/adverse selection prediction |
| execution | schedule orders, venue selection |
| risk | volatility, tail risk, drawdown prediction |
| portfolio | covariance estimation, clustering, allocation |
| news | sentiment, event extraction, novelty |
| compliance | surveillance, anomaly detection |
| operations | reconciliation anomaly detection |

## 27. Common Failure Modes

| Failure | Symptom | Fix |
| --- | --- | --- |
| lookahead bias | live performance far worse | point-in-time pipeline |
| survivorship bias | impossible historical returns | survivorship-free universe |
| overfitting | fragile parameters | purged CV, holdout, simplicity |
| ignored costs | paper alpha disappears | realistic cost model |
| capacity failure | alpha decays with size | impact/capacity analysis |
| hidden beta | strategy profits only in bull market | factor regression, neutralization |
| data revision bias | macro/fundamental strategy fails | data vintage control |
| bad labels | model predicts untradeable target | cost-aware labels |
| uncalibrated probabilities | bad sizing | calibration and sizing caps |
| regime shift | model stops working | monitoring, adaptive risk |
| model leakage | suspiciously high accuracy | feature timestamp audit |
| LLM hallucination | false text features | validation, source checks |
| RL simulator gap | policy fails live | realistic simulator and constraints |

## 28. Practical Checklist

Before trusting a strategy:

1. Is the hypothesis economically plausible?
2. Is all data point-in-time?
3. Is the universe survivorship-free?
4. Are corporate actions handled?
5. Are labels aligned with trade timing?
6. Is validation time-aware?
7. Are overlapping labels purged?
8. Are costs realistic?
9. Is capacity estimated?
10. Does it beat simple baselines?
11. Is performance robust by regime?
12. Does it survive parameter perturbation?
13. Are factor exposures understood?
14. Is drawdown acceptable?
15. Are production risk controls defined?
16. Is there a paper-trading period?
17. Is there a kill switch?
18. Are all experiments logged?

## 29. Interview-Ready Answers

### "How would you build a systematic trading strategy?"

```text
I would start with an economic hypothesis, then build a point-in-time dataset and a simple baseline. I would define labels that match the trading horizon and costs, train a model with walk-forward or purged cross-validation, and backtest with realistic transaction costs, slippage, borrow, and capacity constraints. Then I would convert signals to positions through portfolio construction and risk limits, paper trade it, monitor live drift and slippage, and deploy gradually with kill switches and audit logs.
```

### "Why is ML hard in trading?"

```text
Financial data is noisy, nonstationary, and low signal-to-noise. Labels overlap, markets adapt, and costs can erase small edges. Standard random cross-validation leaks information. A model can have good prediction metrics but still fail after turnover, market impact, drawdowns, and capacity constraints.
```

### "What is purged cross-validation?"

```text
Purged cross-validation removes training samples whose label periods overlap the test period, and embargoes nearby samples to reduce leakage. It is useful because financial labels often overlap in time, such as 20-day forward returns computed every day.
```

### "What metrics matter?"

```text
For prediction, I look at IC, rank IC, log loss, Brier score, AUC, or top-bottom spread depending on the task. For trading, I care more about after-cost Sharpe, drawdown, turnover, capacity, exposure, information ratio, slippage, and robustness across regimes. Prediction metrics are only useful if they translate to economic P&L after costs.
```

### "How do you avoid backtest overfitting?"

```text
Use point-in-time data, realistic costs, walk-forward testing, purged/embargoed cross-validation, untouched holdout periods, experiment tracking, multiple-testing adjustments like deflated Sharpe, stress tests, parameter sensitivity, paper trading, and a requirement for economic rationale.
```

### "Where can ML help most?"

```text
ML is useful for cross-sectional ranking, combining weak signals, nonlinear tabular patterns, risk forecasting, execution, order book prediction, text/event extraction, and trade filtering through meta-labeling. It is less reliable as a magic alpha generator from raw prices alone.
```

## 30. Quick Glossary

| Term | Short Meaning |
| --- | --- |
| alpha | expected excess return |
| signal | score used to make a trade decision |
| label | future outcome predicted by model |
| IC | correlation between signal and future return |
| rank IC | Spearman rank correlation |
| turnover | portfolio trading activity |
| slippage | execution price loss vs benchmark |
| market impact | price movement caused by trade |
| capacity | capital limit before edge degrades |
| Sharpe | return per volatility |
| Sortino | return per downside volatility |
| drawdown | peak-to-trough loss |
| VaR | value at risk |
| expected shortfall | average loss beyond VaR |
| purging | removing overlapping training labels |
| embargo | gap around test period to avoid leakage |
| meta-labeling | ML model filters/sizes primary signals |
| triple barrier | label using profit, loss, and time barriers |
| implementation shortfall | execution cost vs decision price |
| OMS | order management system |
| EMS | execution management system |

## 31. References

- Financial ML/backtesting: [The Probability of Backtest Overfitting](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253)
- Deflated Sharpe ratio: [The Deflated Sharpe Ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- Financial ML book reference: [Advances in Financial Machine Learning](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086)
- Lopez de Prado overview: [The 7 Reasons Most Machine Learning Funds Fail](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101)
- Execution theory: [Optimal Execution of Portfolio Transactions](https://www.math.nyu.edu/~almgren/papers/optliq.pdf)
- Market impact and implementation shortfall: [Implementation Shortfall](https://www.jstor.org/stable/4479403)
- Deep order book learning: [DeepLOB: Deep Convolutional Neural Networks for Limit Order Books](https://arxiv.org/abs/1808.03668)
- Market making foundation: [High-frequency trading in a limit order book](https://www.researchgate.net/publication/24086205_High-frequency_trading_in_a_limit_order_book)
- DPO/ML not trading-specific but useful for preference learning context: [Direct Preference Optimization](https://arxiv.org/abs/2305.18290)
- BloombergGPT: [BloombergGPT: A Large Language Model for Finance](https://arxiv.org/abs/2303.17564)
- FinGPT: [FinGPT: Open-Source Financial Large Language Models](https://arxiv.org/abs/2306.06031)
- SEC market access controls: [Risk Management Controls for Brokers or Dealers With Market Access](https://www.sec.gov/rules-regulations/2011/06/risk-management-controls-brokers-or-dealers-market-access)
- SEC Regulation SCI: [Regulation Systems Compliance and Integrity](https://www.sec.gov/rules-regulations/2015/12/regulation-systems-compliance-integrity)
- FINRA algorithmic trading guidance: [Regulatory Notice 15-09](https://www.finra.org/rules-guidance/notices/15-09)
- FINRA algorithmic trading topic page: [Algorithmic Trading](https://www.finra.org/rules-guidance/key-topics/algorithmic-trading)

