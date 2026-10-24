"""Fictional Meridian University. Coordinates and distances are in metres."""
from math import hypot
import networkx as nx

BUILDINGS = {
 0:("North Hostel","residential"),2:("Research Centre","academic"),5:("Sports Complex","sports"),
 6:("Library","library"),8:("AI & DS Block","academic"),10:("Science Laboratories","academic"),
 12:("Main Entrance","entrance"),14:("Central Atrium","junction"),17:("Cafeteria","cafeteria"),
 18:("Administration","admin"),20:("Engineering Block","academic"),22:("Auditorium","event"),
 24:("Innovation Hub","academic"),26:("Examination Hall","exam"),29:("South Hostel","residential"),
 30:("South Gate","entrance"),32:("Student Centre","event"),35:("Indoor Arena","sports")}


def make_campus():
    graph = nx.Graph()
    for r in range(6):
        for c in range(6):
            i = r*6+c
            name,kind = BUILDINGS.get(i,(f"Junction {i:02d}","junction"))
            graph.add_node(str(i),id=str(i),name=name,kind=kind,x=c*85+45,y=(5-r)*75+45)
    pairs=[]
    for r in range(6):
        for c in range(6):
            i=r*6+c
            if c<5:pairs.append((i,i+1))
            if r<5:pairs.append((i,i+6))
    pairs += [(1,8),(4,9),(19,26),(21,28),(27,34),(7,14)]
    for index,(a,b) in enumerate(pairs):
        u,v=graph.nodes[str(a)],graph.nodes[str(b)]
        distance=round(hypot(u['x']-v['x'],u['y']-v['y']),2)
        width=1.2 if a//6==b//6==2 else (4.5 if a//6==b//6==3 else 3.0)
        capacity=max(15,int(distance*width*.35))
        graph.add_edge(str(a),str(b),id=f"P{index+1:03d}",source=str(a),target=str(b),
                       distance=distance,width=width,capacity=capacity,speed=1.4,
                       hard_capacity=int(distance*width*2.5),occupancy=0,predicted=0.,closed=False,
                       zone=2 if 17 in (a,b) else (3 if 26 in (a,b) else (1 if any(n in (8,10,20) for n in (a,b)) else 0)))
    return graph


def travel_time(edge, occupancy=None):
    """Seconds; comfort capacity is not a hard physical occupancy limit."""
    ratio=max(0.,edge['occupancy'] if occupancy is None else occupancy)/edge['capacity']
    speed=max(.12,edge['speed']/(1+1.8*ratio*ratio))
    return edge['distance']/speed


def graph_payload(graph):
    return {'nodes':[dict(d) for _,d in graph.nodes(data=True)],
            'edges':[dict(d,congestion=d['occupancy']/d['capacity'],
                          predicted_congestion=d['predicted']/d['capacity'],
                          traversal_seconds=travel_time(d),predicted_seconds=travel_time(d,d['predicted']))
                     for _,_,d in graph.edges(data=True)],
            'metadata':{'name':'Meridian University','fictional':True,'coordinate_units':'metres'}}


def edge_ids(graph,path):
    return [graph[a][b]['id'] for a,b in zip(path,path[1:])]
