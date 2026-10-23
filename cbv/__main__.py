"""Main entrypoint for running cbv module via python -m cbv."""

import sys
if len(sys.argv)>1 and sys.argv[1]=='backfill':
    sys.argv.pop(1)
    from scripts.backfill import main
    main()
    raise SystemExit(0)

from cbv.cli import app

if __name__ == "__main__":
    app()
