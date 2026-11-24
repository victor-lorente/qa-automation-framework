"""Fixtures shared by the step definitions: API contexts and admin authentication.

They live here (test layer) and not in the root conftest.py because they depend on the
API clients; the root conftest.py only handles configuration and safety guards.
"""

from collections.abc import Iterator
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import APIRequestContext, Playwright, StorageState

from core.api_clients.auth_client import AuthClient
from core.config import Settings
from core.utils.http_checks import require_status


@pytest.fixture
def anon_api(playwright: Playwright, settings: Settings) -> Iterator[APIRequestContext]:
    """Fresh, isolated, unauthenticated context per test.

    Login/logout tests always use this one, so they can never break the shared session.
    """
    context = playwright.request.new_context(base_url=settings.app_url)
    yield context
    context.dispose()


@pytest.fixture(scope="session")
def admin_token(playwright: Playwright, settings: Settings) -> str:
    """Log in once per session (= once per pytest-xdist worker)."""
    context = playwright.request.new_context(base_url=settings.app_url)
    try:
        response = AuthClient(context).login(
            settings.admin_user, settings.admin_password.get_secret_value()
        )
        require_status(response, 200, action="Admin login (session setup)")
        return response.json()["token"]
    finally:
        context.dispose()


@pytest.fixture(scope="session")
def admin_storage_state(admin_token: str, settings: Settings) -> StorageState:
    """The admin session as a cookie, reusable by API contexts and (later) the browser.

    RBP returns the token in the login body only; protected routes read a cookie `token`.
    """
    url = urlsplit(settings.app_url)
    # TODO: align httpOnly/sameSite with the cookie the browser gets after a real UI
    # login (inspect context.cookies() once the UI layer exists).
    return {
        "cookies": [
            {
                "name": "token",
                "value": admin_token,
                "domain": url.hostname or "",
                "path": "/",
                "expires": -1,
                "httpOnly": False,
                "secure": url.scheme == "https",
                "sameSite": "Lax",
            }
        ],
        "origins": [],
    }


@pytest.fixture(scope="session")
def admin_api(
    playwright: Playwright, settings: Settings, admin_storage_state: StorageState
) -> Iterator[APIRequestContext]:
    """Shared authenticated context for setup and verification. Never log out with it."""
    context = playwright.request.new_context(
        base_url=settings.app_url, storage_state=admin_storage_state
    )
    yield context
    context.dispose()
