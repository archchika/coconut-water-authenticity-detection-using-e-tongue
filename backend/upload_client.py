"""
Phase 5.2 — Upload client for POST /api/upload-data/

Retry with backoff, log failures locally, optional in-memory queue when offline.
Use from gateway (e.g. Raspberry Pi) to send readings to Django.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2


def upload_reading(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: int | float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    log: logging.Logger | None = None,
) -> bool:
    """
    POST payload to url (e.g. https://api.example.com/api/upload-data/).
    Retries with exponential backoff on 5xx, connection errors, timeouts.
    Logs failures locally. Returns True if a attempt succeeded (2xx).
    """
    log = log or logger
    for attempt in range(max_retries):
        try:
            r = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"},
            )
            if 200 <= r.status_code < 300:
                return True
            log.warning(
                "upload_reading attempt %d/%d failed: HTTP %d %s",
                attempt + 1,
                max_retries,
                r.status_code,
                r.text[:200] if r.text else "",
            )
        except (requests.RequestException, OSError) as e:
            log.warning(
                "upload_reading attempt %d/%d error: %s",
                attempt + 1,
                max_retries,
                e,
            )
        if attempt < max_retries - 1:
            delay = backoff_factor ** attempt
            time.sleep(delay)
    log.error(
        "upload_reading failed after %d retries to %s",
        max_retries,
        url,
    )
    return False


class UploadQueue:
    """
    Optional queue for when offline: append payloads on failure, flush when online.
    Optional size limit to avoid unbounded growth.
    """

    def __init__(self, max_size: int = 100):
        self._queue: deque[dict[str, Any]] = deque(maxlen=max_size if max_size > 0 else 0)

    def push(self, payload: dict[str, Any]) -> None:
        if self._queue.maxlen and len(self._queue) >= self._queue.maxlen:
            self._queue.popleft()
        self._queue.append(payload)

    def __len__(self) -> int:
        return len(self._queue)

    def flush(
        self,
        url: str,
        *,
        timeout: int | float = DEFAULT_TIMEOUT,
        max_retries: int = 1,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        log: logging.Logger | None = None,
    ) -> int:
        """
        Try to send each queued payload; remove on success. Returns number sent.
        """
        log = log or logger
        sent = 0
        while self._queue:
            payload = self._queue[0]
            if upload_reading(
                url,
                payload,
                timeout=timeout,
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                log=log,
            ):
                self._queue.popleft()
                sent += 1
            else:
                break
        return sent

    def enqueue_on_failure(self, payload: dict[str, Any]) -> None:
        """Call when upload_reading returned False to queue for later."""
        self.push(payload)
