from __future__ import annotations

import logging
import threading
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

_started = False


def start_self_ping() -> None:
    global _started

    if _started or not settings.SELF_PING_ENABLED or not settings.SELF_PING_URL:
        return

    _started = True
    interval = max(60, settings.SELF_PING_INTERVAL_SECONDS)

    def loop() -> None:
        while True:
            time.sleep(interval)
            request = Request(
                settings.SELF_PING_URL,
                headers={"User-Agent": "kindergarten-crm-self-ping"},
            )
            try:
                with urlopen(request, timeout=20) as response:
                    logger.info("Self ping completed with status %s", response.status)
            except (OSError, URLError) as exc:
                logger.warning("Self ping failed: %s", exc)

    thread = threading.Thread(target=loop, name="self-ping", daemon=True)
    thread.start()
