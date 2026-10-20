"""HTTP client wrapper with rate limiting, retries, and custom user-agent."""

import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from cbv.config import (
    USER_AGENT,
    REQUEST_TIMEOUT,
    REQUEST_DELAY,
    MAX_RETRIES,
    logger,
)


class HttpClient:
    """Robust HTTP client for polite scraping."""

    def __init__(
        self,
        user_agent: str = USER_AGENT,
        timeout: int = REQUEST_TIMEOUT,
        delay: float = REQUEST_DELAY,
        max_retries: int = MAX_RETRIES,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.delay = delay
        self.max_retries = max_retries
        self._last_request_time = 0.0

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _apply_delay(self):
        """Enforces a courteous interval between consecutive requests."""
        if self.delay > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()

    def get(self, url: str, **kwargs) -> requests.Response:
        """Performs a GET request with automatic delay, timeout, and error handling."""
        self._apply_delay()
        kwargs.setdefault("timeout", self.timeout)
        logger.debug(f"HTTP GET {url}")
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response

    def download(self, url: str, **kwargs) -> bytes:
        """Downloads raw binary content from a given URL."""
        response = self.get(url, **kwargs)
        return response.content


# Default singleton instance
default_client = HttpClient()
