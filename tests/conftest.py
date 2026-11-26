"""Fixtures shared by the step definitions: API contexts, admin session and page objects.

They live here (test layer) and not in the root conftest.py because they depend on the
API clients and page objects; the root conftest.py only handles configuration and safety guards.
"""

from collections.abc import Iterator

import pytest
from playwright.sync_api import APIRequestContext, BrowserContext, Page, Playwright, StorageState

from core.api_clients.auth_client import AuthClient
from core.api_clients.room_client import RoomClient
from core.config import Settings
from core.page_objects.admin.login_page import AdminLoginPage
from core.page_objects.admin.rooms_page import AdminRoomsPage
from core.page_objects.components.admin_nav import AdminNav
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


@pytest.fixture
def room_cleanup(admin_api: APIRequestContext) -> Iterator[list[str]]:
    """Register room names BEFORE creating them; they are deleted after the test, even if it fails.

    Registering first also catches rooms created by mistake (e.g. a validation regression
    in a negative test), whose id the test never saw. Rooms are found by name, so names
    must be unique (RBP accepts duplicates).
    """
    names: list[str] = []
    yield names
    if not names:
        return
    rooms = RoomClient(admin_api)
    listing = rooms.list_rooms()
    require_status(listing, 200, action="Room cleanup: list rooms")
    for room in listing.json()["rooms"]:
        if room["roomName"] in names:
            require_status(
                rooms.delete_room(room["roomid"]), 202, action=f"Room cleanup: delete {room['roomName']}"
            )


# --- UI ------------------------------------------------------------------------------
# Page objects wrap pytest-playwright's `page` (function scope), so every test gets a
# fresh browser context and keeps --tracing / --screenshot support.


@pytest.fixture
def admin_login_page(page: Page) -> AdminLoginPage:
    return AdminLoginPage(page)


@pytest.fixture
def admin_rooms_page(page: Page) -> AdminRoomsPage:
    return AdminRoomsPage(page)


@pytest.fixture
def admin_nav(page: Page) -> AdminNav:
    return AdminNav.on(page)


@pytest.fixture
def admin_signed_in(context: BrowserContext, admin_storage_state: StorageState) -> None:
    """Reuse the API admin session in the browser: no login form unless login is under test."""
    context.add_cookies(admin_storage_state["cookies"])
