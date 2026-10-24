"""Real HTTP startup, shutdown and restart check for the local launcher."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8010'


def request(path,body=None):
    encoded=json.dumps(body).encode() if body is not None else None
    req=urllib.request.Request(BASE+path,data=encoded,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=15) as response:
        data=response.read()
        return json.loads(data) if 'application/json' in response.headers.get('Content-Type','') else data


def boot(env):
    proc=subprocess.Popen([sys.executable,str(ROOT/'run.py'),'--port','8010'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for _ in range(150):
        if proc.poll() is not None:raise RuntimeError('Launcher failed')
        try:
            if request('/health')['model_loaded']:return proc
        except OSError:time.sleep(.1)
    proc.terminate();raise RuntimeError('Readiness timeout')


def stop(proc):
    proc.terminate()
    try:proc.wait(timeout=10)
    except subprocess.TimeoutExpired:proc.kill();proc.wait()


def main():
    with tempfile.TemporaryDirectory() as directory:
        env=dict(os.environ,CROWDFLOW_DB=str(Path(directory)/'restart.sqlite3'))
        p=boot(env)
        try:
            assert b'CrowdFlow' in request('/')
            assert request('/simulation/state')['status']=='idle'
            result=request('/route',{'source':'12','destination':'17','demand':100,'strategy':'adaptive'})
            assert sum(r['pedestrians'] for r in result['routes'])==100
            request('/simulate/start',{'scenario':'self_induced','population':40})
            state=request('/simulate/step',{'steps':4})
            assert state['metrics']['walking']>0
        finally:stop(p)
        p=boot(env)
        try:
            state=request('/simulation/state')
            assert state['status']=='idle' and state['metrics']['population']==0
            assert len(request('/graph')['nodes'])==36
            assert request('/model/metrics')['test']['mae']>0
        finally:stop(p)
    print('Real HTTP launcher/restart check passed.')


if __name__=='__main__':main()
