import json
from pathlib import Path
import joblib
import numpy as np
from ml.features import frame,feature_row

ROOT=Path(__file__).resolve().parents[1]


class Predictor:
    def __init__(self):
        bundle=joblib.load(ROOT/'ml/model.joblib')
        self.model=bundle['model'];self.model.n_jobs=1
        self.metrics=json.loads((ROOT/'ml/metrics.json').read_text())

    def predict(self,rows):
        result=np.maximum(0,self.model.predict(frame(rows)))
        warnings=[]
        ranges=self.metrics['feature_ranges']
        for i,row in enumerate(rows):
            outside=[f for f,r in ranges.items() if row[f]<r['min'] or row[f]>r['max']]
            if outside:warnings.append({'row':i,'outside_training_range':outside})
        return result.tolist(),warnings

    def update_graph(self,graph,minute,day=0,histories=None,arrival_rates=None,exam=False,event=False):
        edges=list(graph.edges(data=True));rows=[]
        for _,_,e in edges:
            rows.append(feature_row(e,minute,day,(histories or {}).get(e['id']),
                                    (arrival_rates or {}).get(e['id'],0),exam,event))
        predictions,warnings=self.predict(rows)
        for (_,_,edge),prediction in zip(edges,predictions):edge['predicted']=min(edge['hard_capacity'],prediction)
        return warnings
