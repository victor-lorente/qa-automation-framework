from playwright.sync_api import APIResponse

from core.api_clients.base_client import BaseClient


class RoomClient(BaseClient):
    ROOMS = "/api/room"

    def list_rooms(self) -> APIResponse:
        """Public. 200 {"rooms": [{"roomid", "roomName", "type", "roomPrice", ...}]}."""
        return self._send("GET", self.ROOMS)
