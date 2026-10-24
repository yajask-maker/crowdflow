"""Explicit Dijkstra/A* plus K-shortest alternatives and feedback allocation."""
import heapq
import itertools
import time
from math import hypot
import networkx as nx
from algorithms.campus import travel_time,edge_ids

STRATEGIES=('distance','congestion','adaptive','astar')


def weight(edge,mode):
    return edge['distance'] if mode=='distance' else travel_time(edge,edge['predicted'])


def shortest_path(graph,source,target,mode='distance',astar=False):
    if source not in graph or target not in graph:raise ValueError('Unknown campus location')
    if source==target:return [source],0.
    def heuristic(node):
        if not astar:return 0.
        a,b=graph.nodes[node],graph.nodes[target]
        d=hypot(a['x']-b['x'],a['y']-b['y'])
        return d if mode=='distance' else d/max(e['speed'] for _,_,e in graph.edges(data=True))
    distances={source:0.};previous={};queue=[(heuristic(source),0.,source)]
    while queue:
        _,cost,u=heapq.heappop(queue)
        if cost>distances[u]:continue
        if u==target:
            path=[u]
            while u in previous:u=previous[u];path.append(u)
            return list(reversed(path)),cost
        for v,e in graph[u].items():
            if e['closed']:continue
            new=cost+weight(e,mode)
            if new<distances.get(v,float('inf')):
                distances[v]=new;previous[v]=u
                heapq.heappush(queue,(new+heuristic(v),new,v))
    raise nx.NetworkXNoPath('No open path connects these locations')


def candidate_paths(graph,source,target,k=6):
    if source==target:return [[source]]
    open_graph=nx.subgraph_view(graph,filter_edge=lambda a,b:not graph[a][b]['closed'])
    try:
        paths=list(itertools.islice(nx.shortest_simple_paths(open_graph,source,target,
                    weight=lambda a,b,d:travel_time(d,d['predicted'])),max(1,k//2)))
        # A plain K-shortest list can contain nearly identical paths. Penalize
        # overlap to search for geographically distinct, still feasible options.
        used={e['id']:0 for _,_,e in graph.edges(data=True)}
        for path in paths:
            for pid in edge_ids(graph,path):used[pid]+=1
        for _ in range(k*2):
            path=nx.shortest_path(open_graph,source,target,weight=lambda a,b,d:
                    travel_time(d,d['predicted'])*(1+used[d['id']]*1.5))
            for pid in edge_ids(graph,path):used[pid]+=1
            if path not in paths:paths.append(path)
            if len(paths)>=k:break
        return paths
    except nx.NetworkXNoPath:raise nx.NetworkXNoPath('No open path connects these locations')


def feedback_time(edge,occupancy):
    # Snapshot walking time plus a conservative fluid queue admission estimate.
    # Beyond the physical ceiling, extra assigned people must wait upstream.
    queue=max(0.,occupancy-edge['hard_capacity'])/edge['hard_capacity']
    return travel_time(edge,occupancy)+queue*travel_time(edge,edge['hard_capacity'])


def route_groups(graph,source,target,demand=1,strategy='adaptive',k=6):
    if strategy not in STRATEGIES:raise ValueError('Unknown routing strategy')
    if demand<0:raise ValueError('Demand must be nonnegative')
    t=time.perf_counter()
    if strategy=='adaptive':paths=candidate_paths(graph,source,target,k)
    else:
        primary,_=shortest_path(graph,source,target,'distance' if strategy=='distance' else 'time',strategy=='astar')
        paths=[primary]
    counts=[0]*len(paths)
    reservations={e['id']:0 for _,_,e in graph.edges(data=True)}
    # Greedy marginal assignment in small groups; overlap is reserved globally.
    # This is a conservative snapshot approximation, not a time-expanded optimum.
    remaining=demand
    while remaining:
        group=min(5,remaining)
        costs=[]
        for path in paths:
            costs.append(sum(feedback_time(graph[a][b],max(graph[a][b]['occupancy'],graph[a][b]['predicted'])+
                                          reservations[graph[a][b]['id']]+group)
                             for a,b in zip(path,path[1:])))
        choice=min(range(len(paths)),key=lambda i:costs[i]) if strategy=='adaptive' else 0
        counts[choice]+=group
        for pid in edge_ids(graph,paths[choice]):reservations[pid]+=group
        remaining-=group
    routes=[]
    for i,path in enumerate(paths):
        edges=[graph[a][b] for a,b in zip(path,path[1:])]
        baseline=sum(travel_time(e,e['predicted']) for e in edges)
        assigned=sum(feedback_time(e,max(e['occupancy'],e['predicted'])+reservations[e['id']]) for e in edges)
        routes.append({'nodes':path,'pathways':edge_ids(graph,path),'pedestrians':counts[i],
                       'distance_metres':sum(e['distance'] for e in edges),'predicted_seconds':baseline,
                       'feedback_seconds':assigned,'max_predicted_congestion':max(
                           (max(e['occupancy'],e['predicted'])/e['capacity'] for e in edges),default=0.),
                       'max_feedback_congestion':max(((max(e['occupancy'],e['predicted'])+reservations[e['id']])/e['capacity'] for e in edges),default=0.)})
    average=sum(r['feedback_seconds']*r['pedestrians'] for r in routes)/demand if demand else 0.
    return {'strategy':strategy,'demand':demand,'routes':routes,'estimated_seconds':average,
            'execution_ms':(time.perf_counter()-t)*1000,'estimate_note':'Snapshot estimate including assignment; use controlled simulation for measured travel times.'}
