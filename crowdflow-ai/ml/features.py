from math import sin,cos,pi
import pandas as pd

FEATURES=['time_sin','time_cos','weekday','class_change','lunch','exam','event','occupancy',
          'lag_5','lag_10','rolling_mean','arrival_rate','distance','width','capacity','zone']


def schedule(minute,day,exam=False,event=False):
    return {'time_sin':sin(2*pi*minute/1440),'time_cos':cos(2*pi*minute/1440),'weekday':day%7,
            'class_change':int(any(abs(minute-t)<=10 for t in (540,600,660,840,900,960))),
            'lunch':int(720<=minute<810),'exam':int(exam),'event':int(event)}


def feature_row(edge,minute,day,history=None,arrival_rate=0,exam=False,event=False):
    history=history or [edge['occupancy']]*3
    return dict(schedule(minute,day,exam,event),occupancy=float(edge['occupancy']),
                lag_5=float(history[-2] if len(history)>1 else history[-1]),
                lag_10=float(history[-3] if len(history)>2 else history[-1]),
                rolling_mean=sum(history[-3:])/len(history[-3:]),arrival_rate=float(arrival_rate),
                distance=edge['distance'],width=edge['width'],capacity=edge['capacity'],zone=edge['zone'])


def frame(rows):return pd.DataFrame(rows)[FEATURES].astype(float)
