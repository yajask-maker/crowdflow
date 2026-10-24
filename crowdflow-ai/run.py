"""Launch the packaged dashboard and Python API on one local port."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent


def main():
    os.chdir(ROOT)
    parser=argparse.ArgumentParser(description='CrowdFlow AI local application')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--retrain',action='store_true')
    args=parser.parse_args()
    try:
        import uvicorn
        import sklearn
    except ImportError:
        print('Install dependencies first: python -m pip install -r requirements.txt')
        return 1
    if not (ROOT/'frontend/dist/index.html').exists():
        print('Build the frontend first: cd frontend, then npm ci and npm run build.')
        return 1
    metrics_path=ROOT/'ml/metrics.json'
    if metrics_path.exists():
        metrics=json.loads(metrics_path.read_text())
        if metrics['versions']['sklearn']!=sklearn.__version__ and not args.retrain:
            print('The supplied model requires scikit-learn '+metrics['versions']['sklearn']+'. Install requirements.txt or run python run.py --retrain.')
            return 1
    if args.retrain or not (ROOT/'ml/model.joblib').exists():
        from ml.train import train
        train()
        print('Model trained. Refresh measured scenarios with: python -m simulation.compare')
    print(f'CrowdFlow AI dashboard: http://{args.host}:{args.port}',flush=True)
    print(f'Interactive API documentation: http://{args.host}:{args.port}/docs',flush=True)
    print('Local demonstrator: fictional campus and synthetic data. Press Ctrl+C to stop.',flush=True)
    uvicorn.run('backend.app:app',host=args.host,port=args.port)
    return 0


if __name__=='__main__':raise SystemExit(main())
