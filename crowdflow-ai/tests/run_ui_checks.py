"""Own a local server for the React/real-API integration suite, and always stop it."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def main():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        env=os.environ.copy();env['CROWDFLOW_DB']=str(Path(tmp)/'ui.sqlite3')
        server=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app:app','--host','127.0.0.1','--port','8000'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=time.monotonic()+45
            while True:
                if server.poll() is not None:raise RuntimeError('Test API server could not start. Check that port 8000 is free.')
                try:
                    with urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=1) as r:
                        if r.status==200:break
                except (OSError,TimeoutError):
                    if time.monotonic()>deadline:raise RuntimeError('API did not become ready')
                    time.sleep(.2)
            print('Real API is ready. Executing React DOM integration tests.',flush=True)
            npm_command=[shutil.which('npm') or 'npm','test']
            if os.name=='nt':npm_command=['cmd','/c']+npm_command
            result=subprocess.run(npm_command,cwd=ROOT/'frontend',env=env)
            if result.returncode:return result.returncode
            print('Executing the production ESM bundle smoke test.',flush=True)
            return subprocess.run([shutil.which('node') or 'node',str(ROOT/'tests/production_smoke.mjs')],cwd=ROOT,env=env).returncode
        finally:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait()


if __name__=='__main__':raise SystemExit(main())
