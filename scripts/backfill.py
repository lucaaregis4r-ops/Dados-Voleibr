"""Standalone equivalent of `python -m cbv backfill`, avoids eager legacy DB imports."""
import sys,argparse,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cbv.backfill import run_backfill
from cbv.config import DUCKDB_PATH,RAW_DIR


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--competition');parser.add_argument('--season');parser.add_argument('--limit',type=int)
    parser.add_argument('--workers',type=int,default=3);parser.add_argument('--interval',type=float,default=.6);parser.add_argument('--cached-only',action='store_true')
    args=parser.parse_args();result=run_backfill(DUCKDB_PATH,RAW_DIR/'matches',args.competition,args.season,args.limit,args.workers,args.interval,not args.cached_only)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
