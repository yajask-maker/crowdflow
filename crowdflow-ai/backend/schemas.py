from typing import Literal
from pydantic import BaseModel,Field,ConfigDict

Strategy=Literal['distance','congestion','adaptive','astar']
Scenario=Literal['normal','lunch','exam','closure','self_induced']


class Input(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)


class RouteRequest(Input):
    source:str
    destination:str
    demand:int=Field(default=100,ge=0,le=3000)
    strategy:Strategy='adaptive'
    departure_minute:float=Field(default=570,ge=0,lt=1440)
    day:int=Field(default=0,ge=0,le=6)


class MovementRequest(Input):
    source:str
    destination:str
    demand:int=Field(ge=0,le=1500)
    departure:float=Field(default=0,ge=0,le=3600)


class StartRequest(Input):
    scenario:Scenario='normal'
    population:int|None=Field(default=None,ge=0,le=1500)
    strategy:Strategy='adaptive'
    seed:int=Field(default=2026,ge=0,le=4294967295)
    minute:float|None=Field(default=None,ge=0,lt=1440)
    day:int=Field(default=0,ge=0,le=6)
    intensity:float=Field(default=1,ge=.2,le=3)
    requests:list[MovementRequest]|None=Field(default=None,max_length=50)


class StepRequest(Input):
    steps:int=Field(default=1,ge=1,le=60)


class ClosureRequest(Input):
    pathway_id:str
    closed:bool=True


class PredictRow(Input):
    pathway_id:str
    minute:float=Field(default=570,ge=0,lt=1440)
    day:int=Field(default=0,ge=0,le=6)
    occupancy:float=Field(default=0,ge=0,le=20000)
    lag_5:float|None=Field(default=None,ge=0,le=20000)
    lag_10:float|None=Field(default=None,ge=0,le=20000)
    arrival_rate:float=Field(default=0,ge=0,le=10000)
    exam:bool=False
    event:bool=False


class PredictRequest(Input):
    pathways:list[PredictRow]=Field(min_length=1,max_length=100)


class CompareRequest(Input):
    scenario:Scenario='self_induced'
    population:int|None=Field(default=None,ge=0,le=1000)
    seed:int=Field(default=2026,ge=0,le=4294967295)
    intensity:float=Field(default=1,ge=.2,le=3)
