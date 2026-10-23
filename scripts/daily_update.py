"""03:00 BRT entrypoint: build everything in isolation, then promote validated artifacts."""
import sys,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from cbv.pipeline import staged_update


def run_full_daily_pipeline():
    def worker(data,publish):
        env=dict(os.environ,CBV_DATA_DIR=str(data),CBV_PUBLISH_DIR=str(publish))
        subprocess.run([sys.executable,str(ROOT/'scripts/daily_worker.py')],cwd=ROOT,env=env,check=True)
    staged_update(ROOT,worker)
    return True

if __name__=='__main__':run_full_daily_pipeline()
