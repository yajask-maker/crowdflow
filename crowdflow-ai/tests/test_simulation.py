from collections import Counter
import numpy as np
from simulation.engine import Simulation
from simulation.compare import compare
from algorithms.campus import travel_time


def assert_conserved(sim):
    counts=Counter(p.status for p in sim.agents)
    assert sum(counts.values())==len(sim.agents)
    edge_counts=Counter(p.edge_id for p in sim.agents if p.status=='walking')
    assert sum(edge_counts.values())==counts['walking']
    for pid,(_,_,e) in sim.edge_lookup.items():
        assert e['occupancy']==edge_counts[pid]
        assert 0<=e['occupancy']<=e['hard_capacity']


def test_movement_conservation_and_pause():
    sim=Simulation();sim.start('self_induced',80)
    sim.tick();assert_conserved(sim)
    start=sim.state()['pedestrians'];assert start
    assert all(p['status']=='walking' for p in start)
    assert all(p['x']!=sim.graph.nodes['12']['x'] or p['y']!=sim.graph.nodes['12']['y'] for p in start)
    assert all(np.hypot(p['x']-sim.graph.nodes['12']['x'],p['y']-sim.graph.nodes['12']['y'])<=7.001 for p in start)
    sim.status='paused';before=sim.elapsed;sim.step(20);assert sim.elapsed==before
    sim.status='running'
    for _ in range(1200):
        sim.tick();assert_conserved(sim)
        if sim.status=='completed':break
    assert sim.status=='completed';assert sim.metrics()['completed']==80
    assert all(p.node==p.destination for p in sim.agents)
    sim.reset();assert sim.status=='idle';assert sim.metrics()['population']==0


def test_density_speed_and_hard_limit():
    sim=Simulation();sim.start('self_induced',800,'distance');sim.tick()
    assert_conserved(sim)
    assert sim.metrics()['waiting']>0
    e=next(e for _,_,e in sim.graph.edges(data=True) if e['occupancy'])
    assert travel_time(e,e['capacity']*2)>travel_time(e,0)


def test_mid_edge_closure_no_teleport():
    sim=Simulation();sim.start('self_induced',20,'distance');sim.tick()
    p=sim.agents[0];pid=p.edge_id;progress=p.progress
    sim.close(pid);sim.tick()
    assert p.edge_id==pid and p.progress>progress
    assert_conserved(sim)
    sim.close(pid,False)


def test_disconnected_wait_then_reopen():
    sim=Simulation();sim.start('self_induced',10)
    for _,e in sim.graph['12'].items():e['closed']=True
    sim.step(5);assert sim.metrics()['waiting']==10;assert_conserved(sim)
    for _,e in sim.graph['12'].items():e['closed']=False
    sim.tick();assert sim.metrics()['walking']==10


def test_zero_and_identical():
    sim=Simulation();assert sim.start('normal',0)['status']=='completed'
    sim.start(requests=[{'source':'8','destination':'8','demand':5,'departure':0}]);sim.tick()
    assert sim.metrics()['completed']==5;assert sim.metrics()['walking']==0


def test_comparison_identical_demand_and_reproducibility():
    a=compare(None,'self_induced',30);b=compare(None,'self_induced',30)
    assert len(a['rows'])==3
    for x,y in zip(a['rows'],b['rows']):
        assert x['population']==30 and x['completion_rate']==1
        for key in ('average_travel_seconds','p95_travel_seconds','maximum_pathway_occupancy','time_above_capacity_edge_seconds','rerouting_count'):
            assert x[key]==y[key]


def test_capacity_time_includes_the_last_occupied_interval():
    sim=Simulation();sim.start('self_induced',80,'distance');sim.tick()
    assert all(p.status=='walking' for p in sim.agents)
    before=sim.capacity_edge_seconds
    for p in sim.agents:p.progress=sim.edge_lookup[p.edge_id][2]['distance']-.01
    sim.tick()
    assert all(p.status=='waiting' for p in sim.agents)
    assert sim.capacity_edge_seconds-before==5
    assert_conserved(sim)
