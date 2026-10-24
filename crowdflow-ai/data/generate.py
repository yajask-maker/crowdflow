"""Stochastic five-minute count process, independent innovations and daily latent demand."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from algorithms.campus import make_campus
from ml.features import feature_row,schedule

ROOT=Path(__file__).resolve().parents[1]
SEED=2026


def generate(days=28):
    rng=np.random.default_rng(SEED);graph=make_campus();rows=[]
    for day in range(days):
        day_scale=rng.lognormal(0,.14)*(1 if day%7<5 else .5)
        exam=day%9 in (4,5);event=day%7==3
        for _,_,edge in graph.edges(data=True):
            count=int(rng.poisson(3));history=[count]*3;latent=1.;previous_arrivals=0
            minutes=list(range(420,1200,5));records=[]
            for minute in minutes:
                flags=schedule(minute,day,exam,event)
                # Exogenous schedule + temporally correlated latent variation.
                latent=.85*latent+.15*rng.lognormal(0,.45)
                zone=edge['zone'];base=.05*edge['capacity']
                boost=1+flags['class_change']*(2.2 if zone==1 else .6)+flags['lunch']*(5 if zone==2 else .7)
                boost+=flags['exam']*(4 if zone==3 and 500<minute<620 else .2)
                boost+=flags['event']*(2 if 990<minute<1080 else 0)
                arrivals=int(rng.poisson(max(.1,base*boost*day_scale*latent)))
                edge['occupancy']=count
                records.append(dict(feature_row(edge,minute,day,history,previous_arrivals/5,exam,event),
                                    day=day,minute=minute,pathway_id=edge['id'],synthetic=True))
                # People remain stochastically; density slows departures.
                survival=.34+.22*min(count/edge['capacity'],2)/2
                count=min(edge['hard_capacity'],int(rng.binomial(count,survival))+arrivals)
                history.append(count);previous_arrivals=arrivals
            for i in range(len(records)-1):
                # The next record's occupancy is the state five minutes after features.
                records[i]['target_5min']=records[i+1]['occupancy'];rows.append(records[i])
    df=pd.DataFrame(rows).sort_values(['day','minute','pathway_id'])
    ROOT.joinpath('data').mkdir(exist_ok=True)
    df.to_csv(ROOT/'data/pedestrian_counts.csv.gz',index=False,compression={'method':'gzip','mtime':0},float_format='%.6f')
    assumptions={'seed':SEED,'days':days,'rows':len(df),'pathways':graph.number_of_edges(),
      'interval_minutes':5,'horizon_minutes':5,'synthetic':True,
      'process':'Poisson arrivals, binomial departures, correlated latent demand and lognormal day variation',
      'units':'occupancy: persons, arrival_rate: persons/minute, distances: metres, speed: m/s',
      'schedule':'07:00–20:00; class changes 09,10,11,14,15,16; lunch 12:00–13:30; weekend multiplier 0.5',
      'capacity':'comfort threshold 0.35 persons/m²; physical admission ceiling 2.5 persons/m²',
      'observations':'All values synthetic; no campus observations or personal tracking data.'}
    (ROOT/'data/assumptions.json').write_text(json.dumps(assumptions,indent=2))
    print(json.dumps(assumptions,indent=2));return df


if __name__=='__main__':generate()
