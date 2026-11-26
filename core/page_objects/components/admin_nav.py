from playwright.sync_api import Locator, Page


class AdminNav:
    """Navigation bar shared by every /admin/* screen. Locators are searched inside `root`."""

    def __init__(self, root: Locator) -> None:
        self.root = root
        # Section links only exist with an admin session. NOTE: "Logout" is NOT a valid
        # signed-in signal: RBP also shows it on the login page to signed-out visitors.
        self.rooms_link = root.get_by_role("link", name="Rooms")
        self.logout_button = root.get_by_role("button", name="Logout")

    @classmethod
    def on(cls, page: Page) -> "AdminNav":
        # The bar is a <nav> element: accessible role "navigation".
        return cls(page.get_by_role("navigation"))
