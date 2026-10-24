SCENARIOS=[
 {'id':'normal','name':'Normal Campus Movement','description':'Distributed trips over five minutes. Detours may add time at low demand.','minute':570,'population':120,'window':300},
 {'id':'lunch','name':'Lunch Break Congestion','description':'Students from multiple blocks converge on the cafeteria.','minute':735,'population':450,'window':60},
 {'id':'exam','name':'Examination Hall Rush','description':'Hundreds leave hostels and classrooms for the examination hall.','minute':535,'population':550,'window':90},
 {'id':'closure','name':'Unexpected Corridor Closure','description':'P025 closes after 60 simulated seconds; pedestrians on it finish safely.','minute':660,'population':300,'window':120,'closure_at':60,'close_pathway':'P025'},
 {'id':'self_induced','name':'Self-Induced Congestion','description':'A simultaneous 500-person entrance-to-cafeteria request overloads the shortest corridor.','minute':710,'population':500,'window':0}
]


def get_scenario(sid):
    return next(s for s in SCENARIOS if s['id']==sid)
