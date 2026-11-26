from playwright.sync_api import APIResponse

from core.api_clients.base_client import BaseClient


class HealthClient(BaseClient):
    """Spring Boot actuator health of each service, through the front end's /api proxy.

    Going through the proxy checks the service AND that the front end routes to it,
    and works in every environment (the per-service ports only exist locally).
    """

    def check(self, service: str) -> APIResponse:
        """200 {"status": "UP", "groups": [...]} when the service is healthy."""
        return self._send("GET", f"/api/{service}/actuator/health")
