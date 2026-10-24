"""Individual agents, finite edge admission, node-only rerouting, reproducible demand."""
from collections import Counter,defaultdict,deque
from dataclasses import dataclass,field
from math import hypot
import time
import numpy as np
import networkx as nx
from algorithms.campus import make_campus,travel_time,graph_payload
from algorithms.routing import route_groups,candidate_paths
from simulation.scenarios import get_scenario


@dataclass
class Pedestrian:
    id:int
    source:str
    destination:str
    departure:float
    node:str
    status:str='pending'
    path:list=field(default_factory=list)
    index:int=0
    edge_id:str|None=None
    progress:float=0.
    journey_seconds:float=0.
    last_reroute:float=-999.
    reroutes:int=0


class Simulation:
    dt=5.
    def __init__(self,predictor=None):
        self.predictor=predictor;self.reset()

    def reset(self):
        self.graph=make_campus();self.agents=[];self.elapsed=0.;self.status='idle';self.strategy='adaptive'
        self.minute=570.;self.day=0;self.seed=2026;self.scenario='normal';self.intensity=1.
        self.history=[];self.samples=defaultdict(lambda:deque(maxlen=3));self.entry_times=defaultdict(deque)
        self.warnings=[];self.max_occupancy=0;self.capacity_edge_seconds=0.;self.execution_ms=0.;self.closure_triggered=False
        self.edge_lookup={e['id']:(a,b,e) for a,b,e in self.graph.edges(data=True)}
        self.next_forecast=0.;self.next_sample=0.
        self.config={}

    def start(self,scenario='normal',population=None,strategy='adaptive',seed=2026,minute=None,intensity=1.,requests=None,day=0):
        self.reset();s=get_scenario(scenario)
        self.scenario=scenario;self.strategy=strategy;self.seed=seed;self.intensity=intensity;self.day=day
        self.minute=s['minute'] if minute is None else minute
        count=s['population'] if population is None else population
        rng=np.random.default_rng(seed);id_counter=0
        if requests is None:
            requests=[]
            for _ in range(count):
                if scenario=='self_induced':source,destination='12','17'
                elif scenario=='lunch':source,destination=str(rng.choice(['8','10','20','0','12'])),'17'
                elif scenario=='exam':source,destination=str(rng.choice(['0','29','8','20','12'])),'26'
                elif scenario=='closure':source,destination='12','17'
                else:
                    source,destination=rng.choice(['0','6','8','10','12','17','20','22','26','29','35'],2,replace=False).tolist()
                departure=0. if s['window']==0 else float(rng.uniform(0,s['window']))
                requests.append({'source':source,'destination':destination,'demand':1,'departure':departure})
        for request in requests:
            for _ in range(request['demand']):
                self.agents.append(Pedestrian(id_counter,request['source'],request['destination'],request.get('departure',0),request['source']))
                id_counter+=1
        self.config={'scenario':scenario,'population':len(self.agents),'strategy':strategy,'seed':seed,'minute':self.minute,'intensity':intensity,'day':day}
        self.status='running' if self.agents else 'completed'
        self.forecast();self.record();return self.state()

    def forecast(self):
        if self.elapsed>=self.next_sample:
            for pid,(_,_,e) in self.edge_lookup.items():self.samples[pid].append(e['occupancy'])
            self.next_sample=self.elapsed+300
        histories={pid:list(v)[:-1]+[self.edge_lookup[pid][2]['occupancy']] for pid,v in self.samples.items()}
        rates={pid:len(q)/5 for pid,q in self.entry_times.items()}
        if self.predictor:
            self.warnings=self.predictor.update_graph(self.graph,(self.minute+self.elapsed/60)%1440,self.day,
                histories,rates,self.scenario=='exam',self.scenario in ('self_induced','closure'))
        else:
            for _,_,e in self.graph.edges(data=True):e['predicted']=float(e['occupancy'])
        self.next_forecast=self.elapsed+30

    def close(self,pid,closed=True):
        if pid not in self.edge_lookup:raise ValueError('Unknown pathway')
        self.edge_lookup[pid][2]['closed']=closed
        return self.state()

    def plan_waiting(self):
        groups=defaultdict(list)
        for p in self.agents:
            if p.status=='waiting' and (not p.path or p.index>=len(p.path)-1 or self.graph[p.node][p.path[p.index+1]]['closed']):
                if p.node==p.destination:
                    p.status='completed';p.journey_seconds=max(0,self.elapsed-p.departure);continue
                groups[(p.node,p.destination)].append(p)
        # Across OD batches, reservations include already planned waiting/walking agents.
        reserved=Counter()
        if self.strategy=='adaptive':
            for p in self.agents:
                if p.status in ('walking','waiting') and p.path:
                    for a,b in zip(p.path[p.index if p.status=='waiting' else p.index+1:],p.path[(p.index if p.status=='waiting' else p.index+1)+1:]):reserved[self.graph[a][b]['id']]+=1
        for (source,target),people in groups.items():
            original={pid:e['predicted'] for pid,(_,_,e) in self.edge_lookup.items()}
            if self.strategy=='adaptive':
                for pid,(_,_,e) in self.edge_lookup.items():e['predicted']=max(e['predicted'],e['occupancy'])+reserved[pid]
            try:
                begin=time.perf_counter();result=route_groups(self.graph,source,target,len(people),self.strategy)
                self.execution_ms+=(time.perf_counter()-begin)*1000
                cursor=0
                for route in result['routes']:
                    for p in people[cursor:cursor+route['pedestrians']]:
                        replacing=bool(p.path);p.path=route['nodes'][:];p.index=0
                        if replacing:p.reroutes+=1;p.last_reroute=self.elapsed
                    cursor+=route['pedestrians']
                    for pid in route['pathways']:reserved[pid]+=route['pedestrians']
            except nx.NetworkXNoPath:
                # Remain at the current node until a connection reopens.
                for p in people:p.path=[];p.index=0
            finally:
                for pid,(_,_,e) in self.edge_lookup.items():e['predicted']=original[pid]

    def maybe_reroute(self,p):
        if self.strategy!='adaptive' or self.elapsed-p.last_reroute<30 or len(p.path)-p.index<3:return
        old=p.path[p.index:]
        original={pid:e['predicted'] for pid,(_,_,e) in self.edge_lookup.items()}
        own=Counter(self.graph[a][b]['id'] for a,b in zip(old,old[1:]))
        for pid,(_,_,e) in self.edge_lookup.items():
            e['predicted']=max(e['predicted'],e['occupancy'])+max(0,self.reroute_reservations[pid]-own[pid])
        from algorithms.routing import feedback_time
        old_cost=sum(feedback_time(self.graph[a][b],self.graph[a][b]['predicted']+1) for a,b in zip(old,old[1:]))
        try:
            begin=time.perf_counter()
            result=route_groups(self.graph,p.node,p.destination,1,'adaptive',k=3)
            self.execution_ms+=(time.perf_counter()-begin)*1000
            new=next(r for r in result['routes'] if r['pedestrians'])
            if new['feedback_seconds']<old_cost*.8 and old_cost-new['feedback_seconds']>15 and new['nodes']!=old:
                for pid in own:self.reroute_reservations[pid]-=1
                for pid in new['pathways']:self.reroute_reservations[pid]+=1
                p.path=new['nodes'];p.index=0;p.reroutes+=1;p.last_reroute=self.elapsed
        except nx.NetworkXNoPath:pass
        finally:
            for pid,(_,_,e) in self.edge_lookup.items():e['predicted']=original[pid]

    def tick(self):
        if self.status!='running':return
        s=get_scenario(self.scenario)
        if s.get('closure_at') is not None and self.elapsed>=s['closure_at'] and not self.closure_triggered:
            self.close(s['close_pathway']);self.closure_triggered=True
        for p in self.agents:
            if p.status=='pending' and p.departure<=self.elapsed:p.status='waiting'
        for q in self.entry_times.values():
            while q and q[0]<self.elapsed-300:q.popleft()
        if self.elapsed>=self.next_forecast:self.forecast()
        self.plan_waiting()
        # Admission before movement; occupancy ceiling includes both directions.
        for p in self.agents:
            if p.status=='waiting' and p.path and p.index<len(p.path)-1:
                a,b=p.node,p.path[p.index+1];e=self.graph[a][b]
                if not e['closed'] and e['occupancy']<e['hard_capacity']:
                    p.status='walking';p.edge_id=e['id'];p.progress=0.;e['occupancy']+=1
                    self.entry_times[e['id']].append(self.elapsed)
        self.max_occupancy=max(self.max_occupancy,max((e['occupancy'] for _,_,e in self.graph.edges(data=True)),default=0))
        self.capacity_edge_seconds+=self.dt*sum(e['occupancy']>e['capacity'] for _,_,e in self.graph.edges(data=True))
        speeds={pid:e['distance']/travel_time(e,e['occupancy']*self.intensity) for pid,(_,_,e) in self.edge_lookup.items()}
        self.reroute_reservations=Counter()
        if self.strategy=='adaptive':
            for p in self.agents:
                if p.status in ('walking','waiting') and p.path:
                    for a,b in zip(p.path[p.index if p.status=='waiting' else p.index+1:],p.path[(p.index if p.status=='waiting' else p.index+1)+1:]):self.reroute_reservations[self.graph[a][b]['id']]+=1
        for p in self.agents:
            if p.status=='walking':
                e=self.edge_lookup[p.edge_id][2]
                p.progress=min(e['distance'],p.progress+speeds[p.edge_id]*self.dt)
                if p.progress>=e['distance']:
                    e['occupancy']-=1;p.node=p.path[p.index+1];p.index+=1;p.edge_id=None;p.progress=0.
                    if p.node==p.destination:
                        p.status='completed';p.journey_seconds=self.elapsed+self.dt-p.departure
                    else:
                        p.status='waiting';self.maybe_reroute(p)
        self.elapsed+=self.dt
        for _,_,e in self.graph.edges(data=True):
            self.max_occupancy=max(self.max_occupancy,e['occupancy'])
        if all(p.status=='completed' for p in self.agents):self.status='completed'
        if int(self.elapsed)%15==0 or self.status=='completed':self.record()

    def step(self,steps=1):
        for _ in range(steps):
            self.tick()
            if self.status!='running':break
        return self.state()

    def record(self):
        occupancies=[e['occupancy'] for _,_,e in self.graph.edges(data=True)]
        counts=Counter(p.status for p in self.agents)
        self.history.append({'seconds':self.elapsed,'active':counts['walking']+counts['waiting'],
                             'completed':counts['completed'],'max_occupancy':max(occupancies,default=0),
                             'congested':sum(e['occupancy']>e['capacity'] for _,_,e in self.graph.edges(data=True))})
        self.history=self.history[-500:]

    def metrics(self):
        finished=[p.journey_seconds for p in self.agents if p.status=='completed']
        counts=Counter(p.status for p in self.agents)
        return {'population':len(self.agents),'pending':counts['pending'],'walking':counts['walking'],'waiting':counts['waiting'],
                'completed':counts['completed'],'average_travel_seconds':float(np.mean(finished)) if finished else None,
                'p95_travel_seconds':float(np.percentile(finished,95)) if finished else None,
                'maximum_pathway_occupancy':self.max_occupancy,'time_above_capacity_edge_seconds':self.capacity_edge_seconds,
                'rerouting_count':sum(p.reroutes for p in self.agents),
                'reroutes_per_pedestrian':sum(p.reroutes for p in self.agents)/len(self.agents) if self.agents else 0,
                'algorithm_execution_ms':self.execution_ms,'completion_rate':counts['completed']/len(self.agents) if self.agents else 1.,
                'congested_pathways':sum(e['occupancy']>e['capacity'] for _,_,e in self.graph.edges(data=True)),
                'maximum_congestion':max((e['occupancy']/e['capacity'] for _,_,e in self.graph.edges(data=True)),default=0),
                'average_predicted_occupancy':float(np.mean([e['predicted'] for _,_,e in self.graph.edges(data=True)]))}

    def state(self):
        positions=[]
        for p in self.agents:
            if p.status not in ('walking','waiting'):continue
            a=self.graph.nodes[p.node];x,y=a['x'],a['y']
            if p.status=='walking':
                b=self.graph.nodes[p.path[p.index+1]];fraction=p.progress/self.edge_lookup[p.edge_id][2]['distance']
                x+=(b['x']-x)*fraction;y+=(b['y']-y)*fraction
            positions.append({'id':p.id,'x':x,'y':y,'status':p.status,'edge_id':p.edge_id})
        return {'status':self.status,'elapsed_seconds':self.elapsed,'clock_minute':(self.minute+self.elapsed/60)%1440,
                'scenario':self.scenario,'strategy':self.strategy,'seed':self.seed,'metrics':self.metrics(),
                'graph':graph_payload(self.graph),'pedestrians':positions,'history':self.history,'prediction_warnings':self.warnings,
                'config':self.config}
