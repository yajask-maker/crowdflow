import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from backend.app import app
from backend import storage
from ml.predictor import Predictor
from ml.features import feature_row
from algorithms.campus import make_campus

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def client(tmp_path_factory):
    storage.DB=tmp_path_factory.mktemp('db')/'test.sqlite3'
    with TestClient(app) as c:yield c


@pytest.fixture(autouse=True)
def reset(client):client.post('/simulate/reset')


def test_ml_real_metrics_and_baseline():
    df=pd.read_csv(ROOT/'data/test_predictions.csv.gz');metrics=json.loads((ROOT/'ml/metrics.json').read_text())
    assert metrics['test']['mae']==pytest.approx(mean_absolute_error(df.target_5min,df.predicted))
    assert metrics['test']['rmse']==pytest.approx(np.sqrt(mean_squared_error(df.target_5min,df.predicted)))
    assert metrics['test']['r2']==pytest.approx(r2_score(df.target_5min,df.predicted))
    assert metrics['baseline']['mae']==pytest.approx(mean_absolute_error(df.target_5min,df.occupancy))
    assert df.day.min()==23 and df.day.max()==27
    assert metrics['split']['train_days'][1]<metrics['split']['validation_days'][0]
    assert metrics['split']['validation_days'][1]<metrics['split']['test_days'][0]


def test_prediction_output_and_ood(client):
    result=client.post('/predict',json={'pathways':[{'pathway_id':'P001','occupancy':15,'lag_5':12,'lag_10':8,'arrival_rate':2}]}).json()
    assert result['horizon_minutes']==5;assert result['predictions'][0]['occupancy']>=0
    result=client.post('/predict',json={'pathways':[{'pathway_id':'P001','occupancy':400}]}).json()
    assert result['warnings']
    assert client.post('/predict',json={'pathways':[{'pathway_id':'bad'}]}).status_code==404
    assert client.post('/predict',json={'pathways':[{'pathway_id':'P001','occupancy':-1}]}).status_code==422
    assert client.post('/predict',json={'pathways':[{'pathway_id':'P001','occupancy':10000}]}).status_code==422


def test_graph_and_route_api(client):
    assert client.get('/health').json()['model_loaded']
    graph=client.get('/graph').json();assert len(graph['nodes'])==36;assert len(graph['edges'])==66
    assert len(client.get('/locations').json())==36
    assert len(client.get('/scenarios').json())==5
    request={'source':'12','destination':'17','demand':500,'strategy':'adaptive'}
    r=client.post('/route',json=request);assert r.status_code==200
    assert sum(p['pedestrians'] for p in r.json()['routes'])==500
    smaller=client.post('/route',json=dict(request,demand=5)).json()
    assert smaller['estimated_seconds']!=r.json()['estimated_seconds']
    assert client.post('/route',json=dict(request,source='bad')).status_code==404
    assert client.post('/route',json=dict(request,demand=-1)).status_code==422
    assert client.post('/route',json=dict(request,strategy='invalid')).status_code==422
    g=client.get('/graph').json()
    for e in g['edges']:
        if '17' in (e['source'],e['target']):client.post('/simulate/closure',json={'pathway_id':e['id']})
    assert client.post('/route',json=request).status_code==409


def test_simulation_api_and_closure(client):
    s=client.post('/simulate/start',json={'scenario':'self_induced','population':60}).json()
    assert s['status']=='running' and s['metrics']['population']==60
    s=client.post('/simulate/step',json={'steps':4}).json();assert s['metrics']['walking']>0
    assert len(s['pedestrians'])==s['metrics']['walking']+s['metrics']['waiting']
    assert sum(e['occupancy'] for e in s['graph']['edges'])==s['metrics']['walking']
    t=s['elapsed_seconds'];client.post('/simulate/pause')
    assert client.post('/simulate/step',json={'steps':3}).json()['elapsed_seconds']==t
    assert client.post('/simulate/resume').json()['status']=='running'
    s=client.post('/simulate/closure',json={'pathway_id':'P025','closed':True}).json()
    assert next(e for e in s['graph']['edges'] if e['id']=='P025')['closed']
    assert client.post('/simulate/closure',json={'pathway_id':'bad'}).status_code==404
    assert client.get('/simulation/state').status_code==200
    assert client.get('/analytics').status_code==200
    assert client.post('/simulate/reset').json()['status']=='idle'
    assert client.post('/simulate/start',json={'scenario':'normal','population':0}).json()['status']=='completed'


@pytest.mark.parametrize('scenario',['normal','lunch','exam','closure','self_induced'])
def test_scenario_smoke(client,scenario):
    client.post('/simulate/start',json={'scenario':scenario,'population':20})
    for _ in range(30):
        state=client.post('/simulate/step',json={'steps':60}).json()
        if state['status']=='completed':break
    assert state['status']=='completed'
    assert state['metrics']['completed']==20
    if scenario=='closure':assert next(e for e in state['graph']['edges'] if e['id']=='P025')['closed']


def test_multiple_requests_and_validation(client):
    requests=[{'source':'12','destination':'17','demand':20,'departure':0},{'source':'0','destination':'26','demand':10,'departure':120}]
    state=client.post('/simulate/start',json={'requests':requests}).json()
    assert state['metrics']['population']==30
    state=client.post('/simulate/step',json={'steps':3}).json()
    assert state['metrics']['pending']==10
    assert client.post('/simulate/start',json={'requests':[dict(requests[0],source='bad')]}).status_code==404
    assert client.post('/simulate/start',json={'requests':[dict(requests[0],demand=1500),dict(requests[1],demand=1500)]}).status_code==422
    assert client.post('/simulate/step',json={'steps':1000}).status_code==422


def test_comparison_api_and_storage(client):
    result=client.post('/compare',json={'scenario':'self_induced','population':50,'seed':21})
    assert result.status_code==200;r=result.json()
    assert len(r['rows'])==3;assert all(row['completed']==50 for row in r['rows'])
    assert r['experiment_id']>0
    assert client.get('/analytics').json()['comparison']['seed']==21
    assert len(client.get('/analytics').json()['experiments'])>0
    assert client.get('/model/metrics').json()['test']['mae']>0
    assert client.get('/docs').status_code==200
    assert client.get('/openapi.json').json()['info']['title']=='CrowdFlow AI'


def test_built_dashboard_assets(client):
    r=client.get('/');assert r.status_code==200 and 'CrowdFlow' in r.text
    import re
    paths=re.findall(r'(?:src|href)="(/assets/[^\"]+)"',r.text)
    assert paths
    for path in paths:assert client.get(path).status_code==200
