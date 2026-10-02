# Modern Time-Series Forecasting: Complete Guide

Prepared for interview preparation and real system design. Updated May 2026.

This guide covers modern time-series forecasting: classical methods, machine learning, deep learning, foundation models, probabilistic forecasting, calibration, evaluation metrics, backtesting, hierarchical reconciliation, applications, and production design.

The short version:

```text
Forecasting is not just predicting the next value.
It is estimating future uncertainty well enough to make better decisions.
```

## 1. What Time-Series Forecasting Is

Time-series forecasting predicts future values of a variable observed over time.

Examples:

- sales next week
- electricity load tomorrow
- CPU utilization in 10 minutes
- demand for a product next month
- hospital admissions next quarter
- cash flow next year
- weather variables over the next 10 days

The input is ordered in time:

```text
y_1, y_2, ..., y_t
```

The forecast asks for:

```text
y_{t+1}, y_{t+2}, ..., y_{t+h}
```

where `h` is the forecast horizon.

## 2. The Most Important Forecasting Mindset

A forecast is useful only relative to a decision.

Before choosing a model, ask:

- What decision will the forecast support?
- What horizon matters?
- Is under-forecasting worse than over-forecasting?
- Do we need a point forecast, quantiles, or full distribution?
- How often will forecasts be updated?
- What data is known at prediction time?
- What is the cost of latency?
- What level of aggregation matters?

Example:

```text
Inventory planning does not need only "expected demand."
It needs uncertainty, lead time, service level, stockout cost, and holding cost.
```

## 3. Core Terminology

| Term | Meaning |
| --- | --- |
| Time series | Sequence of observations ordered by time |
| Forecast horizon | Number of future time steps predicted |
| Forecast origin | Time point from which forecast is made |
| Lead time | Operational delay between decision and effect |
| Frequency | Time interval between observations, such as hourly, daily, monthly |
| Seasonality | Repeating pattern at fixed period, such as daily or weekly |
| Trend | Long-term directional movement |
| Cyclicality | Non-fixed-period repeated movement, often macro/business cycle |
| Noise | Unpredictable random variation |
| Exogenous variable | External feature used to forecast target |
| Covariate | Another name for input feature |
| Static covariate | Feature fixed for a series, such as store region |
| Past covariate | Feature observed historically but unknown in future |
| Future covariate | Feature known for forecast horizon, such as calendar holidays |
| Target | Variable being forecast |
| Univariate forecasting | Forecast one variable from its own history |
| Multivariate forecasting | Forecast using multiple related variables |
| Global model | One model trained across many related time series |
| Local model | Separate model per time series |
| Hierarchical forecasting | Forecast series that aggregate across levels |
| Probabilistic forecast | Forecast distribution or quantiles, not just one value |
| Prediction interval | Range intended to contain future value with specified probability |
| Calibration | Whether forecast uncertainty matches observed frequencies |
| Sharpness | How narrow or concentrated a probabilistic forecast is |
| Backtesting | Historical simulation of forecasting performance |
| Leakage | Using information that would not be available at prediction time |

## 4. The Modern State Of The Field

Forecasting in 2026 is a pluralistic field. There is no single best model.

The modern stack looks like this:

```text
Classical statistical models:
  ARIMA, ETS, STL, Theta, Prophet, state-space models

Feature-based ML:
  lag/rolling/calendar features + LightGBM/XGBoost/CatBoost

Deep forecasting:
  DeepAR, N-BEATS, N-HiTS, TFT, PatchTST, TCNs, diffusion/state-space models

Foundation models:
  Chronos, TimesFM, Moirai, Lag-Llama, TimeGPT, MOMENT, Sundial, Timer, TinyTimeMixer, Chronos-2

Forecast systems:
  ensembles, reconciliation, conformal calibration, monitoring, human override
```

The practical state of the art is often an ensemble:

```text
strong statistical baseline
+ gradient-boosted global model
+ neural/global model
+ foundation model zero-shot or fine-tuned
+ calibrated quantiles
+ business-rule postprocessing
+ monitoring
```

## 5. Forecasting Problem Types

### 5.1 Point Forecasting

Predict one value per future time step.

```text
tomorrow demand = 120 units
```

Use when:

- decisions are roughly symmetric
- uncertainty is less important
- downstream system only accepts one value

Risk:

- hides uncertainty
- can lead to bad inventory, staffing, or risk decisions

### 5.2 Probabilistic Forecasting

Predict a distribution or quantiles.

Example:

```text
p10 = 90
p50 = 120
p90 = 180
```

Use when:

- risk matters
- decisions are asymmetric
- planning needs safety buffers
- extreme events matter
- inventory or capacity decisions depend on service levels

### 5.3 Multi-Horizon Forecasting

Predict multiple future steps:

```text
t+1, t+2, ..., t+28
```

Two common strategies:

- recursive: predict one step, feed prediction back in
- direct: predict all horizons directly

Recursive forecasts can accumulate errors. Direct multi-horizon models can learn horizon-specific behavior.

### 5.4 Univariate Forecasting

Forecast one series using only its history.

Good for:

- simple demand series
- quick baselines
- foundation model zero-shot testing

Limitation:

- cannot use promotions, price, weather, events, or cross-series information

### 5.5 Multivariate Forecasting

Use multiple series or variables.

Example:

```text
forecast store demand using:
sales history, price, promotion flag, holiday, weather, inventory, web traffic
```

Hard part:

- future covariates must actually be known or forecastable at prediction time

### 5.6 Global Forecasting

A global model is trained across many series.

Example:

```text
one LightGBM or neural model for 10,000 product-store series
```

Why it works:

- shares statistical strength
- learns common seasonalities and holiday effects
- helps sparse/noisy series
- scales better than hand-tuning one model per series

### 5.7 Local Forecasting

A local model is trained separately per series.

Example:

```text
one ARIMA model per product
```

Works well when:

- few series
- long history
- each series behaves differently
- interpretability is important

### 5.8 Hierarchical Forecasting

Series aggregate across levels:

```text
Total sales
  -> region
    -> store
      -> product
```

Forecasts should be coherent:

```text
sum(product forecasts) = store forecast
sum(store forecasts) = region forecast
sum(region forecasts) = total forecast
```

Use reconciliation to enforce this.

## 6. Anatomy Of A Time Series

Most time series can be decomposed conceptually:

```text
observed value = trend + seasonality + events + covariate effects + noise
```

### 6.1 Trend

Long-term direction:

- growth
- decline
- saturation
- regime change

### 6.2 Seasonality

Repeating pattern:

- hour of day
- day of week
- month of year
- annual seasonality
- holiday calendar

Multiple seasonalities are common:

```text
hourly electricity load:
  daily seasonality
  weekly seasonality
  annual seasonality
```

### 6.3 Events

Special causes:

- holidays
- promotions
- price changes
- product launches
- outages
- policy changes
- sports events
- weather shocks

### 6.4 Noise And Irreducible Uncertainty

Some variance is not predictable from available data.

The goal is not perfect prediction. The goal is useful prediction with honest uncertainty.

## 7. Data Preparation

### 7.1 Time Index Quality

Check:

- regular frequency
- missing timestamps
- duplicate timestamps
- timezone consistency
- daylight saving time issues
- late-arriving data
- clock drift for sensors

Bad timestamps ruin forecasting quietly.

### 7.2 Missing Values

Missing can mean different things:

- true zero
- not measured
- delayed reporting
- system outage
- product unavailable
- censored by stockout

Never blindly fill missing values before understanding their meaning.

### 7.3 Outliers

Outliers can be:

- data errors
- real events
- one-time shocks
- future-relevant extremes

Treatment depends on purpose:

- remove data errors
- cap measurement glitches
- keep real shocks
- flag events as covariates when possible

### 7.4 Transformations

Common transformations:

- log transform for positive skew
- Box-Cox
- differencing
- seasonal differencing
- scaling per series
- standardization
- robust scaling

Foundation models often do internal scaling, but model-specific preprocessing still matters.

### 7.5 Leakage Prevention

Time-series leakage is especially easy.

Common leakage:

- using future rolling windows
- using final aggregate statistics computed over full dataset
- random train/test split
- future covariates that would not be known
- target leakage through inventory, stockouts, or fulfillment data
- using revised economic data instead of data vintage available at forecast time

Rule:

```text
At each backtest origin, use only data known at that time.
```

## 8. Feature Engineering

Feature-based ML remains extremely strong in production.

### 8.1 Lag Features

Lag features expose past target values:

```text
y_{t-1}, y_{t-7}, y_{t-28}, y_{t-365}
```

Choose lags based on:

- frequency
- seasonality
- business cycle
- lead time

### 8.2 Rolling Features

Rolling statistics:

- rolling mean
- rolling median
- rolling standard deviation
- rolling min/max
- exponentially weighted moving average

Example:

```text
mean sales over last 7 days
mean sales over same weekday last 4 weeks
```

Compute them only from past data.

### 8.3 Calendar Features

Useful features:

- hour
- day of week
- week of year
- month
- quarter
- holiday
- days to holiday
- payday
- school calendar
- fiscal period

### 8.4 Static Features

For global models:

- product category
- store region
- customer segment
- sensor type
- country
- building type

### 8.5 Known Future Covariates

These are powerful because they are available for the forecast horizon:

- price plan
- planned promotions
- holiday calendar
- weather forecast
- scheduled maintenance
- capacity plan

### 8.6 Unknown Future Covariates

If a covariate is not known in the future, you must:

- forecast it separately
- use only historical values
- exclude it
- treat it as scenario input

Example:

```text
Future actual weather is unknown.
Weather forecast is known.
Use weather forecast, not actual future weather.
```

## 9. Classical Forecasting Models

Classical methods are still strong, especially with limited data.

### 9.1 Naive And Seasonal Naive

Naive:

```text
forecast = last observed value
```

Seasonal naive:

```text
forecast for next Monday = value from previous Monday
```

Why they matter:

- hard to beat for some series
- essential baselines
- useful sanity checks

### 9.2 Moving Average And Exponential Smoothing

Exponential smoothing gives more weight to recent observations.

ETS models handle:

- error
- trend
- seasonality

Good for:

- business series
- stable seasonality
- limited data
- interpretable baselines

### 9.3 ARIMA / SARIMA / SARIMAX

ARIMA models autoregression, differencing, and moving-average error terms.

SARIMA adds seasonality.

SARIMAX adds exogenous variables.

Good for:

- univariate series
- short/medium data
- interpretable statistical modeling
- autocorrelated residuals

Less ideal for:

- thousands of heterogeneous series without automation
- nonlinear covariate effects
- complex events/promotions

### 9.4 Prophet

Prophet models:

- trend
- seasonality
- holidays
- changepoints

Good for:

- business users
- daily data
- calendar effects
- analyst-in-the-loop workflows

Less ideal when:

- many related series need pooled learning
- high-frequency dynamics dominate
- covariates are complex

### 9.5 State-Space Models And Kalman Filters

State-space models represent hidden states evolving over time.

Useful for:

- noisy sensors
- missing data
- online updates
- dynamic regression
- structural time series
- nowcasting

## 10. Machine Learning Forecasting

### 10.1 Regression Framing

Turn forecasting into supervised learning:

```text
features at time t -> target at time t+h
```

Example row:

```text
target: sales next week
features: lag_1, lag_7, rolling_28_mean, price, promo, weekday, category
```

### 10.2 Gradient Boosting

LightGBM, XGBoost, and CatBoost are very strong for tabular forecasting.

Why:

- handle nonlinearities
- use many covariates
- robust on structured business data
- fast to train
- interpretable with feature importance/SHAP
- strong competition performance

Common production pattern:

```text
global LightGBM
+ lag features
+ rolling features
+ calendar features
+ static item/store features
+ known future covariates
```

### 10.3 Direct vs Recursive ML

Direct:

```text
train separate model for each horizon
or train model with horizon as feature
```

Recursive:

```text
predict t+1, feed prediction to predict t+2
```

Direct is often more stable for multi-horizon business forecasting.

### 10.4 Quantile Regression With ML

Train models for quantiles:

```text
p10, p50, p90
```

Using pinball loss.

Good for:

- prediction intervals
- inventory planning
- risk-sensitive decisions

Need to avoid quantile crossing:

```text
p10 should be <= p50 <= p90
```

## 11. Deep Learning Forecasting

Deep forecasting works best when you have many related series, nonlinear patterns, and enough data.

### 11.1 DeepAR

DeepAR trains an autoregressive recurrent model across many related time series and outputs probabilistic forecasts.

Strengths:

- probabilistic
- global learning
- handles related series
- likelihood-based

Limitations:

- autoregressive sampling can be slow
- less dominant than newer architectures for some long-horizon tasks

### 11.2 N-BEATS

N-BEATS uses deep residual blocks for univariate forecasting.

Strengths:

- strong point forecasting
- works across domains
- interpretable variant decomposes trend/seasonality

### 11.3 N-HiTS

N-HiTS improves long-horizon forecasting with hierarchical interpolation and multi-rate sampling.

Strengths:

- efficient
- strong for long horizons
- stable compared with some transformer approaches

### 11.4 Temporal Fusion Transformer

TFT is built for multi-horizon forecasting with static, past, and future covariates.

Strengths:

- covariate handling
- attention-based temporal modeling
- interpretable variable importance
- multi-horizon outputs

Limitations:

- many moving parts
- can be overkill for simple series
- tuning matters

### 11.5 PatchTST And Patch-Based Transformers

PatchTST treats time series as patches, similar to how vision transformers use image patches.

Why patches help:

- reduce sequence length
- capture local patterns
- improve long-horizon transformer efficiency

Strengths:

- strong long-term forecasting benchmarks
- simple transformer adaptation

### 11.6 Diffusion And Generative Forecasting

Diffusion-style models generate future trajectories rather than only point or quantile forecasts.

Useful for:

- multimodal futures
- scenario generation
- probabilistic paths

Limitations:

- computationally heavier
- harder to calibrate/evaluate
- less standard in business forecasting

### 11.7 State-Space And Mamba-Like Models

State-space sequence models are attractive for long sequences because they can be more efficient than quadratic attention.

Use when:

- long histories matter
- low-latency sequence processing matters
- transformer cost is too high

This is active research, not yet a universal replacement.

## 12. Time-Series Foundation Models

Foundation models are pretrained on many time series and used zero-shot or fine-tuned.

Examples:

- Chronos / Chronos-2
- TimesFM
- Moirai / Moirai-MoE
- Lag-Llama
- TimeGPT
- MOMENT
- TinyTimeMixer
- Timer
- Sundial
- Time-MoE

### 12.1 Why They Matter

They promise:

- zero-shot forecasting
- less feature engineering
- fewer per-dataset training loops
- strong cold-start baselines
- easier forecasting pipelines
- transfer across domains

### 12.2 How They Work

Different approaches:

| Model Family | Basic Idea |
| --- | --- |
| Chronos | scale/quantize values into tokens and train language-model-style transformer |
| TimesFM | decoder-only patched time-series model trained on large time-series corpus |
| Moirai | masked encoder universal forecasting transformer over large-scale time-series archive |
| Lag-Llama | decoder-only probabilistic foundation model using lags as covariates |
| TimeGPT | hosted pretrained transformer for forecasting/anomaly tasks |
| MOMENT | general time-series foundation model for forecasting/classification/anomaly/imputation |

### 12.3 When Foundation Models Shine

Use them when:

- you need a strong zero-shot baseline
- many series have little history
- you need quick deployment
- feature engineering capacity is low
- domain is similar to pretraining data
- you want probabilistic forecasts quickly

### 12.4 When They Do Not Automatically Win

Be careful when:

- future covariates drive the forecast
- business events/promotions dominate
- domain is absent from pretraining
- data is sparse/intermittent
- hierarchy coherence is required
- benchmark leakage is possible
- you need interpretability
- a simple baseline already performs near noise ceiling

Important practical framing:

```text
Foundation models are strong baselines and useful priors.
They are not a replacement for backtesting, covariates, calibration, or decision-aware evaluation.
```

### 12.5 Zero-Shot, Fine-Tuning, And Ensembling

Zero-shot:

```text
use pretrained model directly
```

Fine-tuning:

```text
adapt pretrained model to your domain
```

Ensembling:

```text
combine foundation model with statistical/ML models
```

In production, ensembling foundation models with classical/ML models is often safer than betting on one model family.

## 13. Model Selection: What To Use When

| Situation | Good Starting Point |
| --- | --- |
| one short series | naive, seasonal naive, ETS, ARIMA |
| one long seasonal series | ETS, SARIMA, Prophet, N-BEATS |
| thousands of related business series | global LightGBM + statistical baselines |
| many series with covariates | LightGBM/CatBoost, TFT, DeepAR, N-HiTS |
| long-horizon forecasting | N-HiTS, PatchTST, TimesFM/Chronos/Moirai, ensembles |
| cold-start or little history | foundation model + similar-series global model |
| intermittent demand | Croston variants, TSB, ADIDA/IMAPA, count models, hierarchical pooling |
| probabilistic inventory planning | quantile GBM, DeepAR, TFT, foundation probabilistic model, conformal calibration |
| hierarchy must add up | base model + reconciliation |
| high interpretability | ETS/ARIMA/Prophet, regression/GBM with features |
| real-time observability metrics | simple seasonal baselines, robust online models, foundation model as baseline |
| weather/spatiotemporal field | specialized graph/Fourier/physics-informed models |

## 14. Probabilistic Forecasting

### 14.1 Why Point Forecasts Are Not Enough

Two forecasts can have the same mean but very different risk:

```text
Forecast A:
  demand likely between 95 and 105

Forecast B:
  demand likely between 20 and 220
```

The same point forecast leads to different decisions.

### 14.2 Quantile Forecasts

Quantiles answer:

```text
What value is the target below with probability q?
```

Examples:

- p10: conservative lower forecast
- p50: median
- p90: high-side forecast

Use:

- p50 for median demand
- p90/p95 for service-level inventory
- p10/p90 for uncertainty bands

### 14.3 Prediction Intervals

A 90% prediction interval should contain the actual future value about 90% of the time.

Example:

```text
90% interval = [80, 170]
```

### 14.4 Full Distribution Forecasts

Some models produce a parametric or sampled distribution.

Examples:

- Gaussian
- Student-t
- negative binomial
- mixture distribution
- sample paths

Use full distributions when downstream optimization can use them.

## 15. Forecast Calibration

Calibration asks whether predicted probabilities match observed frequencies.

### 15.1 Interval Calibration

If the model says 90% interval, about 90% of observations should fall inside.

Metric:

```text
empirical coverage = observations inside interval / total observations
```

If coverage is 75% for nominal 90%, intervals are too narrow or miscentered.

If coverage is 99% for nominal 90%, intervals may be too wide.

### 15.2 Quantile Calibration

For a predicted p90 quantile, about 90% of observed values should be below it.

Check by quantile:

```text
predicted p10 -> actual below about 10%
predicted p50 -> actual below about 50%
predicted p90 -> actual below about 90%
```

### 15.3 Distribution Calibration

Use PIT, probability integral transform.

For each observation:

```text
u_t = predicted_CDF(y_t)
```

If forecasts are calibrated, PIT values should look uniform.

Patterns:

- U-shape: distribution too narrow
- hump shape: distribution too wide
- skew: biased forecasts

### 15.4 Calibration vs Sharpness

Calibration:

```text
Do probabilities match reality?
```

Sharpness:

```text
Are intervals/distributions as narrow as possible?
```

Good probabilistic forecasts are:

```text
calibrated and sharp
```

Not just calibrated. A forecast interval of `[-infinity, +infinity]` is calibrated but useless.

### 15.5 Calibration By Slice

Always check calibration by:

- horizon
- product/category
- geography
- demand level
- season
- promotion vs non-promotion
- weekday/weekend
- high volatility vs low volatility
- model family

A model can be calibrated on average but badly miscalibrated where decisions matter.

### 15.6 Calibration Methods

Common recalibration techniques:

| Method | Use |
| --- | --- |
| residual scaling | widen/narrow intervals based on backtest residuals |
| quantile recalibration | map predicted quantiles to empirical quantiles |
| isotonic regression | nonparametric monotonic recalibration |
| conformal prediction | distribution-free interval calibration under assumptions |
| ensemble calibration | combine models to improve uncertainty |
| variance inflation | simple fix for undercoverage |
| horizon-specific calibration | calibrate each lead time separately |
| segment-specific calibration | calibrate by product/region/volatility group |

## 16. Conformal Prediction For Forecasting

Conformal prediction wraps a model to produce calibrated intervals.

Basic idea:

```text
1. Train forecasting model.
2. Use calibration window to collect forecast errors.
3. Choose error quantile matching desired coverage.
4. Widen future intervals by that amount.
```

### 16.1 Why It Is Popular

- model-agnostic
- works with arbitrary forecasters
- gives coverage guarantees under assumptions
- useful when model uncertainty is unreliable

### 16.2 Time-Series Complications

Standard conformal assumes exchangeability. Time series are dependent and may drift.

Adaptations:

- rolling calibration windows
- weighted conformal
- block conformal
- adaptive conformal
- conformalized quantile regression
- ensemble conformalized quantile regression

### 16.3 Practical Use

Use conformal when:

- intervals under-cover in backtests
- model gives point forecasts only
- business needs coverage guarantees
- data drift is manageable with rolling calibration

Do not use conformal blindly when:

- regime shifts are severe
- calibration window is tiny
- dependence is strong and unaccounted for
- coverage must be conditional on many slices

## 17. Evaluation Metrics

No metric is universally best. Choose metrics based on the decision.

### 17.1 Point Forecast Metrics

| Metric | Formula / Meaning | Best Use | Caution |
| --- | --- | --- | --- |
| MAE | mean absolute error | robust, interpretable units | scale-dependent |
| RMSE | root mean squared error | penalizes large errors | sensitive to outliers |
| MSE | mean squared error | optimization/math convenience | hard to interpret units |
| MAPE | mean absolute percentage error | percent error intuition | breaks near zero, biased |
| sMAPE | symmetric percentage error | competitions/comparisons | still has quirks |
| WAPE | total absolute error / total actual | aggregate business error | can hide low-volume failures |
| MASE | MAE scaled by naive forecast MAE | compare across series | needs sensible naive baseline |
| RMSSE | RMSE scaled by naive differences | M5-style scale-free squared error | sensitive to outliers |
| Bias | mean forecast error | systematic over/underforecast | can cancel across series |
| Tracking signal | cumulative error / error scale | monitoring bias | threshold depends on context |

### 17.2 Probabilistic Metrics

| Metric | Meaning | Best Use |
| --- | --- | --- |
| Pinball loss | quantile forecast loss | quantile models |
| Weighted quantile loss | scaled quantile loss | business-scale probabilistic eval |
| CRPS | distributional accuracy, integrates quantile losses | full probabilistic forecasts |
| Log score / NLL | negative log probability of observed value | parametric distributions |
| Interval coverage | observed fraction inside interval | calibration |
| Interval width | sharpness | compare uncertainty concentration |
| Winkler / interval score | rewards narrow intervals with correct coverage | interval forecasts |
| PIT histogram | distribution calibration diagnostic | full CDF forecasts |

### 17.3 Business Metrics

Sometimes statistical metrics are not enough.

Use:

- stockout rate
- service level
- inventory holding cost
- waste/spoilage
- staffing shortfall
- overstaffing cost
- SLA violation probability
- energy imbalance cost
- revenue loss
- cash shortfall risk

Example:

```text
The best RMSE model may not be the best inventory model.
```

### 17.4 Metric Selection Guide

| Scenario | Recommended Metrics |
| --- | --- |
| compare across many series | MASE, RMSSE, WAPE |
| high-volume business aggregate | WAPE, weighted MAE, service-level cost |
| intermittent demand | MASE/RMSSE, stockout/holding cost, avoid MAPE |
| probabilistic forecast | CRPS, pinball loss, coverage, interval score |
| inventory planning | quantile loss, service level, stockout/holding cost |
| energy/load | MAE/RMSE, peak error, CRPS for probabilistic |
| finance/risk | directional metrics, quantile loss, VaR coverage, economic P&L |
| anomaly/observability | precision/recall on events plus forecast residual behavior |

## 18. Backtesting And Validation

### 18.1 Why Random Splits Are Wrong

Random splits leak future information into training.

Use time-ordered splits.

### 18.2 Holdout Split

Simple:

```text
train: first 80%
test: final 20%
```

Good first check, but high variance.

### 18.3 Rolling-Origin Backtest

Simulate repeated forecasting:

```text
train up to Jan -> forecast Feb
train up to Feb -> forecast Mar
train up to Mar -> forecast Apr
```

This is the standard robust approach.

### 18.4 Expanding vs Sliding Window

Expanding:

```text
training window grows over time
```

Sliding:

```text
fixed recent window moves forward
```

Use sliding windows when old history becomes irrelevant.

### 18.5 Multi-Horizon Evaluation

Evaluate by horizon:

```text
h=1, h=7, h=14, h=28
```

Average metrics can hide that long horizons fail.

### 18.6 Baselines

Always compare to:

- naive
- seasonal naive
- moving average
- ETS/ARIMA/Theta
- simple global ML model

If a complex model cannot beat seasonal naive, it is not useful.

### 18.7 Statistical Comparison

Use:

- Diebold-Mariano test with care
- bootstrapped confidence intervals
- paired comparisons across forecast origins
- win rates across series
- skill scores relative to baseline

## 19. Hierarchical And Grouped Forecasting

### 19.1 Why Reconciliation Matters

Without reconciliation:

```text
forecast total sales = 10,000
sum of regional forecasts = 11,200
```

This creates planning contradictions.

### 19.2 Reconciliation Approaches

| Method | Idea |
| --- | --- |
| bottom-up | forecast bottom level, sum upward |
| top-down | forecast top level, allocate downward |
| middle-out | anchor at middle level |
| optimal combination | forecast all levels, combine coherently |
| MinT / MinTrace | minimize reconciled forecast variance using covariance estimates |
| probabilistic reconciliation | reconcile full distributions or samples |

### 19.3 Practical Advice

- Generate strong base forecasts at multiple levels.
- Reconcile after forecasting.
- Evaluate both bottom-level and aggregate performance.
- Check coherence.
- Reconcile probabilistic forecasts if decisions use uncertainty.

## 20. Intermittent Demand

Intermittent demand has many zeros.

Examples:

- spare parts
- slow-moving SKUs
- rare medical supplies
- low-volume product-store combinations

Problems:

- MAPE breaks
- normal errors are poor
- zeros dominate
- demand occurrence and demand size are different processes

Methods:

- Croston
- SBA
- TSB
- ADIDA
- IMAPA
- count models
- hierarchical pooling
- quantile forecasts for service levels

Often better framing:

```text
P(demand occurs) * demand size given occurrence
```

## 21. Anomaly Detection And Forecasting

Forecasting can support anomaly detection:

```text
actual outside prediction interval -> anomaly candidate
```

But anomaly detection needs:

- calibrated intervals
- seasonality-aware baselines
- alert grouping
- suppression windows
- root-cause context
- precision/recall evaluation on incidents

Do not alert on every residual spike.

## 22. Forecasting With External Events

Many failures come from missing causal drivers.

Examples:

- demand spikes from promotion
- traffic spike from ad campaign
- electricity load from temperature
- call volume from outage
- sales drop from stockout

If the driver is known in advance, include it.

If the driver is unknown, forecast scenarios:

```text
base case
high promotion response
low promotion response
weather scenario
recession scenario
```

## 23. Forecasting Applications

### 23.1 Retail And Demand Planning

Uses:

- replenishment
- inventory
- promotions
- pricing
- supply chain

Important:

- hierarchy
- intermittent demand
- stockouts/censoring
- promotions
- lead time
- service levels

### 23.2 Energy

Uses:

- load forecasting
- electricity price forecasting
- renewable generation
- grid balancing

Important:

- weather covariates
- probabilistic forecasts
- peak error
- intraday updates

### 23.3 Finance

Uses:

- volatility
- risk
- liquidity
- cash flow
- macroeconomic nowcasting

Important:

- nonstationarity
- regime shifts
- low signal-to-noise
- economic value over RMSE
- careful backtesting

### 23.4 Observability And Infrastructure

Uses:

- CPU/memory load
- traffic
- latency
- error rate
- capacity planning
- anomaly detection

Important:

- high frequency
- seasonality
- incident periods
- alert fatigue
- online calibration

### 23.5 Healthcare And Epidemiology

Uses:

- admissions
- disease incidence
- staffing
- supply planning

Important:

- reporting delays
- data revisions
- uncertainty
- policy changes
- ethical risk

### 23.6 Weather And Climate

Modern weather forecasting has become a special frontier of spatiotemporal forecasting.

Examples:

- GraphCast
- Pangu-Weather
- FourCastNet
- GenCast

These are not generic business time-series models. They are specialized spatiotemporal physical-field models trained on massive weather reanalysis data.

### 23.7 Manufacturing And IoT

Uses:

- predictive maintenance
- sensor forecasting
- quality prediction
- throughput planning

Important:

- missing sensor data
- drift
- irregular sampling
- physical constraints
- anomaly vs forecast distinction

## 24. Production Forecasting Architecture

### 24.1 Batch Forecasting Pipeline

```text
data ingestion
  -> validation
  -> feature generation
  -> model training or loading
  -> backtesting
  -> forecast generation
  -> calibration
  -> reconciliation
  -> business constraints
  -> publish forecasts
  -> monitor actuals
```

### 24.2 Online Forecasting Pipeline

```text
streaming data
  -> real-time aggregation
  -> online features
  -> forecast update
  -> anomaly scoring
  -> alerting / decision system
```

### 24.3 Forecast Store

Store:

- forecast timestamp
- forecast origin
- target timestamp
- horizon
- model version
- point forecast
- quantiles/distribution samples
- input data snapshot
- covariates used
- calibration version
- reconciliation version

This enables proper evaluation later.

## 25. Monitoring

Monitor:

- forecast accuracy
- bias
- coverage
- interval width
- data freshness
- missing values
- covariate drift
- residual drift
- business KPI impact
- model latency
- failed jobs

Drift examples:

- new product category
- changed customer behavior
- changed data pipeline
- macro shock
- promotion strategy changed
- sensor recalibrated

## 26. Common Failure Modes

| Failure | Symptom | Fix |
| --- | --- | --- |
| leakage | great backtest, poor production | time-aware validation |
| wrong frequency | weird seasonality | resample correctly |
| missing covariates | promotion/weather shocks missed | add known drivers |
| overfitting | complex model wins one split only | rolling backtests |
| MAPE misuse | infinite/unstable metric near zero | use MASE/WAPE/RMSSE |
| uncalibrated intervals | 90% interval covers 70% | conformal/recalibration |
| hierarchy incoherence | totals do not add up | reconciliation |
| stockout censoring | model learns low demand during stockout | correct censored demand |
| stale model | performance degrades | retraining/monitoring |
| regime shift | all models fail | scenario modeling, robust monitoring |
| ignoring decision cost | good RMSE, bad operations | business objective metric |
| foundation model overtrust | zero-shot looks good on one split | compare against baselines |

## 27. Modern Evaluation Checklist

For any serious forecast project:

1. Define forecast horizon and decision.
2. Identify what data is known at prediction time.
3. Build naive and seasonal naive baselines.
4. Use rolling-origin backtesting.
5. Evaluate by horizon and segment.
6. Use scale-free metrics across many series.
7. Use probabilistic metrics if decisions involve risk.
8. Check calibration and sharpness.
9. Compare foundation models against classical/ML baselines.
10. Check leakage carefully.
11. Reconcile hierarchy if needed.
12. Monitor production drift and calibration.

## 28. State-Of-The-Art Trends As Of 2026

Major trends:

| Trend | Meaning |
| --- | --- |
| time-series foundation models | pretrained models for zero/few-shot forecasting |
| probabilistic forecasting | quantiles/distributions becoming default for decisions |
| conformal calibration | model-agnostic interval calibration in production |
| global models | one model across many related series |
| hybrid ensembles | combining statistical, ML, deep, and foundation models |
| spatiotemporal foundation models | weather/climate models with graph/Fourier/geometric architectures |
| hierarchy-aware forecasting | coherent forecasts across product/geography/time levels |
| decision-aware evaluation | optimizing cost, service level, risk, not just RMSE |
| benchmark realism | GIFT-Eval, ProbTS, and live/rolling benchmarks to reduce leakage |
| covariate-aware foundation models | newer models adding better multivariate and exogenous support |

Important caveat:

```text
The SOTA model family depends on the domain, horizon, covariates, data volume, and decision metric.
There is no universal winner.
```

## 29. Recommended Practical Baseline Stack

For business forecasting:

```text
1. seasonal naive
2. ETS / AutoARIMA / Theta
3. global LightGBM with lag and calendar features
4. N-HiTS or TFT if enough related series
5. Chronos/TimesFM/Moirai/TimeGPT zero-shot baseline
6. ensemble best performers
7. conformal or quantile calibration
8. reconciliation if hierarchical
```

For probabilistic forecasting:

```text
1. quantile regression baseline
2. probabilistic statistical model
3. DeepAR/TFT/Moirai/Chronos-style probabilistic model
4. CRPS + pinball loss evaluation
5. coverage/sharpness calibration
6. conformal adjustment if needed
```

For observability:

```text
1. seasonal naive / robust rolling baseline
2. anomaly-aware preprocessing
3. fast global model or foundation model benchmark
4. calibrated residual intervals
5. alert grouping and incident-level evaluation
```

## 30. Interview-Ready Answers

### "What is the modern state of time-series forecasting?"

```text
Modern forecasting is a mix of classical statistical models, feature-based global ML, deep probabilistic models, and time-series foundation models. Classical baselines are still hard to beat on many small or stable series. Gradient boosting with lag, rolling, calendar, and covariate features is extremely strong in production. Deep models help when there are many related series and nonlinear covariate effects. Foundation models like Chronos, TimesFM, Moirai, Lag-Llama, and TimeGPT are strong zero-shot baselines, but they still need backtesting, calibration, and comparison against simpler models.
```

### "How do you evaluate forecasts?"

```text
I use rolling-origin backtests, never random splits. I compare against naive and seasonal naive baselines, evaluate by horizon and segment, and choose metrics based on the decision. For point forecasts I use MAE/RMSE/WAPE/MASE/RMSSE depending on scale and business need. For probabilistic forecasts I use pinball loss, CRPS, interval coverage, interval width, and calibration diagnostics.
```

### "What is calibration in forecasting?"

```text
Calibration means predicted probabilities match observed frequencies. If a model gives a 90% prediction interval, actual values should fall inside about 90% of the time. I check coverage by horizon and segment, use PIT or quantile calibration for distributional forecasts, and apply recalibration or conformal prediction if intervals are too narrow or too wide.
```

### "When would you use a foundation model?"

```text
I would use a time-series foundation model as a strong zero-shot or cold-start baseline, especially when there is little labeled history or we need fast deployment. But I would still compare it against seasonal naive, ETS/ARIMA, and global LightGBM. If the forecast depends heavily on known future covariates like promotions or price, a feature-based or covariate-aware model may outperform a generic zero-shot model.
```

### "Why is MAPE dangerous?"

```text
MAPE divides by the actual value, so it breaks or explodes near zero and behaves badly for intermittent demand. For many-series forecasting, I prefer MASE, RMSSE, WAPE, or business-cost metrics.
```

### "How do you handle hierarchical forecasts?"

```text
I generate base forecasts at the relevant levels, then apply reconciliation so forecasts are coherent across the hierarchy. Simple approaches include bottom-up and top-down; stronger methods like MinT or MinTrace use covariance information to minimize reconciled forecast variance. I evaluate both bottom-level and aggregate performance.
```

## 31. Quick Glossary

| Term | Short Meaning |
| --- | --- |
| horizon | future steps predicted |
| origin | time forecast is made |
| lead time | delay between decision and need |
| seasonal naive | repeat last season's value |
| ETS | exponential smoothing state-space family |
| ARIMA | autoregressive integrated moving-average model |
| SARIMAX | seasonal ARIMA with exogenous variables |
| global model | one model trained across many series |
| covariate | external predictor |
| known future covariate | future feature known at forecast time |
| probabilistic forecast | distribution or quantiles |
| pinball loss | quantile forecast loss |
| CRPS | proper score for full distributions |
| coverage | fraction inside interval |
| sharpness | concentration/narrowness of forecast distribution |
| conformal prediction | model-agnostic calibrated interval method |
| reconciliation | making hierarchical forecasts add up |
| foundation model | pretrained model used across datasets/tasks |
| backtest | historical simulation of forecast deployment |
| leakage | using future information accidentally |

## 32. References

- Forecasting textbook: [Forecasting: Principles and Practice](https://otexts.com/fpp3/)
- M4 Competition: [The M4 Competition: 100,000 time series and 61 forecasting methods](https://www.sciencedirect.com/science/article/pii/S0169207019301128)
- M5 Competition: [The M5 competition: Background, organization, and implementation](https://www.sciencedirect.com/science/article/pii/S0169207021001187)
- Monash archive: [Monash Time Series Forecasting Archive](https://arxiv.org/abs/2105.06643)
- GIFT-Eval: [A Benchmark For General Time Series Forecasting Model Evaluation](https://arxiv.org/abs/2410.10393)
- ProbTS: [Benchmarking Point and Distributional Forecasting across Diverse Prediction Horizons](https://papers.nips.cc/paper_files/paper/2024/hash/55f2a27b1ac39dbfdd0fc83742dc87d7-Abstract-Datasets_and_Benchmarks_Track.html)
- Foundation model survey: [Foundation Models for Time Series: A Survey](https://arxiv.org/abs/2504.04011)
- TimesFM: [A decoder-only foundation model for time-series forecasting](https://arxiv.org/abs/2310.10688)
- Google TimesFM blog: [A decoder-only foundation model for time-series forecasting](https://research.google/blog/a-decoder-only-foundation-model-for-time-series-forecasting/)
- Chronos: [Learning the Language of Time Series](https://arxiv.org/abs/2403.07815)
- Amazon Chronos page: [Chronos: Learning the language of time series](https://www.amazon.science/publications/chronos-learning-the-language-of-time-series)
- Moirai: [Unified Training of Universal Time Series Forecasting Transformers](https://arxiv.org/abs/2402.02592)
- Lag-Llama: [Towards Foundation Models for Probabilistic Time Series Forecasting](https://arxiv.org/abs/2310.08278)
- DeepAR: [Probabilistic Forecasting with Autoregressive Recurrent Networks](https://arxiv.org/abs/1704.04110)
- N-BEATS: [Neural basis expansion analysis for interpretable time series forecasting](https://arxiv.org/abs/1905.10437)
- N-HiTS: [Neural Hierarchical Interpolation for Time Series Forecasting](https://arxiv.org/abs/2201.12886)
- TFT: [Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting](https://arxiv.org/abs/1912.09363)
- Prophet: [Forecasting at scale](https://peerj.com/preprints/3190/)
- Conformalized quantile regression: [Conformalized Quantile Regression](https://arxiv.org/abs/1905.03222)
- Time-series conformal forecasting: [Ensemble Conformalized Quantile Regression for Probabilistic Time Series Forecasting](https://arxiv.org/abs/2202.08756)
- Hierarchical forecasting: [Optimal combination forecasts for hierarchical time series](https://robjhyndman.com/publications/hierarchical/)
- HierarchicalForecast library: [Nixtla hierarchicalforecast](https://github.com/Nixtla/hierarchicalforecast)
- AutoGluon TimeSeries: [Time Series Forecasting](https://auto.gluon.ai/dev/tutorials/timeseries/index.html)
- Darts: [User-Friendly Modern Machine Learning for Time Series](https://arxiv.org/abs/2110.03224)
- GluonTS: [Probabilistic Time Series Models in Python](https://arxiv.org/abs/1906.05264)
- sktime: [A Unified Interface for Machine Learning with Time Series](https://arxiv.org/abs/1909.07872)
- GraphCast: [Learned Global Weather Forecasting](https://deepmind.google/research/publications/graphcast-learned-global-weather-forecasting/)
- Pangu-Weather: [Accurate medium-range global weather forecasting with 3D neural networks](https://www.nature.com/articles/s41586-023-06185-3)
- FourCastNet: [A Global Data-driven High-resolution Weather Model](https://arxiv.org/abs/2202.11214)

