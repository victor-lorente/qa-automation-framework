"""What every page has in common: the Playwright Page and its own route. Nothing else.

Deliberately minimal: Playwright already auto-waits and pytest-playwright injects the
page, so there are no click/fill wrappers or generic waits here. Shared UI pieces (e.g.
the admin navigation bar) are reused by composition (components/), not by inheritance.
"""

from typing import ClassVar

from playwright.sync_api import Page


class BasePage:
    PATH: ClassVar[str]

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> None:
        # Relative path: resolved against the base_url fixture (settings.app_url).
        self.page.goto(self.PATH)
