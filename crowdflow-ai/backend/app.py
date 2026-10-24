from contextlib import asynccontextmanager
import json
from pathlib import Path
from threading import RLock
import networkx as nx
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from algorithms.campus import graph_payload
from algorithms.routing import route_groups
from simulation.engine import Simulation
from simulation.scenarios import SCENARIOS
from simulation.compare import compare
from ml.predictor import Predictor
from ml.features import feature_row
from backend.schemas import RouteRequest,StartRequest,StepRequest,ClosureRequest,PredictRequest,CompareRequest
from backend import storage

ROOT=Path(__file__).resolve().parents[1]
lock=RLock();predictor=None;sim=None;last_comparison=None


@asynccontextmanager
async def lifespan(app):
    global predictor,sim
    predictor=Predictor();predictor.model.n_jobs=1
    sim=Simulation(predictor);storage.init_db()
    yield


app=FastAPI(title='CrowdFlow AI',version='1.0.0',description='Synthetic campus forecasting and feedback-aware pedestrian routing.',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],allow_methods=['GET','POST'],allow_headers=['Content-Type'])


def valid_nodes(source,target):
    if source not in sim.graph or target not in sim.graph:raise HTTPException(404,'Unknown campus location')


@app.get('/health')
def health():return {'status':'ok','model_loaded':predictor is not None,'data_source':'synthetic'}


@app.get('/graph')
def graph():
    with lock:return graph_payload(sim.graph)


@app.get('/locations')
def locations():return [dict(d) for _,d in sim.graph.nodes(data=True)]


@app.get('/scenarios')
def scenarios():return SCENARIOS


@app.post('/predict')
def predict(request:PredictRequest):
    rows=[]
    for row in request.pathways:
        if row.pathway_id not in sim.edge_lookup:raise HTTPException(404,'Unknown pathway')
        e=sim.edge_lookup[row.pathway_id][2].copy();e['occupancy']=row.occupancy
        if row.occupancy>e['hard_capacity']:raise HTTPException(422,'Occupancy exceeds physical admission ceiling')
        history=[row.lag_10 if row.lag_10 is not None else row.occupancy,
                 row.lag_5 if row.lag_5 is not None else row.occupancy,row.occupancy]
        rows.append(feature_row(e,row.minute,row.day,history,row.arrival_rate,row.exam,row.event))
    predictions,warnings=predictor.predict(rows)
    return {'horizon_minutes':5,'predictions':[{'pathway_id':r.pathway_id,'occupancy':p} for r,p in zip(request.pathways,predictions)],'warnings':warnings}


@app.post('/route')
def route(request:RouteRequest):
    with lock:
        valid_nodes(request.source,request.destination)
        g=sim.graph.copy()
        histories={pid:list(v) for pid,v in sim.samples.items()}
        predictor.update_graph(g,request.departure_minute,request.day,histories,
                               {pid:len(q)/5 for pid,q in sim.entry_times.items()},sim.scenario=='exam',sim.scenario=='self_induced')
        try:return route_groups(g,request.source,request.destination,request.demand,request.strategy)
        except nx.NetworkXNoPath as exc:raise HTTPException(409,str(exc))


@app.post('/simulate/start')
def start(request:StartRequest):
    with lock:
        if request.requests:
            if sum(r.demand for r in request.requests)>1500:raise HTTPException(422,'Total demand must not exceed 1500')
            for r in request.requests:valid_nodes(r.source,r.destination)
        result=sim.start(**request.model_dump())
        storage.log('start',request.model_dump());return result


@app.post('/simulate/step')
def step(request:StepRequest):
    with lock:return sim.step(request.steps)


@app.post('/simulate/pause')
def pause():
    with lock:
        if sim.status=='running':sim.status='paused'
        return sim.state()


@app.post('/simulate/resume')
def resume():
    with lock:
        if sim.status=='paused':sim.status='running'
        return sim.state()


@app.post('/simulate/reset')
def reset():
    with lock:sim.reset();return sim.state()


@app.post('/simulate/closure')
def closure(request:ClosureRequest):
    with lock:
        try:result=sim.close(request.pathway_id,request.closed)
        except ValueError as exc:raise HTTPException(404,str(exc))
        storage.log('closure',request.model_dump());return result


@app.get('/simulation/state')
def state():
    with lock:return sim.state()


@app.get('/model/metrics')
def metrics():return predictor.metrics


@app.get('/analytics')
def analytics():
    with lock:
        return {'simulation':sim.metrics(),'history':sim.history,'comparison':last_comparison,
                'experiments':storage.experiments(),'data_source':'All experiments and ML counts are synthetic.'}


@app.post('/compare')
def comparison(request:CompareRequest):
    global last_comparison
    result=compare(predictor,**request.model_dump());result['experiment_id']=storage.save_experiment(result)
    with lock:last_comparison=result
    return result


@app.get('/benchmarks')
def benchmarks():
    path=ROOT/'data/comparison_results.json'
    return json.loads(path.read_text()) if path.exists() else []


# Serve the built dashboard from the same origin. API routes are registered first.
DIST=ROOT/'frontend/dist'
if DIST.exists():
    app.mount('/assets',StaticFiles(directory=DIST/'assets'),name='assets')
    @app.get('/',include_in_schema=False)
    def index():return FileResponse(DIST/'index.html')
