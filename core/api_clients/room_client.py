from typing import Any

from playwright.sync_api import APIResponse

from core.api_clients.base_client import BaseClient


class RoomClient(BaseClient):
    """Room service, through the front end's /api proxy (RBP >= 2069ba1c)."""

    ROOMS = "/api/room"

    def list_rooms(self) -> APIResponse:
        """Public. 200 {"rooms": [{"roomid", "roomName", "type", "roomPrice", ...}]}."""
        return self._send("GET", self.ROOMS)

    def create_room(self, payload: dict[str, Any]) -> APIResponse:
        """Admin only. 201 with the created room (including "roomid").

        Validation: 400 {"error", "errorCode", "fieldErrors": [...]}.
        No session or invalid session: 403 (empty body). Room names may repeat.
        """
        return self._send("POST", self.ROOMS, data=payload)

    def get_room(self, room_id: int) -> APIResponse:
        """Public. 200 with the room."""
        return self._send("GET", f"{self.ROOMS}/{room_id}")

    def delete_room(self, room_id: int) -> APIResponse:
        """Admin only. 202."""
        return self._send("DELETE", f"{self.ROOMS}/{room_id}")
