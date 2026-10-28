"""Configuration settings and logging setup for CBV Volley Data."""

from pathlib import Path
import logging
import os
import sys

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("CBV_DATA_DIR", BASE_DIR / "data"))
RAW_DIR = DATA_DIR / "raw"
RAW_PAGES_DIR = RAW_DIR / "pages"
RAW_REPORTS_DIR = RAW_DIR / "reports"
PROCESSED_DIR = DATA_DIR / "processed"
DUCKDB_PATH = DATA_DIR / "cbv.duckdb"
LOG_DIR = Path(os.getenv("CBV_LOG_DIR", BASE_DIR / "logs"))
LOG_FILE = LOG_DIR / "cbv.log"

# Network & Scraping Settings
BASE_URL = os.getenv("CBV_BASE_URL", "https://cbv.com.br")
USER_AGENT = os.getenv("CBV_USER_AGENT", "CBVVolleyData/0.1 research-project")
REQUEST_TIMEOUT = int(os.getenv("CBV_REQUEST_TIMEOUT", "30"))
REQUEST_DELAY = float(os.getenv("CBV_REQUEST_DELAY", "1.0"))
MAX_RETRIES = int(os.getenv("CBV_MAX_RETRIES", "3"))

# Ensure essential directories exist
for path in [DATA_DIR, RAW_DIR, RAW_PAGES_DIR, RAW_REPORTS_DIR, PROCESSED_DIR, LOG_DIR]:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        if not path.is_dir():
            raise


def setup_logger(name: str = "cbv", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured logger writing to both console and logs/cbv.log."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
    # Suppress verbose warnings from third party libraries
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger


logger = setup_logger()

