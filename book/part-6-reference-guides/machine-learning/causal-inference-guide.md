# Causal Inference: A Complete Practical Guide

Prepared for interview preparation and real system design. Updated May 2026.

This guide explains causal inference from first principles through modern applied practice: potential outcomes, DAGs, experiments, observational studies, matching, weighting, regression adjustment, doubly robust estimation, instrumental variables, regression discontinuity, difference-in-differences, synthetic controls, causal ML, sensitivity analysis, and production workflows.

This is educational material, not medical, legal, financial, or policy advice. Causal claims can affect real people, so high-stakes applications require domain experts, careful study design, and independent review.

## 1. The One-Sentence Definition

Causal inference is the science of estimating what would happen if we intervened.

Simple version:

```text
Prediction asks:
  What is likely to happen?

Causal inference asks:
  What would happen if we changed something?
```

Examples:

- Would a discount increase purchases?
- Did a policy reduce unemployment?
- Does a drug lower mortality?
- Did a product change improve retention?
- Would smaller class sizes improve test scores?
- Did a marketing campaign create incremental revenue?

The key word is "if."

```text
What if we treated this patient?
What if we did not send this email?
What if this state had not passed the law?
What if this user had not seen the new onboarding flow?
```

## 2. Why Prediction Is Not Causation

A predictive model learns associations:

```text
P(Y | X)
```

A causal model asks about interventions:

```text
P(Y | do(T = t))
```

Those are different.

Example:

```text
People who take a medication may be sicker than people who do not.
If treated people have worse outcomes, that does not mean the medication caused harm.
The treated group may have been higher risk before treatment.
```

Prediction can say:

```text
Patients taking this medication have higher risk.
```

Causal inference asks:

```text
For comparable patients, what would happen if they did vs did not take the medication?
```

Good interview line:

> Prediction is about forecasting outcomes under the world as observed. Causal inference is about comparing outcomes under alternative worlds created by interventions.

## 3. The Fundamental Problem

For one unit, we cannot observe both possible outcomes.

If a user receives a coupon:

```text
we observe purchase outcome with coupon
we do not observe what the same user would have done without coupon
```

If a patient receives treatment:

```text
we observe outcome under treatment
we do not observe outcome for the same patient under no treatment
```

This is the fundamental problem of causal inference.

We want:

```text
Y_i(1) - Y_i(0)
```

But for each unit `i`, we observe only one of:

```text
Y_i(1) or Y_i(0)
```

Causal inference is about constructing credible comparisons to estimate the missing counterfactual.

## 4. Core Vocabulary

| Term | Meaning |
| --- | --- |
| Unit | entity being studied: user, patient, firm, region, device |
| Treatment | intervention/action/exposure whose effect we want |
| Control | no treatment, status quo, or comparison treatment |
| Outcome | variable affected by treatment |
| Potential outcome | outcome a unit would have under a treatment condition |
| Counterfactual | unobserved potential outcome under an alternative treatment |
| Estimand | causal quantity we want to estimate |
| Estimate | numerical result produced from data |
| Confounder | variable affecting both treatment and outcome |
| Mediator | variable on causal path from treatment to outcome |
| Collider | variable caused by two variables; conditioning on it can create bias |
| Instrument | variable affecting treatment but not outcome except through treatment |
| DAG | directed acyclic graph showing causal assumptions |
| SCM | structural causal model with equations and causal graph |
| ATE | average treatment effect |
| ATT | average treatment effect on treated |
| CATE | conditional average treatment effect |
| ITT | intention-to-treat effect |
| LATE | local average treatment effect for compliers |
| Propensity score | probability of receiving treatment given covariates |
| Positivity | each covariate group has treatment and control support |
| Identification | showing the effect can be expressed using observed data under assumptions |
| Estimation | computing the effect from data |
| Inference | uncertainty quantification: standard errors, confidence intervals, tests |

## 5. The Causal Workflow

A serious causal analysis follows this order:

```text
1. Define the causal question.
2. Define treatment, control, outcome, unit, and time window.
3. Specify assumptions.
4. Identify the causal effect.
5. Estimate the effect.
6. Quantify uncertainty.
7. Run diagnostics and sensitivity checks.
8. Interpret with limitations.
```

Do not start with:

```text
Which model should I use?
```

Start with:

```text
What intervention and counterfactual are we comparing?
```

## 6. Estimands

An estimand is the exact causal quantity you want.

### 6.1 Individual Treatment Effect

```text
ITE_i = Y_i(1) - Y_i(0)
```

This is individual-level effect. It is not directly observed.

### 6.2 Average Treatment Effect

```text
ATE = E[Y(1) - Y(0)]
```

Average effect in the target population.

Use when:

- policy applies to entire population
- broad average effect matters

### 6.3 Average Treatment Effect On The Treated

```text
ATT = E[Y(1) - Y(0) | T = 1]
```

Effect for those who actually received treatment.

Use when:

- evaluating a program as implemented
- treated group is the policy-relevant group

### 6.4 Average Treatment Effect On Controls

```text
ATC = E[Y(1) - Y(0) | T = 0]
```

Effect if untreated people had been treated.

Use when:

- deciding whether to expand treatment to untreated group

### 6.5 Conditional Average Treatment Effect

```text
CATE(x) = E[Y(1) - Y(0) | X = x]
```

Effect for people with features `X = x`.

Use for:

- personalization
- uplift modeling
- targeting
- heterogeneous treatment effects

### 6.6 Intention-To-Treat Effect

ITT is the effect of assignment to treatment, not necessarily receiving treatment.

Example:

```text
effect of being assigned a coupon
not effect of actually opening or using coupon
```

Use when:

- compliance is imperfect
- assignment is randomized
- policy controls assignment, not uptake

### 6.7 Local Average Treatment Effect

LATE is the effect for compliers whose treatment status changes because of an instrument.

Example:

```text
lottery assignment affects who attends a school
LATE estimates effect for people induced to attend by lottery
```

## 7. Potential Outcomes Framework

The potential outcomes framework writes causal effects using counterfactual outcomes.

For binary treatment:

```text
Y(1) = outcome if treated
Y(0) = outcome if untreated
```

Observed outcome:

```text
Y = T * Y(1) + (1 - T) * Y(0)
```

Treatment effect:

```text
Y(1) - Y(0)
```

This framework is natural for:

- randomized experiments
- treatment effect estimation
- matching/weighting
- CATE/uplift modeling
- policy evaluation

## 8. Structural Causal Models And DAGs

Pearl-style causal inference uses structural causal models and directed acyclic graphs.

A structural causal model represents variables as equations:

```text
X = f_X(U_X)
T = f_T(X, U_T)
Y = f_Y(T, X, U_Y)
```

A DAG represents causal arrows:

```text
X -> T -> Y
X -> Y
```

DAGs help answer:

- What should we adjust for?
- What should we not adjust for?
- Is the effect identifiable?
- Are there backdoor paths?
- Are mediators or colliders being conditioned on?

Potential outcomes and DAGs are complementary:

```text
Potential outcomes define causal estimands.
DAGs organize causal assumptions and identification.
```

## 9. Interventions And The do(.) Operator

Conditioning:

```text
P(Y | T = 1)
```

means looking at people who naturally received treatment.

Intervening:

```text
P(Y | do(T = 1))
```

means setting treatment to 1 by intervention.

These differ when treatment is confounded.

Example:

```text
P(health outcome | surgery)
```

is not necessarily:

```text
P(health outcome | do(surgery))
```

because surgery patients differ systematically from non-surgery patients.

## 10. Core Assumptions

### 10.1 Consistency

If a unit receives treatment `T = 1`, observed outcome equals its treated potential outcome:

```text
Y = Y(1)
```

If untreated:

```text
Y = Y(0)
```

This requires treatment to be well-defined.

Bad treatment definition:

```text
"marketing"
```

Better:

```text
"15% coupon email sent at 9am with subject line A"
```

### 10.2 Exchangeability / Ignorability

Treatment and control groups are comparable after adjustment:

```text
(Y(1), Y(0)) independent of T given X
```

In randomized experiments, randomization makes this plausible.

In observational studies, this is a strong assumption.

### 10.3 Positivity / Overlap

Every covariate pattern has a nonzero chance of treatment and control:

```text
0 < P(T = 1 | X = x) < 1
```

If all high-risk patients receive treatment, you cannot learn what would happen if high-risk patients did not receive it.

### 10.4 SUTVA

SUTVA includes:

- no interference between units
- no hidden versions of treatment

Interference examples:

- one user's treatment affects another user
- herd immunity
- marketplace promotions change supply for others
- peer effects in schools

Hidden treatment versions:

```text
"treated" includes different doses, channels, timings, or qualities
```

### 10.5 No Unmeasured Confounding

All common causes of treatment and outcome are measured and adjusted for.

This is often the hardest assumption in observational studies.

## 11. DAG Concepts

### 11.1 Confounder

A confounder causes both treatment and outcome.

```text
C -> T
C -> Y
T -> Y
```

If not adjusted, it biases treatment effect.

Example:

```text
health severity -> medication
health severity -> mortality
medication -> mortality
```

### 11.2 Mediator

A mediator lies on the causal pathway.

```text
T -> M -> Y
```

Example:

```text
tutoring -> study hours -> test score
```

If you want total effect of tutoring, do not adjust for study hours.

If you want direct effect not through study hours, mediation analysis is needed.

### 11.3 Collider

A collider is caused by two variables.

```text
T -> C <- U
```

Conditioning on a collider can create a false association.

Example:

```text
talent -> admitted to elite school <- wealth
```

Among admitted students, talent and wealth may become negatively associated even if unrelated in the full population.

### 11.4 Backdoor Path

A backdoor path is a noncausal path from treatment to outcome through common causes.

```text
T <- C -> Y
```

To estimate causal effect, block backdoor paths by adjusting for appropriate confounders.

### 11.5 Frontdoor Path

Frontdoor identification can work when confounding between treatment and outcome exists, but a mediator is observed and satisfies special assumptions.

Classic pattern:

```text
T -> M -> Y
U -> T
U -> Y
```

If all effect of `T` on `Y` goes through `M`, and certain paths can be adjusted, the effect can be identifiable.

Frontdoor is elegant but less commonly usable than backdoor adjustment.

## 12. What To Adjust For

Adjust for:

- common causes of treatment and outcome
- pre-treatment confounders
- variables needed to block backdoor paths

Do not adjust for:

- mediators when estimating total effect
- colliders
- descendants of treatment
- variables measured after treatment that are affected by treatment

Rule:

```text
Adjustment set should be chosen from causal knowledge, not feature importance.
```

Machine learning feature selection can choose colliders or mediators and make causal bias worse.

## 13. Randomized Experiments

Randomized controlled trials are the cleanest design for causal inference.

Randomization makes treatment independent of potential outcomes:

```text
(Y(1), Y(0)) independent of T
```

### 13.1 Difference In Means

For randomized binary treatment:

```text
ATE_hat = mean(Y | T = 1) - mean(Y | T = 0)
```

This is unbiased under proper randomization.

### 13.2 Regression Adjustment In Experiments

Even in experiments, regression can improve precision:

```text
Y = alpha + beta*T + gamma*X + error
```

Because treatment is randomized, covariates are not needed for unbiasedness, but can reduce variance.

### 13.3 Stratified Randomization

Randomize within strata:

```text
region
gender
risk level
device type
```

This improves balance and precision.

### 13.4 Cluster Randomization

Randomize groups:

- schools
- hospitals
- stores
- regions
- households

Use when:

- interference within groups exists
- treatment delivered at group level

Need cluster-aware standard errors.

### 13.5 Noncompliance

Assignment and treatment received differ.

Examples:

- assigned coupon but never opens email
- assigned drug but does not take it
- assigned training but does not attend

Effects:

- ITT: effect of assignment
- per-protocol: effect among compliers, but can be biased
- IV/LATE: effect for compliers induced by assignment

### 13.6 Attrition

Outcome missingness after treatment can bias results if missingness depends on treatment and potential outcome.

Need:

- attrition reporting
- bounds
- inverse probability weighting
- sensitivity analysis

## 14. Target Trial Emulation

Target trial emulation is a practical discipline for observational causal studies.

Before analyzing observational data, specify the randomized trial you wish you could run:

```text
eligibility criteria
treatment strategies
assignment time
follow-up period
outcome
causal contrast
analysis plan
```

Then emulate it using observational data as closely as possible.

This helps avoid:

- immortal time bias
- unclear treatment timing
- vague eligibility
- post-treatment adjustment
- outcome-window confusion

Good framing:

> If you cannot describe the target trial, your causal question is probably not well-defined.

## 15. Observational Causal Inference

In observational data, treatment is not randomized.

Examples:

- users self-select into premium plan
- doctors assign treatment based on severity
- cities adopt policy based on local conditions
- high-value customers receive marketing

The key problem:

```text
treated and control groups differ before treatment
```

Goal:

```text
construct a credible counterfactual comparison
```

Methods:

- regression adjustment
- matching
- stratification
- propensity score weighting
- doubly robust estimators
- instrumental variables
- regression discontinuity
- difference-in-differences
- synthetic control

Method choice depends on the identification strategy.

## 16. Matching

Matching pairs treated units with similar control units.

Goal:

```text
compare like with like
```

Common methods:

- exact matching
- nearest-neighbor matching
- caliper matching
- propensity score matching
- Mahalanobis matching
- coarsened exact matching

### 16.1 Matching Workflow

```text
1. Choose pre-treatment covariates.
2. Match treated and control units.
3. Check covariate balance.
4. Estimate treatment effect in matched sample.
5. Quantify uncertainty.
```

### 16.2 Balance

Balance means treated and control groups look similar on covariates.

Check:

- standardized mean differences
- variance ratios
- distribution plots
- overlap

Do not judge matching by predictive accuracy. Judge it by covariate balance and causal assumptions.

### 16.3 Matching Limitations

- cannot fix unmeasured confounding
- can discard data
- bad propensity models hurt matching
- exact matching impossible in high dimensions
- estimates effect for matched population, not always full population

## 17. Propensity Scores

The propensity score is:

```text
e(X) = P(T = 1 | X)
```

It summarizes treatment assignment probability.

Use it for:

- matching
- stratification
- inverse probability weighting
- overlap diagnostics

### 17.1 Propensity Score Matching

Match treated and control units with similar `e(X)`.

### 17.2 Stratification

Divide data into propensity score bins and compare treated/control within bins.

### 17.3 Overlap Diagnostics

Plot propensity distributions by treatment group.

Bad overlap:

```text
treated propensities near 1
control propensities near 0
```

This means causal estimates rely on extrapolation.

### 17.4 Trimming

Drop observations with extreme propensities:

```text
e(X) < 0.01 or e(X) > 0.99
```

This changes the target population but improves stability.

## 18. Inverse Probability Weighting

IPW creates a pseudo-population where treatment is independent of measured confounders.

Weights for ATE:

```text
if T = 1: weight = 1 / e(X)
if T = 0: weight = 1 / (1 - e(X))
```

Then compare weighted outcomes.

### 18.1 Stabilized Weights

Stabilized weights reduce variance:

```text
treated: P(T=1) / e(X)
control: P(T=0) / (1 - e(X))
```

### 18.2 IPW Problems

Problems:

- extreme weights
- poor overlap
- noisy propensity estimates
- high variance
- sensitive to propensity misspecification

Always inspect weight distribution.

## 19. Outcome Regression And G-Computation

Outcome regression models:

```text
E[Y | T, X]
```

Then predict each unit under both treatments:

```text
Y_hat(1, X_i)
Y_hat(0, X_i)
```

Estimate:

```text
ATE_hat = average_i [Y_hat(1, X_i) - Y_hat(0, X_i)]
```

This is also called:

- standardization
- g-computation
- outcome modeling

Pros:

- intuitive
- flexible with ML
- works when outcome model is good

Cons:

- biased if outcome model misspecified
- can extrapolate where treatment/control overlap is poor

## 20. Doubly Robust Estimation

Doubly robust methods combine:

- outcome model
- propensity model

The big idea:

```text
If either the outcome model or the propensity model is correct,
the estimator can still be consistent, under assumptions.
```

### 20.1 AIPW

Augmented inverse probability weighting combines regression adjustment and IPW correction.

For ATE, conceptually:

```text
estimate outcome under treatment/control
add correction based on observed residuals weighted by propensity
```

Pros:

- robust to one nuisance model being wrong
- works well with cross-fitting
- strong modern baseline

Cons:

- extreme propensities still cause variance
- double robustness does not protect against unmeasured confounding

### 20.2 TMLE

Targeted maximum likelihood estimation:

```text
1. fit initial outcome model
2. estimate propensity
3. update outcome model in a targeting step
4. estimate target causal parameter
```

TMLE is widely used in biostatistics and epidemiology.

Strength:

- compatible with flexible ML
- doubly robust
- targets a specific estimand

## 21. Double Machine Learning

Double/debiased machine learning uses ML to estimate nuisance functions while preserving valid causal estimation.

Nuisance functions:

```text
m(X) = E[Y | X]
e(X) = E[T | X]
```

DML uses:

- orthogonal scores
- cross-fitting
- residualization

### 21.1 Why Orthogonalization Matters

If ML nuisance models are slightly wrong, naive plug-in estimates can be biased.

Orthogonal scores make the causal estimate less sensitive to small nuisance errors.

### 21.2 Cross-Fitting

Cross-fitting:

```text
split data into folds
fit nuisance models on other folds
predict nuisance functions on held-out fold
estimate causal effect using out-of-fold nuisance predictions
```

This reduces overfitting bias.

### 21.3 When To Use DML

Use when:

- high-dimensional confounders
- flexible ML needed
- effect parameter is low-dimensional
- you need inference, not just prediction

Do not use DML as magic. It still needs identification assumptions and overlap.

## 22. Instrumental Variables

An instrument `Z` affects treatment `T` and affects outcome `Y` only through treatment.

Pattern:

```text
Z -> T -> Y
U -> T
U -> Y
```

`U` is unobserved confounding.

A valid instrument satisfies:

1. Relevance: `Z` affects `T`.
2. Exclusion: `Z` affects `Y` only through `T`.
3. Independence: `Z` is as-if random relative to confounders.
4. Monotonicity for LATE: no defiers, in common setup.

Examples:

- randomized assignment with noncompliance
- distance to facility
- lottery eligibility
- judge assignment
- policy threshold

### 22.1 Two-Stage Least Squares

Stage 1:

```text
T = a + b*Z + controls + error
```

Stage 2:

```text
Y = c + d*T_hat + controls + error
```

`d` estimates causal effect under IV assumptions.

### 22.2 IV Risks

- weak instruments
- exclusion restriction violations
- instrument affects outcome directly
- instrument correlated with unobserved confounders
- LATE applies only to compliers

IV estimates can be credible but narrow in interpretation.

## 23. Regression Discontinuity

Regression discontinuity uses a cutoff rule.

Example:

```text
students with score >= 80 receive scholarship
students with score < 80 do not
```

Near the cutoff, units are assumed comparable.

Estimate:

```text
effect = discontinuity in outcome at threshold
```

### 23.1 Sharp RD

Treatment determined exactly by cutoff.

### 23.2 Fuzzy RD

Cutoff changes probability of treatment but does not determine it perfectly.

This is like an IV design with threshold as instrument.

### 23.3 RD Diagnostics

Check:

- no manipulation around cutoff
- covariates continuous at cutoff
- outcome jump only at cutoff
- bandwidth sensitivity
- polynomial/order sensitivity
- density test around cutoff

### 23.4 RD Interpretation

RD estimates a local effect near the cutoff.

It may not generalize far from threshold.

## 24. Difference-In-Differences

Difference-in-differences compares changes over time between treated and control groups.

Basic setup:

```text
treated group before/after
control group before/after
```

Estimator:

```text
(treated_after - treated_before) - (control_after - control_before)
```

### 24.1 Key Assumption

Parallel trends:

```text
Absent treatment, treated and control groups would have changed similarly.
```

### 24.2 Event Studies

Plot effects by time relative to treatment.

Use to inspect:

- pre-trends
- dynamic effects
- delayed effects
- anticipation

### 24.3 Staggered Adoption

When units adopt treatment at different times, naive two-way fixed effects can be problematic with heterogeneous effects.

Modern approaches:

- group-time average treatment effects
- Callaway-Sant'Anna style estimators
- Sun-Abraham style event studies
- imputation-based DiD
- synthetic DiD

### 24.4 DiD Diagnostics

Check:

- pre-treatment trends
- treatment timing
- anticipation effects
- compositional changes
- spillovers
- robustness to control group choices

## 25. Synthetic Control

Synthetic control constructs a weighted combination of untreated units to match the treated unit before intervention.

Example:

```text
treated state: California
synthetic California: weighted average of other states
```

Then compare post-treatment outcomes.

Use when:

- one or few treated units
- many pre-treatment periods
- aggregate policy intervention
- good donor pool exists

### 25.1 Synthetic Control Diagnostics

Check:

- pre-period fit
- donor weights
- placebo tests
- leave-one-out sensitivity
- post-treatment divergence

### 25.2 Synthetic Difference-In-Differences

Synthetic DiD combines ideas from synthetic control and DiD, using unit and time weights to improve robustness in panel settings.

## 26. Interrupted Time Series

Interrupted time series studies a treated unit before and after intervention.

Use when:

- clear intervention time
- long pre/post history
- no good control group

Risks:

- concurrent shocks
- seasonality
- autocorrelation
- regression to mean
- trend misspecification

Better if paired with control series.

## 27. Time-Varying Treatments

Many treatments happen repeatedly over time.

Examples:

- medication dose over months
- repeated marketing contacts
- dynamic pricing
- treatment switching
- ICU interventions

Naive adjustment can fail when time-varying confounders are affected by prior treatment.

Example:

```text
past treatment -> current health status -> current treatment -> outcome
```

Health status is both:

- confounder for current treatment
- mediator of past treatment

Methods:

- g-formula
- marginal structural models
- inverse probability of treatment weighting
- structural nested models
- longitudinal TMLE

## 28. Mediation Analysis

Mediation asks:

```text
How much of treatment effect operates through mediator M?
```

Example:

```text
job training -> confidence -> employment
```

Effects:

- total effect
- direct effect
- indirect effect through mediator

Mediation is assumption-heavy because mediator-outcome confounding is difficult, especially when confounders are affected by treatment.

Use carefully.

## 29. Heterogeneous Treatment Effects

Average effects can hide important variation.

Example:

```text
ATE of campaign = 0
new users: +5%
loyal users: 0%
dormant users: -3%
```

CATE methods estimate:

```text
E[Y(1) - Y(0) | X = x]
```

Methods:

- subgroup analysis
- interaction regression
- causal trees
- causal forests
- S/T/X/R/DR learners
- Bayesian additive regression trees
- DML-based CATE

Use for:

- personalization
- uplift modeling
- policy targeting
- treatment selection

Beware:

- multiple testing
- noisy subgroup effects
- overfitting heterogeneity
- fairness and ethics

## 30. Uplift Modeling

Uplift modeling is applied CATE estimation, often in marketing/product.

Question:

```text
Who changes behavior because of treatment?
```

Not:

```text
Who is likely to have the outcome?
```

Examples:

- send coupon only to persuadable customers
- avoid retention emails to sleeping dogs
- choose treatment with highest incremental profit

Evaluation:

- uplift by decile
- Qini curve
- AUUC
- policy value
- incremental profit

## 31. Policy Learning

Policy learning chooses treatment rules.

A policy:

```text
pi(X) = treatment decision
```

Goal:

```text
maximize expected outcome, profit, welfare, or utility
```

Policy learning differs from effect estimation:

```text
effect estimation: how large is the effect?
policy learning: who should receive treatment?
```

Often, the best policy does not require perfect effect estimates everywhere. It needs correct decisions near the treatment threshold.

## 32. Causal Discovery

Causal discovery tries to learn causal graph structure from data.

Methods:

- constraint-based methods
- score-based methods
- functional causal models
- invariant causal prediction
- time-series causal discovery

Limits:

- assumptions are strong
- latent confounding is hard
- equivalent graphs may fit same data
- domain knowledge still matters

Use causal discovery as hypothesis generation, not automatic truth.

## 33. Sensitivity Analysis

Causal estimates depend on assumptions.

Sensitivity analysis asks:

```text
How strong would an unmeasured confounder need to be to change the conclusion?
```

Methods:

- Rosenbaum bounds
- E-values
- omitted variable sensitivity
- negative controls
- placebo outcomes
- placebo treatments
- tipping point analysis
- refutation tests

Good causal work does not say:

```text
We proved causality.
```

It says:

```text
Under these assumptions, estimate is X.
Here is why assumptions are plausible.
Here is how sensitive result is if assumptions fail.
```

## 34. Negative Controls

Negative control outcome:

```text
treatment should not affect this outcome
```

If you find an effect, confounding may exist.

Negative control exposure:

```text
this exposure should not affect outcome
```

If it appears to affect outcome, bias may exist.

Examples:

- future treatment predicting past outcome
- campaign affecting pre-campaign purchase
- medical treatment affecting unrelated pre-treatment condition

## 35. Refutation And Robustness Checks

Useful checks:

- placebo treatment
- placebo outcome
- random common cause
- subset refit
- bootstrap
- alternative adjustment sets
- alternative model forms
- trimming extreme weights
- balance diagnostics
- pre-trend checks
- falsification outcomes

DoWhy explicitly organizes causal analysis around modeling, identification, estimation, and refutation.

## 36. Causal Inference With Machine Learning

Machine learning helps estimate nuisance functions:

- outcome model
- treatment model
- propensity score
- CATE model
- high-dimensional controls

But ML alone does not create causality.

The causal part comes from:

- research design
- assumptions
- identification strategy
- valid comparison group

The ML part helps with:

- flexible function approximation
- heterogeneity
- high-dimensional confounding
- prediction of nuisance functions

Good framing:

```text
Causal ML = causal identification + ML estimation.
```

Not:

```text
ML model + causal vocabulary.
```

## 37. Inference And Uncertainty

Causal estimates need uncertainty.

Use:

- standard errors
- confidence intervals
- bootstrap
- cluster-robust standard errors
- randomization inference
- robust/sandwich estimators
- Bayesian posterior intervals

Cluster standard errors when treatment or outcome is correlated within groups:

- schools
- stores
- users over time
- regions
- hospitals

Do not report only point estimates.

## 38. Internal And External Validity

Internal validity:

```text
Is the causal effect credible for this study population?
```

External validity:

```text
Does it generalize to other populations, times, settings, or treatment versions?
```

Example:

```text
An A/B test on existing active users may not generalize to new users.
```

Transportability requires understanding how populations differ.

## 39. Interference And Network Effects

Standard causal inference often assumes no interference.

This fails when:

- users influence each other
- marketplace supply is limited
- ads create spillovers
- vaccines create herd effects
- peers affect education outcomes
- treatment changes prices for everyone

Solutions:

- cluster randomization
- graph/network experiments
- exposure mapping
- saturation designs
- market-level experiments

Ignoring interference can make individual-level experiments misleading.

## 40. Applications

### 40.1 Product A/B Testing

Questions:

- Did feature increase retention?
- Did onboarding change activation?
- Did notification increase engagement?

Key issues:

- novelty effects
- interference
- metric tradeoffs
- guardrail metrics
- sequential testing

### 40.2 Marketing

Questions:

- What is incremental lift of campaign?
- Who should receive offer?
- Which channel creates incremental profit?

Key issues:

- holdout groups
- attribution vs incrementality
- contact fatigue
- treatment cost

### 40.3 Healthcare

Questions:

- Does treatment improve outcome?
- Which patients benefit?
- What is effect of policy or screening?

Key issues:

- confounding by indication
- time-varying treatment
- censoring
- ethics
- clinical validity

### 40.4 Public Policy

Questions:

- Did minimum wage change employment?
- Did school reform improve outcomes?
- Did tax incentive affect investment?

Methods:

- DiD
- RD
- IV
- synthetic control

### 40.5 Marketplace And Platforms

Questions:

- Did ranking change increase buyer welfare?
- Did seller incentive increase supply?
- Did promotion cannibalize other sellers?

Key issues:

- interference
- equilibrium effects
- network spillovers

### 40.6 Machine Learning Systems

Questions:

- Did a ranking model improve long-term satisfaction?
- Did an ML alert reduce incident time?
- Did model intervention harm a subgroup?

Need:

- causal metrics
- experiments
- fairness analysis
- monitoring

## 41. Tooling

### 41.1 DoWhy

Best for:

- causal graph workflow
- assumptions
- identification
- estimation
- refutation
- sensitivity-style checks

DoWhy encourages the right causal workflow:

```text
model -> identify -> estimate -> refute
```

### 41.2 EconML

Best for:

- heterogeneous treatment effects
- DML
- DR learners
- causal forests
- CATE estimation
- policy learning

### 41.3 CausalML

Best for:

- uplift modeling
- meta-learners
- treatment effect estimation
- marketing-style causal ML

### 41.4 grf

R package for generalized random forests.

Best for:

- causal forests
- heterogeneous treatment effects
- forest-based inference

### 41.5 MatchIt / WeightIt / cobalt

R ecosystem for:

- matching
- weighting
- balance diagnostics
- covariate balance plots

### 41.6 did / fixest / synthdid

Useful for:

- difference-in-differences
- staggered adoption
- fixed effects
- synthetic DiD

### 41.7 CausalPy / PyMC Ecosystem

Useful for:

- Bayesian causal modeling
- synthetic controls
- interrupted time series

## 42. Practical End-To-End Workflow

### Step 1: Define The Target Trial

Write:

```text
Units:
Treatment:
Control:
Eligibility:
Assignment time:
Outcome:
Follow-up window:
Causal estimand:
```

### Step 2: Draw The DAG

Identify:

- treatment
- outcome
- confounders
- mediators
- colliders
- instruments
- selection mechanisms

### Step 3: Choose Identification Strategy

Options:

- randomized experiment
- backdoor adjustment
- IV
- RD
- DiD
- synthetic control
- frontdoor

### Step 4: Build Point-In-Time Dataset

Use only information available before treatment.

Track:

- treatment time
- feature time
- outcome window
- censoring
- missingness

### Step 5: Check Assumptions And Diagnostics

Check:

- balance
- overlap
- pre-trends
- manipulation around cutoff
- instrument strength
- missingness
- interference

### Step 6: Estimate

Use a method aligned with design:

- experiment: difference in means/regression
- backdoor: regression/matching/IPW/AIPW/TMLE/DML
- IV: 2SLS/LATE
- RD: local regression
- DiD: modern DiD estimator
- synthetic control: donor weighting

### Step 7: Quantify Uncertainty

Use appropriate standard errors or bootstrap.

### Step 8: Stress Test

Run:

- sensitivity analysis
- negative controls
- placebo tests
- alternative adjustment sets
- subgroup checks
- robustness to trimming/weights

### Step 9: Communicate Carefully

Report:

- estimand
- estimate
- uncertainty
- assumptions
- diagnostics
- limitations
- decision relevance

## 43. Common Pitfalls

| Pitfall | Why It Is Bad | Fix |
| --- | --- | --- |
| treating prediction as causation | associations can be confounded | define intervention and counterfactual |
| vague treatment | causal effect not well-defined | specify treatment version |
| post-treatment controls | blocks causal paths or creates bias | use pre-treatment covariates |
| conditioning on collider | creates spurious association | use DAG |
| no overlap | relies on extrapolation | trim/change estimand |
| unmeasured confounding | biased observational estimate | better design/sensitivity/IV |
| ignoring interference | estimates wrong effect | cluster/network design |
| bad outcome window | misses or dilutes effect | align with mechanism |
| overfitting CATE | false heterogeneity | honest estimation/holdout |
| no uncertainty | overconfident decisions | standard errors/CI/bootstrap |
| multiple testing | false subgroup effects | correction/pre-specification |
| no sensitivity analysis | assumptions hidden | stress-test assumptions |

## 44. Causal Inference vs Related Concepts

### 44.1 Correlation

Correlation:

```text
X and Y move together
```

Causation:

```text
changing X changes Y
```

### 44.2 Attribution

Marketing attribution often assigns credit to touchpoints.

Causal incrementality asks:

```text
What would have happened without the touchpoint?
```

Attribution is not automatically causal.

### 44.3 Forecasting

Forecasting predicts future outcomes under current process.

Causal inference predicts effects of interventions.

### 44.4 Explainability

Explainability says why a model predicted something.

Causal inference says what happens if we intervene.

Feature importance is not causal importance.

### 44.5 Uplift Modeling

Uplift modeling estimates heterogeneous treatment effects for targeting.

It is an application of causal inference.

## 45. Interview-Ready Answers

### "What is causal inference?"

```text
Causal inference estimates the effect of an intervention by comparing observed outcomes to credible counterfactual outcomes. It is different from prediction because it asks what would happen if we changed treatment, not just what outcome is likely under observed behavior.
```

### "What are the main assumptions?"

```text
The core assumptions are consistency, exchangeability or no unmeasured confounding, positivity or overlap, and SUTVA, which includes no interference and well-defined treatments. The specific assumptions depend on the design, such as parallel trends for DiD, exclusion restriction for IV, or no manipulation around the cutoff for RD.
```

### "How do you choose a causal method?"

```text
I start with the identification strategy, not the estimator. If treatment is randomized, use experimental analysis. If treatment is as-if random near a cutoff, use regression discontinuity. If there is a credible instrument, use IV. If there is a policy change with comparable untreated units over time, use DiD or synthetic control. If relying on observed confounders, use adjustment methods such as matching, weighting, outcome regression, AIPW, TMLE, or DML.
```

### "What is a confounder?"

```text
A confounder is a pre-treatment variable that affects both treatment assignment and the outcome. If not adjusted, it opens a noncausal path between treatment and outcome and biases the effect estimate.
```

### "What is a collider?"

```text
A collider is a variable caused by two other variables. Conditioning on it can create an association between its causes, even if none existed before. That is why causal adjustment cannot be done by blindly controlling for every variable.
```

### "What is the difference between ATE and CATE?"

```text
ATE is the average treatment effect across a population. CATE is the treatment effect conditional on features. ATE answers whether a treatment works on average; CATE answers for whom it works better or worse.
```

### "What is double machine learning?"

```text
Double machine learning uses flexible ML to estimate nuisance functions like the outcome model and propensity model, then uses orthogonal scores and cross-fitting so the final causal estimate is less sensitive to nuisance-model overfitting or small errors.
```

### "How do you validate a causal estimate?"

```text
You validate the design and assumptions, not just the model. I check balance, overlap, pre-trends for DiD, cutoff manipulation for RD, instrument strength and exclusion plausibility for IV, placebo outcomes, negative controls, robustness across specifications, and sensitivity to unmeasured confounding.
```

## 46. Quick Glossary

| Term | Short Meaning |
| --- | --- |
| causal effect | difference between outcomes under interventions |
| counterfactual | what would have happened under alternative treatment |
| potential outcome | outcome under a treatment condition |
| ATE | average treatment effect |
| ATT | average treatment effect on treated |
| CATE | conditional average treatment effect |
| ITT | effect of treatment assignment |
| LATE | effect for instrument-induced compliers |
| DAG | causal graph |
| SCM | structural causal model |
| confounder | common cause of treatment and outcome |
| mediator | variable on causal path |
| collider | variable caused by two variables |
| backdoor path | noncausal path creating confounding |
| propensity score | probability of treatment given covariates |
| matching | compare similar treated/control units |
| IPW | inverse probability weighting |
| AIPW | augmented inverse probability weighting |
| TMLE | targeted maximum likelihood estimation |
| DML | double/debiased machine learning |
| IV | instrumental variables |
| RD | regression discontinuity |
| DiD | difference-in-differences |
| synthetic control | weighted control group matching treated pre-period |
| positivity | treatment/control support for covariate patterns |
| exchangeability | treated/control comparable after adjustment |
| SUTVA | no interference and well-defined treatment |

## 47. References

- Free textbook: [Causal Inference: What If](https://www.hsph.harvard.edu/miguel-hernan/causal-inference-book/)
- Potential outcomes textbook: [Causal Inference for Statistics, Social, and Biomedical Sciences](https://www.cambridge.org/core/books/causal-inference-for-statistics-social-and-biomedical-sciences/71126BE90C58F1A431FE9B2DD07938AB)
- Applied econometrics overview: [The State of Applied Econometrics: Causality and Policy Evaluation](https://www.aeaweb.org/articles?id=10.1257%2Fjep.31.2.3)
- Randomized experiments review: [The Econometrics of Randomized Experiments](https://arxiv.org/abs/1607.00698)
- DoWhy documentation: [DoWhy](https://www.pywhy.org/dowhy/main/index.html)
- DoWhy paper: [DoWhy: An End-to-End Library for Causal Inference](https://arxiv.org/abs/2011.04216)
- EconML documentation: [Machine Learning Based Estimation of Heterogeneous Treatment Effects](https://econml.azurewebsites.net/spec/motivation.html)
- CausalML documentation: [CausalML](https://causalml.readthedocs.io/)
- Generalized random forests: [Generalized Random Forests](https://arxiv.org/abs/1610.01271)
- grf package: [Generalized Random Forests](https://grf-labs.github.io/grf/index.html)
- Causal forests: [Estimation and Inference of Heterogeneous Treatment Effects using Random Forests](https://arxiv.org/abs/1510.04342)
- Meta-learners: [Meta-learners for Estimating Heterogeneous Treatment Effects using Machine Learning](https://arxiv.org/abs/1706.03461)
- R-learner: [Quasi-Oracle Estimation of Heterogeneous Treatment Effects](https://arxiv.org/abs/1712.04912)
- Double ML: [Double/debiased machine learning for treatment and structural parameters](https://academic.oup.com/ectj/article/21/1/C1/5056401)
- AIPW tutorial: [Augmented Inverse Probability Weighting and the Double Robustness Property](https://journals.sagepub.com/doi/10.1177/0272989X211027181)
- TMLE overview: [Targeted Maximum Likelihood Estimation for Causal Inference in Observational Studies](https://academic.oup.com/aje/article/185/1/65/2662306)
- Regression discontinuity guide: [Regression Discontinuity Designs: A Guide to Practice](https://scholar.harvard.edu/files/imbens/files/regression_discontinuity_designs_a_guide_to_practice.pdf)
- Synthetic DiD: [Synthetic Difference-in-Differences](https://www.aeaweb.org/articles?id=10.1257/aer.20190159)
- Sensitivity analysis: [Sensitivity Analysis of Linear Structural Causal Models](https://proceedings.mlr.press/v97/cinelli19a.html)

