from playwright.sync_api import APIResponse

from core.api_clients.base_client import BaseClient


class BrandingClient(BaseClient):
    BRANDING = "/api/branding"

    def get_branding(self) -> APIResponse:
        """Public. 200 {"name", "description", "address", "contact", "map", ...}."""
        return self._send("GET", self.BRANDING)
