from playwright.sync_api import APIResponse

from core.api_clients.base_client import BaseClient


class HealthClient(BaseClient):
    """Spring Boot actuator health endpoints, exposed only on each service's own port.

    They are not reachable through the front end's /api routes, so callers pass the
    absolute URL (see ``Settings.health_urls``); an absolute URL overrides the
    context's base_url.
    """

    def check(self, health_url: str) -> APIResponse:
        """200 {"status": "UP", "groups": [...]} when the service is healthy."""
        return self._send("GET", health_url)
