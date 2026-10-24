from pathlib import Path
import json
from simulation.engine import Simulation

ROOT=Path(__file__).resolve().parents[1]


def compare(predictor,scenario='self_induced',population=None,seed=2026,intensity=1.,horizon_seconds=7200):
    rows=[];curves=[]
    for strategy in ('distance','congestion','adaptive'):
        sim=Simulation(predictor)
        sim.start(scenario,population,strategy,seed,intensity=intensity)
        while sim.status=='running' and sim.elapsed<horizon_seconds:sim.step(12)
        rows.append(dict(sim.metrics(),strategy=strategy,status=sim.status,elapsed_seconds=sim.elapsed,
                         unfinished=len(sim.agents)-sum(p.status=='completed' for p in sim.agents)))
        curves.append({'strategy':strategy,'history':sim.history})
    baseline,adaptive=rows[0],rows[2]
    improvement=None
    if all(r['status']=='completed' for r in rows) and baseline['average_travel_seconds']:
        improvement=100*(baseline['average_travel_seconds']-adaptive['average_travel_seconds'])/baseline['average_travel_seconds']
    return {'scenario':scenario,'population':rows[0]['population'],'seed':seed,'intensity':intensity,
            'horizon_seconds':horizon_seconds,'rows':rows,'curves':curves,'improvement_percent':improvement,
            'interpretation':'Positive improvement means adaptive is faster than distance-only. Negative means it is slower. Incomplete trials are censored; no overall improvement is reported.',
            'metric_notes':'Travel times include node waits, for completed pedestrians. Capacity time sums seconds across pathways. Execution time covers route allocation calls, not ML inference; timings vary by machine.'}


if __name__=='__main__':
    from ml.predictor import Predictor
    from simulation.scenarios import SCENARIOS
    predictor=Predictor();reports=[]
    for s in SCENARIOS:
        report=compare(predictor,s['id']);reports.append(report)
        print(s['id'],[(r['strategy'],round(r['average_travel_seconds'] or 0,1),r['unfinished']) for r in report['rows']],flush=True)
    (ROOT/'data/comparison_results.json').write_text(json.dumps(reports,indent=2))
