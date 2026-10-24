# College demonstration guide

## Ready-to-run scenarios

| Scenario | Population | Departure clock | Demand pattern | What to show |
|---|---:|---|---|---|
| Normal Campus Movement | 120 | 09:30 | Multiple random OD trips spread over five minutes | At low density, shortest distance can already be sufficient |
| Lunch Break Congestion | 450 | 12:15 | Multiple buildings to cafeteria within 60 seconds | Convergence at a destination and route distribution |
| Examination Hall Rush | 550 | 08:55 | Hostels/classrooms to examination hall over 90 seconds | Schedule flag, multi-origin demand and rush congestion |
| Unexpected Corridor Closure | 300 | 11:00 | Entrance to cafeteria over two minutes; P025 closes at 60 seconds | Safe completion of current edge and node-level replanning |
| Self-Induced Congestion | 500 | 11:50 | All students request entrance to cafeteria simultaneously | Routing recommendations create the bottleneck they initially ignore |

Selecting a preset updates population and start time. Starting or restarting resets the previous network and applies the selected configuration. Manual closures can be reopened. To compare strategies, choose the same scenario, count, intensity and seed in Experiments.

## Simultaneous class-change setup

In Live simulation, set start time to 10:00. Expand Advanced and add two OD requests: AI & DS Block → Engineering Block, 100 people, departure 0; Engineering Block → Science Laboratories, 100 people, departure 0. Added rows replace the preset-generated population. Start to release both class groups on the same tick. The class-change feature is derived from the known timetable window.

## Suggested five-to-seven-minute presentation

### 1. Problem (40 seconds)

“Our project is CrowdFlow AI, a campus pedestrian navigation system. A shortest route is not necessarily the fastest route when many students choose it together. There is an extra feedback problem: our own recommendations change the crowd. We investigate whether assigning students across alternatives can reduce that congestion.”

### 2. Campus and algorithms (60 seconds)

“This is Meridian University, a fictional campus with 36 locations and 66 pathways. Green paths are flowing freely, amber paths are becoming busy, and red paths exceed a comfort threshold. A separate hard limit prevents impossible edge occupancy. The first algorithm minimizes metres. The second minimizes Random Forest predicted travel time. CrowdFlow adds the pedestrians it is about to recommend before allocating the next group.”

Select Main Entrance to Cafeteria, 500 people, CrowdFlow adaptive. Calculate. Open a route's details and explain the number of pedestrians assigned to each path. Estimates are snapshot estimates, not measured journey results.

### 3. Live feedback (90 seconds)

Choose Self-Induced Congestion with adaptive routing and 120× playback. Start. Observe dots progressing, pathway occupancy and completed trips. Pause; inspect a central pathway; close it; resume. Explain that walkers finish the edge they are already on and following decisions occur at nodes. Reopen and restart if needed.

“To avoid constantly changing instructions, discretionary rerouting requires a 20% saving, more than 15 seconds saved and a 30-second interval. We also reserve the remaining routes of people already assigned, so a vacant-looking alternative is not treated as empty when many others are heading toward it.”

### 4. Actual ML evaluation (60 seconds)

Open ML intelligence.

“This is a real Random Forest trained on reproducible synthetic movement counts. We separate days chronologically: training days, validation days for choosing hyperparameters, then untouched test days. We compare it with simply predicting the present count again. MAE and RMSE are numbers of pedestrians. R² is a regression score, not accuracy. The graphs and values come from the executed evaluation.”

Point to the actual/predicted time series, baseline metric, feature importance and residual histogram. Explain that the simulator can exceed the model's training densities and that range warnings are shown.

### 5. Controlled experiments and honesty (90 seconds)

Open Experiments. Run Self-Induced Congestion with its default demand. Point to mean/P95 journey times, peak occupancy and edge-seconds above capacity. Explain that all three strategies used identical requests and physical dynamics. Run Normal Campus Movement next and show no improvement if the result is unchanged.

“Our innovation is the feedback-aware assignment loop. It is a bounded heuristic, not a guaranteed global optimum. The measured improvement depends on the synthetic scenario. Low-density cases can tie or be worse; we do not force the adaptive algorithm to win.”

## Viva questions and answers

**What exactly is the machine learning target?**
The occupancy of one pathway five minutes after the feature timestamp.

**Why Random Forest?**
It handles nonlinear relationships between crowd counts, schedules and pathway characteristics, without requiring a neural-network training setup. A persistence baseline shows whether the extra model adds value.

**Why not use Dijkstra alone?**
Dijkstra correctly finds the minimum sum of its supplied costs. Distance costs ignore crowd delay. Forecast costs still omit the effect of new recommendations. The issue is the changing edge costs and assignment feedback, not Dijkstra being incorrect.

**Where is feedback represented?**
In the reservation counter. Assigning a group increases estimated occupancy on every pathway in its route before the next group is evaluated. Remaining commitments also influence node rerouting.

**Are you solving the shortest path or a traffic assignment problem?**
Both. Graph search supplies candidate routes; the adaptive component distributes demand over them. This is a heuristic traffic assignment built around shortest-path search.

**What does capacity mean?**
Comfort capacity is a threshold for congestion. The physical ceiling is a higher admission limit. Extra agents wait at nodes and are not added beyond the physical ceiling.

**How do you know there is no data leakage?**
All rows from a day remain in one partition, targets do not cross day boundaries, features use current/past counts and already-known schedules, and hyperparameters are chosen with validation data only.

**What is self-induced congestion?**
A recommended route starts attractive but becomes slow because many users receive that same recommendation. Those recommendations are themselves part of future demand.

**Is the A* heuristic admissible?**
Yes. Straight-line remaining distance divided by the maximum normal speed cannot exceed the travel time of any feasible remaining path.

**What happens when all access to a destination is closed?**
The route API returns no-path HTTP 409. Simulation agents stay waiting, and resume when a connection reopens.

**Why can the prediction be wrong during a large surge?**
The live individual-agent process differs from the synthetic training count process, and the RF cannot extrapolate beyond learned ranges. We report these limits and use current occupancy in adaptive costs.

**Does better mean always faster?**
No. A route may be physically longer and unnecessary at low demand. We report the actual outcomes and require all trials to complete before calculating overall improvement.

**What is stored in SQLite?**
Executed experiment reports and actions such as starts and closures. The current live simulation remains in memory.

## Pre-presentation checklist

Run setup and launch before entering the classroom; verify the server URL in your own browser. Test at the intended projector resolution. Keep one dashboard tab running. Use the supplied built frontend if Node.js is unavailable. Allow installation before going offline. Have Normal and Self-Induced scenarios ready, and keep the API docs available for explaining validation.
