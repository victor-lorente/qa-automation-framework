from playwright.sync_api import Page

from core.page_objects.base_page import BasePage


class AdminLoginPage(BasePage):
    """Admin login form at /admin. Locators chosen with Playwright codegen."""

    PATH = "/admin"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username_input = page.get_by_role("textbox", name="Username")
        self.password_input = page.get_by_role("textbox", name="Password")
        self.login_button = page.get_by_role("button", name="Login")
        self.error_message = page.get_by_text("Invalid credentials")

    def login_as(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
