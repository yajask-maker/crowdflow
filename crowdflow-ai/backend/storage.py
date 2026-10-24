import json
import os
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
DB=Path(os.environ.get('CROWDFLOW_DB',str(ROOT/'data/crowdflow.sqlite3')))


def init_db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(DB) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS experiments (id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, scenario TEXT, seed INTEGER, payload TEXT NOT NULL)')
        conn.execute('CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, kind TEXT, payload TEXT NOT NULL)')


def save_experiment(result):
    with sqlite3.connect(DB) as conn:
        cur=conn.execute('INSERT INTO experiments(scenario,seed,payload) VALUES(?,?,?)',
                         (result['scenario'],result['seed'],json.dumps(result)))
        return cur.lastrowid


def experiments():
    with sqlite3.connect(DB) as conn:
        return [{'id':i,'created_at':t,'scenario':s,'seed':seed} for i,t,s,seed in conn.execute('SELECT id,created_at,scenario,seed FROM experiments ORDER BY id DESC LIMIT 20')]


def log(kind,payload):
    with sqlite3.connect(DB) as conn:conn.execute('INSERT INTO actions(kind,payload) VALUES(?,?)',(kind,json.dumps(payload)))
