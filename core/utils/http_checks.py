"""Readable, secret-safe checks on Playwright ``APIResponse`` objects.

- ``expect_status``: an assertion, for Then steps. A mismatch is a test FAILURE.
- ``require_status``: a precondition, for fixtures and Given steps. A mismatch is a
  setup ERROR, so the report separates "the environment was not ready" from
  "the behaviour is wrong".
"""

import json
import re
from typing import Any

from playwright.sync_api import APIResponse

SENSITIVE_KEY = re.compile(r"(?i)token|password|secret|cookie")
MAX_BODY_CHARS = 1000


class ApiPreconditionError(RuntimeError):
    """Raised when API setup fails; pytest reports it as ERROR, not FAILED."""


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: "***" if SENSITIVE_KEY.search(k) else _redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def describe(response: APIResponse) -> str:
    """Status, URL and (redacted, truncated) body of a response."""
    try:
        body = json.dumps(_redact(response.json()), ensure_ascii=False)
    except Exception:  # not JSON: HTML error page, empty body...
        body = response.text()
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS] + "...(truncated)"
    return f"{response.status} {response.status_text} <- {response.url}\nBody: {body}"


def expect_status(response: APIResponse, expected: int) -> None:
    """Assert the HTTP status in Then steps."""
    __tracebackhide__ = True  # keep this helper's frame out of pytest tracebacks
    if response.status != expected:
        raise AssertionError(f"Expected HTTP {expected}, got {describe(response)}")


def require_status(response: APIResponse, expected: int, *, action: str) -> None:
    """Check a precondition in fixtures and Given steps."""
    __tracebackhide__ = True
    if response.status != expected:
        raise ApiPreconditionError(
            f"{action} failed: expected HTTP {expected}, got {describe(response)}"
        )
