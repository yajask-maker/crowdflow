"""Chronological holdout; validation-only tuning, untouched test days."""
import json
import platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from ml.features import FEATURES,frame

ROOT=Path(__file__).resolve().parents[1]


def scores(y,p):return {'mae':float(mean_absolute_error(y,p)),'rmse':float(np.sqrt(mean_squared_error(y,p))),'r2':float(r2_score(y,p))}


def train():
    path=ROOT/'data/pedestrian_counts.csv.gz'
    if not path.exists():
        from data.generate import generate
        generate()
    df=pd.read_csv(path)
    train=df[df.day<18];valid=df[(df.day>=18)&(df.day<23)];test=df[df.day>=23]
    X,y=frame(train.to_dict('records')),train.target_5min
    trials=[];best=None
    for depth,leaf in [(12,4),(18,4),(None,8)]:
        model=RandomForestRegressor(n_estimators=80,max_depth=depth,min_samples_leaf=leaf,
                                     max_features=.85,n_jobs=-1,random_state=2026)
        model.fit(X,y);p=model.predict(frame(valid.to_dict('records')))
        metric=scores(valid.target_5min,p)
        trials.append({'max_depth':depth,'min_samples_leaf':leaf,'validation':metric})
        if best is None or metric['mae']<best[0]:best=(metric['mae'],model,trials[-1])
    # Refit selected hyperparameters on train+validation. The test remains untouched.
    params=best[1].get_params();final=RandomForestRegressor(**params)
    combined=df[df.day<23]
    final.fit(frame(combined.to_dict('records')),combined.target_5min)
    predictions=final.predict(frame(test.to_dict('records')))
    residuals=predictions-test.target_5min.to_numpy()
    persistence=test.occupancy.to_numpy()
    report={'data_source':'Synthetic stochastic campus counts; not real observations.',
            'horizon_minutes':5,'seed':2026,'model':'RandomForestRegressor',
            'split':{'train_days':[0,17],'validation_days':[18,22],'test_days':[23,27],
                     'train_rows':len(train),'validation_rows':len(valid),'test_rows':len(test),
                     'purge':'Last row of each pathway-day removed. No label crosses day boundaries.'},
            'selected_parameters':{k:params[k] for k in ('n_estimators','max_depth','min_samples_leaf','max_features')},
            'tuning_trials':trials,'test':scores(test.target_5min,predictions),
            'baseline':dict(scores(test.target_5min,persistence),name='Persistence (current occupancy)'),
            'feature_importance':[{'feature':f,'importance':float(v)} for f,v in sorted(zip(FEATURES,final.feature_importances_),key=lambda pair:-pair[1])],
            'errors':{'mean_error':float(residuals.mean()),'p95_absolute':float(np.percentile(abs(residuals),95))},
            'versions':{'python':platform.python_version(),'sklearn':sklearn.__version__},
            'feature_ranges':{f:{'min':float(combined[f].min()),'max':float(combined[f].max())} for f in FEATURES}}
    edges=np.linspace(float(residuals.min())-.01,float(residuals.max())+.01,21)
    counts,_=np.histogram(residuals,bins=edges)
    report['error_histogram']=[{'error':float((edges[i]+edges[i+1])/2),'count':int(n)} for i,n in enumerate(counts)]
    sample=test.copy();sample['predicted']=predictions
    pathway='P024';series=sample[(sample.pathway_id==pathway)&(sample.day==23)]
    report['actual_vs_predicted']=[{'minute':int(r.minute),'actual':float(r.target_5min),'predicted':float(r.predicted)} for r in series.itertuples()]
    report['plot_pathway']=pathway
    joblib.dump({'model':final,'features':FEATURES,'sklearn_version':sklearn.__version__},ROOT/'ml/model.joblib',compress=3)
    (ROOT/'ml/metrics.json').write_text(json.dumps(report,indent=2))
    sample[['day','minute','pathway_id','occupancy','target_5min','predicted']].to_csv(ROOT/'data/test_predictions.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    print(json.dumps({k:report[k] for k in ('test','baseline','selected_parameters','split')},indent=2))
    return report


if __name__=='__main__':train()
