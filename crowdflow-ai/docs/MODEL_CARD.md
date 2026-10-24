# Dataset and model card

## Intended use

Five-minute pathway occupancy prediction for a fictional campus demonstration. It supports routing experiments and explanations of regression, chronological evaluation and feedback-aware systems. It is not validated for operational crowd safety, a real campus, or emergency evacuation.

## Synthetic dataset

`data/generate.py` produces 28 independent campus days at five-minute intervals from 07:00 to 20:00. There are 66 pathways and 155 labelled records per pathway-day, for 286,440 records. The last state of each day is retained only as a target for the preceding record, preventing a label from crossing day partitions.

Seed 2026 is used through NumPy's default_rng. Every row is marked synthetic. `data/assumptions.json` captures units, schedules and generation assumptions.

Arrivals are Poisson draws, departing survivors are binomial draws, daily demand is lognormal with a weekend factor, and latent demand varies with temporal correlation. Class changes, lunchtime, examination sessions, event flags and pathway zones influence expected arrivals. Pathway occupancy also changes survival probability. Random arrivals/departures and hidden variation ensure a forecast cannot reproduce every target exactly.

The arrival-rate feature is **the observed previous interval's arrivals divided by five minutes**. Arrivals used to generate the target are independent later draws and are not included in the current feature record.

## Features

| Feature | Meaning / availability |
|---|---|
| time_sin, time_cos | Cyclic time-of-day representation, known at departure |
| weekday | 0–6, known calendar value |
| class_change | Known timetable windows around 09, 10, 11, 14, 15 and 16 hours |
| lunch | Known 12:00–13:30 window |
| exam, event | Known scenario/calendar flags |
| occupancy | Current measured/simulated count |
| lag_5, lag_10 | Previous five- and ten-minute counts |
| rolling_mean | Mean of current and past two count states |
| arrival_rate | Observed past five-minute arrivals per minute |
| distance, width, capacity, zone | Static pathway geometry and activity context |

Pathway ID is used to align targets and time series, not as a learned categorical shortcut. Future occupancy and future arrival counts never enter the feature matrix. No fitted scaling is needed for a Random Forest; feature ordering is fixed centrally in `ml/features.py`.

## Training and selection

- Train: days 0–17, 184,140 rows.
- Validation: days 18–22, 51,150 rows.
- Test: days 23–27, 51,150 rows.
- Hyperparameter candidates: depths 12, 18, unlimited; corresponding minimum leaves 4, 4, 8. All use 80 trees and max_features 0.85.
- Select the lowest validation MAE; refit selected parameters on days 0–22; evaluate once on days 23–27.
- Baseline: predict current occupancy again (persistence).

All edges from a calendar day are kept in one partition. No label crosses the final day row. Thus random row splits do not leak correlated states from the same day across evaluation boundaries.

`ml/metrics.json` is the authoritative executed report. It contains tuning results, selected parameters, split counts, version metadata, metrics, error histogram, test time series, and training feature ranges. `data/test_predictions.csv.gz` retains all held-out predictions so reported scores can be recomputed independently. Automated tests do so.

## Interpretation

MAE and RMSE are in people; R² is a regression score, not classification accuracy. The model's feature-importance plot is impurity-based importance. Correlated lag features can share or distort importance; importance is not a causal explanation. The actual vs predicted plot uses pathway P024 on held-out day 23, with the five-minute target time indexed by the feature record's time.

## Live simulation domain and safeguards

The training process is a stochastic five-minute count model. The live simulator tracks agents at five-second intervals using admission limits and a density-speed curve. These are related but distinct data-generating processes. Strong surges may exceed the forest's training range, and tree regressors cannot extrapolate reliably.

Inference checks feature ranges and returns explicit warnings. Adaptive routing uses max(prediction, current occupancy) plus commitments; this protects against some underprediction but is not a calibrated uncertainty bound. Live lag history uses five-minute sampled states; forecasts within a bin use those sampled past counts with the current count. Fresh runs warm-start lag history from their initial occupancy.

The route finder uses its selected departure schedule together with the current graph measurements; it is not a multi-hour future demand forecast. Scenario flags come from the selected live scenario. Controls for day and class/lunch times affect known schedule features.

No external campus tracking data, faces, identities, camera feeds or personal movement records are collected.

## Reproducibility and serialisation

The included model uses scikit-learn 1.8.0 and joblib. Install pinned requirements or retrain when changing versions. Only load trusted local joblib files. Inference uses one forest thread; training may parallelize. The underlying seed, dataset and selected parameters are fixed and documented.
