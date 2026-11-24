"""HTTP transport shared by all API clients.

Clients only send requests and return the raw Playwright ``APIResponse``.
They never assert: the test (Then step) decides what the correct outcome is,
so negative cases (401, 400...) are as easy to test as positive ones.
"""

import logging
from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse

logger = logging.getLogger(__name__)


class BaseClient:
    def __init__(self, request: APIRequestContext) -> None:
        # Injected, so the same client works with an anonymous context, an
        # authenticated one, or page.request in a hybrid test.
        self._request = request

    def _send(self, method: str, path: str, **kwargs: Any) -> APIResponse:
        # Method + path only: headers and bodies may contain credentials or tokens.
        logger.info("%s %s", method, path)
        return self._request.fetch(path, method=method, **kwargs)
