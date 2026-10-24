# Executed results and verification

All movement, model and campus data below are synthetic. These numbers come from executed model evaluation and individual-agent simulations included in this package. They are not real-campus observations.

## Held-out model evaluation

| Metric | Random Forest | Persistence baseline |
|---|---:|---:|
| MAE (people) | 2.335068 | 2.857928 |
| RMSE (people) | 3.176263 | 4.014517 |
| R² | 0.820231 | 0.712823 |

Selected parameters: {"n_estimators": 80, "max_depth": 12, "min_samples_leaf": 4, "max_features": 0.85}.
Validation-only tuning and chronological partitions are documented in MODEL_CARD.md. All held-out predictions are retained in data/test_predictions.csv.gz.

## Default scenarios, seed 2026

| Scenario | People | Distance mean (min) | Congestion mean (min) | Adaptive mean (min) | Improvement vs distance |
|---|---:|---:|---:|---:|---:|
| normal | 120 | 4.35 | 4.35 | 4.35 | 0.00% |
| lunch | 450 | 33.48 | 21.06 | 6.92 | 79.35% |
| exam | 550 | 6.29 | 6.13 | 4.81 | 23.59% |
| closure | 300 | 41.03 | 28.56 | 10.82 | 73.62% |
| self induced | 500 | 64.97 | 64.97 | 25.77 | 60.34% |

All default trials completed every requested journey within the 7,200-second horizon. **Normal movement showed no improvement**. Benefits in these chosen synthetic rush scenarios do not imply benefits on every possible demand pattern.

### Normal

| Strategy | Mean (s) | P95 (s) | Peak occupancy | Above capacity (edge·s) | Reroutes/person | Solver time (ms) | Completed |
|---|---:|---:|---:|---:|---:|---:|---:|
| distance | 261.19 | 478.17 | 7 | 0 | 0.0000 | 15.80 | 120/120 |
| congestion | 261.19 | 478.17 | 7 | 0 | 0.0000 | 12.58 | 120/120 |
| adaptive | 261.19 | 478.17 | 7 | 0 | 0.0000 | 440.97 | 120/120 |

### Lunch

| Strategy | Mean (s) | P95 (s) | Peak occupancy | Above capacity (edge·s) | Reroutes/person | Solver time (ms) | Completed |
|---|---:|---:|---:|---:|---:|---:|---:|
| distance | 2008.97 | 2919.30 | 255 | 6030 | 0.0000 | 6.01 | 450/450 |
| congestion | 1263.46 | 2497.43 | 236 | 3910 | 0.0000 | 7.98 | 450/450 |
| adaptive | 414.90 | 613.05 | 99 | 200 | 0.1089 | 1011.66 | 450/450 |

### Exam

| Strategy | Mean (s) | P95 (s) | Peak occupancy | Above capacity (edge·s) | Reroutes/person | Solver time (ms) | Completed |
|---|---:|---:|---:|---:|---:|---:|---:|
| distance | 377.43 | 604.92 | 119 | 810 | 0.0000 | 5.93 | 550/550 |
| congestion | 367.59 | 668.31 | 131 | 570 | 0.0000 | 8.57 | 550/550 |
| adaptive | 288.41 | 413.77 | 78 | 0 | 0.0909 | 697.22 | 550/550 |

### Closure

| Strategy | Mean (s) | P95 (s) | Peak occupancy | Above capacity (edge·s) | Reroutes/person | Solver time (ms) | Completed |
|---|---:|---:|---:|---:|---:|---:|---:|
| distance | 2461.57 | 3411.41 | 237 | 4660 | 0.4400 | 5.02 | 300/300 |
| congestion | 1713.56 | 2779.74 | 203 | 3485 | 0.1833 | 5.33 | 300/300 |
| adaptive | 649.29 | 795.65 | 122 | 515 | 0.0867 | 1381.10 | 300/300 |

### Self Induced

| Strategy | Mean (s) | P95 (s) | Peak occupancy | Above capacity (edge·s) | Reroutes/person | Solver time (ms) | Completed |
|---|---:|---:|---:|---:|---:|---:|---:|
| distance | 3897.90 | 4260.00 | 255 | 7100 | 0.0000 | 1.28 | 500/500 |
| congestion | 3897.90 | 4260.00 | 255 | 7100 | 0.0000 | 1.22 | 500/500 |
| adaptive | 1546.02 | 1965.00 | 290 | 3475 | 0.4820 | 2304.96 | 500/500 |

## Verification performed

| Check | Result |
|---|---|
| Python graph, routing, ML, simulation and API tests | 31 passed |
| React controls and real FastAPI integration | 6 passed |
| Actual production ESM bundle in jsdom | Passed: map, route, ML, experiments, simulation pages |
| Vite production build | Passed |
| Real HTTP launcher startup/shutdown/restart | Passed |
| Fresh virtual environment installation and HTTP launch | Passed |
| Python suite in that fresh environment | 31 passed |

The Python suite includes graph connectivity, solver agreement with NetworkX, closures and disconnected destinations, route allocation, congestion-driven path changes, physical movement, pedestrian conservation, occupancy ceilings, pause/reset, scenario smoke checks, multi-OD demand, API validation, SQLite experiment storage, asset serving and independent recomputation of ML metrics.

The React suite uses real HTTP API calls; Leaflet and Recharts are rendered in jsdom. It verifies all four dashboard pages, map SVG updates, different route demands, real allocations, moving agent markers, closure/reopening, pause/resume/reset, scenario presets, OD controls, model charts and controlled comparisons. It substitutes DOM geometry/ResizeObserver because jsdom has no layout engine; it does not mock API replies.

The production smoke dynamically executes the delivered JavaScript chunks, catches window errors, calculates a real route, and loads analytics/experiment/live pages. The HTTP restart check launches run.py as a subprocess, moves pedestrians, stops it, starts it again and checks a clean simulation/model/graph.

## Verification limits

No supported full browser QA surface was available in the execution environment. There was **no screenshot-based or real-browser visual verification**. Mobile touch, projector layout, rendering pixels and browser-specific performance still require a local browser check. This is explicitly distinguished from successful React DOM and production-bundle execution.

A Starlette deprecation warning about the httpx TestClient transport occurred; it did not affect any test result. Windows launcher scripts are supplied; the executable launcher and integration tests were exercised on Linux/Python 3.12.

## Determinism

Random departure times and OD pairs use the documented seed. The simultaneous fixed-OD self-induced scenario has no random departures or OD choices, so changing its seed intentionally does not create independent stochastic trials. The stored default scenarios use seed 2026.

## Practical limits

Travel estimates in the route finder are snapshot values; the tables above measure actual trips with admission queues and physical movement. Candidate sets and reservations are bounded heuristics. Nodes have unbounded waiting queues; the density-speed curve is an explicit assumption. Prediction performance on the synthetic count dataset does not validate forecasts in a real crowd. Range warnings identify live features outside training bounds.

Execution times exclude forest inference and vary by computer. Compare the other metrics using identical demand/seed/intensity and the same horizon. Do not calculate a population-wide improvement from incomplete runs.

## Primary implementation references

- FastAPI static files: https://fastapi.tiangolo.com/tutorial/static-files/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Leaflet non-geographical coordinates: https://leafletjs.com/examples/crs-simple/crs-simple.html
- scikit-learn chronological splitting guidance: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html

The code uses complete-day partitions with no cross-day targets rather than applying row-wise TimeSeriesSplit to the multi-pathway dataset.
