"""Test data builders: valid defaults, so each test only states what it cares about."""

import uuid
from typing import Any

ROOM_NAME_PREFIX = "QA-"


def unique_room_name() -> str:
    """RBP accepts duplicate room names, so uniqueness is what lets cleanup find our rooms."""
    return f"{ROOM_NAME_PREFIX}{uuid.uuid4().hex[:8]}"


def room_payload(**overrides: Any) -> dict[str, Any]:
    """A valid room; override any field (e.g. room_payload(roomPrice=0))."""
    payload: dict[str, Any] = {
        "roomName": unique_room_name(),
        "type": "Single",
        "accessible": False,
        "roomPrice": 100,
        "description": "Room created by an automated test",
        "image": "/images/room1.jpg",
        "features": [],
    }
    payload.update(overrides)
    return payload
