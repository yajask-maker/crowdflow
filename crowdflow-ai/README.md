# CrowdFlow AI

**Self-Adaptive Shortest Path Optimization Using Machine Learning and Predicted Human Movement**

A working local mini-project for third-year BTech AI & Data Science: a React campus dashboard connected to a Python/FastAPI backend, a trained Random Forest, explicit Dijkstra/A* implementations, and an individual pedestrian simulator.

The central idea is that recommendations change the conditions being predicted. CrowdFlow reserves the future occupancy of assigned groups, considers alternative routes with limited overlap, and revises routes at junctions when the expected saving is substantial.

All campus locations and movement data are fictional/synthetic. Results are executed simulation measurements, not claims about a real university.

## Fastest way to run

Requirements: **Python 3.12**, internet for the initial dependency installation, and a modern desktop browser. The ZIP includes the trained model, generated data, and built frontend. **Node.js is not needed to run the supplied build.** No paid APIs, keys, map tiles, or external services are used during the demo.

### Windows

Extract the ZIP. Open the `crowdflow-ai` folder and double-click **setup.bat** once, then **run.bat**.

Or use PowerShell/Command Prompt inside the extracted folder:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py
```

Open **http://127.0.0.1:8000** in your browser. API documentation: **http://127.0.0.1:8000/docs**. Stop the server with Ctrl+C. Leave the terminal open while demonstrating.

### Linux / macOS

```bash
bash setup.sh
.venv/bin/python run.py
```

If your system calls Python 3.12 `python3.12`, use `python3.12 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt`.

### Existing Python environment

```bash
python -m pip install -r requirements.txt
python run.py
```

Do not open `frontend/dist/index.html` directly: the dashboard needs its Python API.

## A live demonstration in six steps

1. In Overview, select **Main Entrance → Cafeteria**, 500 pedestrians, CrowdFlow adaptive. Calculate the route and inspect the allocations and coloured paths.
2. In Live simulation, choose **Self-Induced Congestion**, population 500, CrowdFlow adaptive, and playback 120×. Start the simulation. Dots move along pathways and densities update.
3. Pause, click a pathway, close it, and resume. Existing walkers finish the current edge safely; following trips are replanned at nodes. Reopen it to restore access.
4. Open ML intelligence. Explain MAE, RMSE, R², the persistence baseline, held-out actual vs predicted counts, feature importance and residual distribution.
5. Open Experiments and run the same scenario. Compare measured means, P95 times, capacity violations, reroutes and solver time across all three strategies.
6. Select Normal Campus Movement and rerun. Show that an adaptive method does not always produce an improvement. Reset or restart for the next demonstration.

`docs/DEMO_GUIDE.md` contains the five scenarios, a suggested presentation script, and viva answers.

## What is included

| Folder/file | Purpose |
|---|---|
| `frontend/` | React + Vite + Tailwind; offline Leaflet map; Recharts; production `dist/` build |
| `backend/` | FastAPI routes, Pydantic validation, SQLite experiment/action storage |
| `algorithms/` | Fictional campus graph; explicit Dijkstra/A*; candidate diversification; feedback allocation |
| `simulation/` | Individual pedestrians; scenarios; controlled three-strategy experiments |
| `ml/` | Feature engineering; training; saved `model.joblib`; computed `metrics.json`; inference |
| `data/` | Reproducible generator; compressed dataset; test predictions; computed benchmarks |
| `tests/` | Python tests, real HTTP restart check, real-API React integration runner, production bundle smoke |
| `docs/` | Architecture, algorithms, data/model card, demo guide, measured results and verification limits |
| `run.py` | One-port local launcher |
| `requirements.txt` | Exact tested direct Python dependency versions |
| `frontend/package-lock.json` | Exact frontend dependency resolution |

The compressed dataset is a normal CSV in gzip format: `pandas.read_csv('data/pedestrian_counts.csv.gz')` opens it directly.

## Regenerate the dataset, model and experiments

Run from the project root with the installed Python environment:

```bash
python -m data.generate
python -m ml.train
python -m simulation.compare
```

Generation seed: 2026. The model predicts pathway occupancy five minutes ahead from current/past measurements and known schedules. Days 0–17 train, 18–22 validate hyperparameters, 23–27 test. The selected model is refit on days 0–22 before the untouched test evaluation. No future arrival counts enter the features.

`python run.py --retrain` retrains the model before launch. If changing scikit-learn versions, regenerate benchmarks as well. The supplied model was trained with scikit-learn 1.8.0; use the pinned requirements for the simplest setup.

## Run the verification suites

Python core/API tests:

```bash
python -m pytest tests -q
python tests/check_restart.py
```

For frontend verification, install Node.js 22+ and the locked development dependencies:

```bash
cd frontend
npm ci
npm run build
cd ..
python tests/run_ui_checks.py
```

The UI runner owns a temporary local API server, executes all six React integration tests against it, and executes the actual production ESM bundle in jsdom. Stop any other server on port 8000 before using this runner. The restart check uses port 8010. These checks make actual HTTP calls; frontend API responses are not mocked.

**Verification scope:** 31 Python tests and 6 React/real-API tests passed, along with production-bundle execution and actual HTTP startup/shutdown/restart. The environment did not provide a supported full browser QA surface. Pixel layout, mobile touch, and performance in Chrome/Firefox still need a local browser check. DOM execution is not claimed as screenshot or real-browser verification.

## Frontend development

Terminal 1, project root:

```bash
python run.py
```

Terminal 2:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite proxies API calls to port 8000. After editing, `npm run build` updates the frontend served by FastAPI. The entire local demo works offline after dependencies are installed.

## API summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/graph` | All nodes and pathway state |
| GET | `/locations` | Campus locations |
| GET | `/scenarios` | Five ready-to-run scenario configurations |
| POST | `/predict` | Batched five-minute ML occupancy predictions and range warnings |
| POST | `/route` | Route candidate allocations and snapshot estimates |
| POST | `/simulate/start` | New scenario or explicit multi-OD demand |
| POST | `/simulate/step` | Advance 1–60 ticks; each tick is 5 seconds |
| POST | `/simulate/pause` | Pause the simulation |
| POST | `/simulate/resume` | Resume a paused simulation |
| POST | `/simulate/reset` | Restore the open campus and empty state |
| POST | `/simulate/closure` | Close/reopen a pathway |
| GET | `/simulation/state` | Positions, graph state, counts and time series |
| GET | `/analytics` | Current metrics, last experiment and SQLite experiment index |
| GET | `/model/metrics` | Executed model evaluation, feature importance and residuals |
| POST | `/compare` | Run the three strategies with identical inputs |
| GET | `/benchmarks` | Computed packaged default scenarios |
| GET | `/health` | API/model readiness |

Interactive schemas and examples are generated at `/docs`. No authentication is needed for this local demonstrator. Bind to 127.0.0.1 for a single-computer presentation.

## Correctness and limitations

- Pedestrian counts are conserved: pending + waiting + walking + completed equals population. Edge occupancy equals the number physically walking on that edge.
- Occupancy can exceed **comfort** capacity; this is the congestion signal. It cannot exceed the separate **physical admission** ceiling. Extra pedestrians queue at nodes.
- Every route uses open edges. Disconnected pedestrians wait; the route API returns HTTP 409 when no route is available. Identical endpoints, zero demand, invalid locations and negative demand are handled.
- Walkers do not teleport. Movement follows graph geometry. An edge closure stops new entries and lets those already inside finish.
- Adaptive allocation uses a conservative snapshot and fluid queue estimate, not a globally optimal time-expanded traffic assignment. Only six candidate paths and five-person assignment groups are considered.
- The RF is evaluated on a stochastic count process. The agent simulator is a different domain; extreme density can exceed its training range. The dashboard reports range warnings, and adaptive routing uses current occupancy as a floor. This does not eliminate model error.
- A tick can add up to five seconds of node delay. All algorithms use the same tick and physical dynamics.
- Speed controls affect playback, not the equations. Closing the dashboard stops its automatic step requests; API clients can still advance the state explicitly.
- The API owns one shared in-memory simulation. SQLite retains experiments and action logs, not a resumable live agent state. This is a local single-user college demonstrator.
- All comparison statistics are measured. Incomplete runs show censored completed-trip statistics and do not claim an overall improvement. Low-density and unusual demand can show no gain or worse performance.

See `docs/VERIFIED_RESULTS.md` for exact results and `docs/MODEL_CARD.md` for assumptions.

## Troubleshooting

- **ModuleNotFoundError:** run setup, or install requirements with the same Python used to launch.
- **Port already in use:** stop the previous terminal, or run `python run.py --port 8001` and open http://127.0.0.1:8001.
- **Blank page after opening a file:** use the server URL, not the HTML file directly.
- **API disconnected:** keep the backend terminal running; reload the page after startup.
- **Model version message:** install the supplied requirements or retrain with the current scikit-learn.
- **Population validation error in Experiments:** comparisons are limited to 1,000 pedestrians; the live simulator allows 1,500.
- **No apparent movement:** choose a rush scenario or allow pending arrivals to reach their departure times; increase playback speed.
- **No route after closures:** reopen pathways or reset. Waiting pedestrians are retained, not dropped.

## College rubric mapping

| Criterion | Evidence |
|---|---|
| Problem definition (5 marks) | Recommendations can create the congestion they ignore; narrow central campus corridor demonstrates the failure mode |
| Methodology and analysis (5 marks) | Executed chronological RF evaluation with baseline; explicit graph solvers; reservation-based assignment; identical-input experiments and conservation tests |
| Presentation and communication (5 marks) | Interactive map, route allocation, live movement, five scenarios, model analytics, transparent measured comparisons and a structured demonstration guide |

Source code is provided under the MIT License. Dependency licenses remain with their respective projects.
