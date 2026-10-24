import networkx as nx
import pytest
from algorithms.campus import make_campus,travel_time
from algorithms.routing import shortest_path,route_groups


def test_connectivity():
    g=make_campus();assert len(g)==36;assert nx.is_connected(g)


@pytest.mark.parametrize('source,target',[('12','17'),('0','35'),('8','26'),('3','3')])
@pytest.mark.parametrize('mode',['distance','time'])
def test_solvers(source,target,mode):
    g=make_campus()
    for _,_,e in g.edges(data=True):e['predicted']=int(e['capacity']*.8)
    fn=lambda a,b,e:e['distance'] if mode=='distance' else travel_time(e,e['predicted'])
    oracle=nx.shortest_path_length(g,source,target,weight=fn)
    for astar in (False,True):
        path,cost=shortest_path(g,source,target,mode,astar)
        assert path[0]==source and path[-1]==target
        assert cost==pytest.approx(oracle)


def test_closure_and_disconnect():
    g=make_campus();path,_=shortest_path(g,'12','17')
    g[path[0]][path[1]]['closed']=True
    result=route_groups(g,'12','17',100)
    assert all(not g[a][b]['closed'] for r in result['routes'] for a,b in zip(r['nodes'],r['nodes'][1:]))
    for _,e in g['17'].items():e['closed']=True
    with pytest.raises(nx.NetworkXNoPath):route_groups(g,'12','17',5)


def test_allocation_and_zero():
    g=make_campus();r=route_groups(g,'12','17',500)
    assert sum(p['pedestrians'] for p in r['routes'])==500
    assert sum(p['pedestrians']>0 for p in r['routes'])>1
    assert route_groups(g,'12','17',0)['estimated_seconds']==0
    assert route_groups(g,'12','12',15)['estimated_seconds']==0
    assert all(e['occupancy']==0 and e['predicted']==0 for _,_,e in g.edges(data=True))


def test_congestion_changes_route():
    g=make_campus();first=route_groups(g,'12','17',1,'congestion')['routes'][0]['nodes']
    g[first[0]][first[1]]['predicted']=g[first[0]][first[1]]['capacity']*5
    second=route_groups(g,'12','17',1,'congestion')['routes'][0]['nodes']
    assert first!=second
