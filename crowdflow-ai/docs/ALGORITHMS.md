# Algorithms and mathematical assumptions

## Why a shortest physical route can be slow

Distance-only routing sends every traveller along the fewest metres. If many students make the same request together, the recommendations themselves create congestion. Forecast-aware routing improves the edge estimates but still ignores the additional people it is about to recommend. CrowdFlow adds these commitments before selecting the next group's route.

This is a demonstration of feedback-aware assignment, not a claim to be the first research system with this idea.

## Edge costs and units

For edge distance d metres, width w metres, normal speed v0 = 1.4 m/s and actual occupancy o people:

- Comfort capacity C = floor(0.35 d w), minimum 15 people.
- Physical admission ceiling H = floor(2.5 d w).
- Congestion ratio r = max(0,o)/C.
- Speed v(o) = max(0.12, v0/(1 + 1.8 r²)) m/s.
- Traversal cost T(o) = d/v(o) seconds.

The intensity control multiplies occupancy only in the speed calculation. It does not multiply or create agents. The speed curve and capacity densities are stated simulation assumptions, not calibrated campus physics.

All costs are nonnegative. Closed edges are excluded from new paths. Current walkers may finish an edge that closes behind them.

For assignment estimates, CrowdFlow additionally models upstream admission delay:

**F(o) = T(o) + max(0,o − H)/H × T(H)**

This is a conservative fluid queue approximation. Without an admission term, the minimum-speed floor can make adding people to an already saturated route appear free. Actual simulation travel times are measured from agent trajectories and queues, not copied from this formula.

## Algorithm 1: distance-only Dijkstra

A heap tracks the smallest known total distance from the source. Relax each open neighbouring edge, update its predecessor when a shorter distance is found, and stop when the destination is reached. Reconstruct the path from predecessors.

The explicit implementation is in `shortest_path`; NetworkX is used as an independent correctness oracle in tests. Heap-based complexity is O((V+E) log V). A whole OD request is assigned to one shortest route; no self-induced congestion is reserved for choosing alternatives.

## Algorithm 2: congestion-aware Dijkstra

Use T(predicted occupancy) as each edge's cost, keeping the same search procedure. This makes the shortest cost path a forecast travel-time path. It considers the forecast before allocation but does not add the newly recommended group to the search weights.

The route finder still reports a feedback-adjusted estimate for comparison; this estimate does not change the conventional algorithm's assignment. Normal replanning can occur if a closure invalidates the route, but it does not continuously redistribute conventional groups.

## Optional A*

Use the same nonnegative predicted-time cost with heuristic:

**h(node) = straight-line distance to destination / maximum normal edge speed.**

Every edge has distance at least its straight-line separation; actual walking speed never exceeds normal speed. Therefore this is a lower bound on the remaining travel time. For distance costs, straight-line distance itself is admissible. Tests compare both modes against NetworkX shortest-path lengths.

A* is offered in the route finder and live simulation. The required controlled comparison evaluates the three specified strategies.

## Algorithm 3: CrowdFlow adaptive

1. Obtain up to half the candidate set from NetworkX K-shortest simple paths using forecast travel time.
2. Search for additional paths with a penalty on repeatedly used edges. This avoids filling the candidate list with almost identical routes sharing every bottleneck.
3. Maintain a pathway reservation counter shared across candidates and OD batches.
4. In groups of at most five people, evaluate each candidate using F(max(current occupancy, prediction) + existing commitments + this group).
5. Assign the group to the lowest-cost candidate and add its occupancy to every pathway on that route.
6. Continue until all demand is allocated. Preview calls return the allocations without mutating physical occupancy.
7. During simulation, reserve the untraversed commitments of waiting and walking pedestrians. Reconsider routes at nodes using these commitments.

Reservations conservatively count all assigned agents as simultaneous future occupancy, rather than computing time-specific entry/exit schedules. They are reconstructed from remaining routes; travelled edges are released. This can overestimate congestion and cause detours. The method is a bounded heuristic, not a proof of global optimality or system-optimal assignment.

Allocation cost for D pedestrians and K candidates of average L edges is approximately O((D/5) K L), after candidate discovery. This campus fixes K≤6 for initial allocations and uses K≤3 for node rerouting. K-shortest discovery can be expensive on much larger graphs; it is intentionally bounded here.

## Rerouting hysteresis

Only reroute at a node. Require at least 30 seconds since the last reroute, an estimated saving exceeding 20%, and more than 15 seconds saved. Closure-invalidated paths are replanned without this discretionary threshold. Continuing through a closed edge is permitted only if the agent was already walking on it.

This prevents switching every tick, but does not guarantee that route changes never interact. Feedback reservations reduce repeated recommendations onto an apparently empty shared alternative.

## Edge cases

| Situation | Behaviour |
|---|---|
| Source equals destination | Zero distance/time; agents complete at their node |
| Zero demand | Valid route preview with zero assignments and zero weighted mean |
| Unknown location/pathway | API 404 |
| Negative demand, invalid strategy, excessive demand | Pydantic/API 422 |
| Disconnected destination | Route API 409; simulator keeps agents waiting until access reopens |
| Extreme occupancy | Current speed floor, admission ceiling, node queue and forecast range warning |
| Temporary closure | Exclude new entries; retain and finish already-admitted walkers |

## Controlled experiment metrics

All strategies receive the same seeded departure and OD requests, clock, population, intensity, geometry and closure schedule. Dynamics are deterministic once these requests are generated. The self-induced scenario departs everyone at once from the same OD pair, so its seed intentionally has no effect.

- Mean and P95 journey time: elapsed time from requested departure to destination, including waiting; only completed trips.
- Peak pathway occupancy: maximum physical edge count observed after admission.
- Time above capacity: sum of five-second intervals above comfort capacity across all edges (edge·seconds); not a single global duration.
- Reroutes per person: successful route replacements divided by population; closure replans included.
- Algorithm execution time: cumulative timed allocation/search calls, excluding ML inference and physical movement; hardware dependent.
- Improvement: 100 × (distance-only mean − adaptive mean) / distance-only mean, only when all three trials finish.

Runs stop after 7,200 simulated seconds. Incomplete results are explicitly marked and no population-wide improvement is reported. Charts and tables are generated from these measured values without forcing CrowdFlow to win.
