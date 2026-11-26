from playwright.sync_api import Locator, Page

from core.page_objects.base_page import BasePage
from core.page_objects.components.admin_nav import AdminNav


class AdminRoomsPage(BasePage):
    """Room list (and create form) at /admin/rooms. Landing page after an admin login."""

    PATH = "/admin/rooms"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.nav = AdminNav.on(page)
        # Rows are plain <div>/<p> without accessible roles or labels, so the
        # developer-provided test id is the stable contract here.
        self._room_rows = page.get_by_test_id("roomlisting")

    def room_row(self, room_name: str) -> Locator:
        """The row of the room with this name (names are unique in tests)."""
        return self._room_rows.filter(has_text=room_name)
