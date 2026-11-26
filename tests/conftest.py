"""Fixtures shared by the step definitions: API contexts and admin authentication.

They live here (test layer) and not in the root conftest.py because they depend on the
API clients; the root conftest.py only handles configuration and safety guards.
"""

from collections.abc import Iterator

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
def admin_storage_state(playwright: Playwright, settings: Settings) -> StorageState:
    """Log in once per session (= once per pytest-xdist worker) and keep the session cookie.

    RBP sets the session as a cookie (`token`) on login, so the context stores it exactly
    as the server sent it. The resulting storage state is reusable by API contexts and,
    later, by the browser.
    """
    context = playwright.request.new_context(base_url=settings.app_url)
    try:
        response = AuthClient(context).login(
            settings.admin_user, settings.admin_password.get_secret_value()
        )
        require_status(response, 200, action="Admin login (session setup)")
        return context.storage_state()
    finally:
        context.dispose()


@pytest.fixture(scope="session")
def admin_api(
    playwright: Playwright, settings: Settings, admin_storage_state: StorageState
) -> Iterator[APIRequestContext]:
    """Shared authenticated context for setup and verification. Never log out with it:
    logout invalidates the token for every test in the session."""
    context = playwright.request.new_context(
        base_url=settings.app_url, storage_state=admin_storage_state
    )
    yield context
    context.dispose()
