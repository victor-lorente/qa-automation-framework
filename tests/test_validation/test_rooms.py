from dataclasses import dataclass
from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse, Playwright, expect
from pytest_bdd import given, parsers, scenarios, then, when

from core.api_clients.room_client import RoomClient
from core.config import Settings
from core.page_objects.admin.rooms_page import AdminRoomsPage
from core.utils.http_checks import expect_status, require_status
from core.utils.test_data import room_payload

scenarios("validation/rooms.feature")

# Invalid-data examples in the .feature map to these payload fields.
FIELDS = {"name": "roomName", "type": "type", "price": "roomPrice"}


@dataclass
class RoomCreation:
    payload: dict[str, Any]
    response: APIResponse


def rooms_named(listing: APIResponse, name: str) -> list[dict[str, Any]]:
    return [room for room in listing.json()["rooms"] if room["roomName"] == name]


def create_room(client: RoomClient, cleanup: list[str], payload: dict[str, Any]) -> RoomCreation:
    """Register the name for cleanup BEFORE sending, so even unexpected creations are deleted."""
    if payload.get("roomName"):
        cleanup.append(payload["roomName"])
    return RoomCreation(payload, client.create_room(payload))


# --- Given ---------------------------------------------------------------------------


@given("the admin is logged in", target_fixture="admin_rooms")
def admin_logged_in(admin_api: APIRequestContext) -> RoomClient:
    return RoomClient(admin_api)


@given("the admin has created a room", target_fixture="existing_room")
def admin_created_room(admin_api: APIRequestContext, room_cleanup: list[str]) -> dict[str, Any]:
    creation = create_room(RoomClient(admin_api), room_cleanup, room_payload())
    require_status(creation.response, 201, action="Create room (precondition)")
    return creation.response.json()


@given("the admin has deleted that room")
def admin_deleted_room(admin_api: APIRequestContext, existing_room: dict[str, Any]) -> None:
    response = RoomClient(admin_api).delete_room(existing_room["roomid"])
    require_status(response, 202, action="Delete room (precondition)")


@given("there is at least one room", target_fixture="existing_room")
def at_least_one_room(anon_api: APIRequestContext) -> dict[str, Any]:
    listing = RoomClient(anon_api).list_rooms()
    require_status(listing, 200, action="List rooms (precondition)")
    rooms = listing.json()["rooms"]
    if not rooms:
        raise AssertionError("Precondition failed: the environment has no rooms")
    return rooms[0]


# --- When ----------------------------------------------------------------------------


@when(
    parsers.re(
        r'the admin creates a "(?P<room_type>\w+)" room priced at (?P<price>\d+) '
        r'with features "(?P<features>[^"]*)"'
    ),
    converters={"price": int},
    target_fixture="creation",
)
def admin_creates_room(
    admin_rooms: RoomClient, room_cleanup: list[str], room_type: str, price: int, features: str
) -> RoomCreation:
    feature_list = [f.strip() for f in features.split(",") if f.strip()]
    payload = room_payload(type=room_type, roomPrice=price, accessible=True, features=feature_list)
    return create_room(admin_rooms, room_cleanup, payload)


@when(
    parsers.re(r'the admin creates a room with (?P<field>name|type|price) "(?P<value>[^"]*)"'),
    target_fixture="creation",
)
def admin_creates_invalid_room(
    admin_rooms: RoomClient, room_cleanup: list[str], field: str, value: str
) -> RoomCreation:
    typed_value: Any = int(value) if field == "price" else value
    return create_room(admin_rooms, room_cleanup, room_payload(**{FIELDS[field]: typed_value}))


@when("a visitor tries to create a room", target_fixture="creation")
def visitor_creates_room(anon_api: APIRequestContext, room_cleanup: list[str]) -> RoomCreation:
    return create_room(RoomClient(anon_api), room_cleanup, room_payload())


@when("someone with an invalid session tries to create a room", target_fixture="creation")
def invalid_session_creates_room(
    playwright: Playwright, settings: Settings, room_cleanup: list[str]
) -> RoomCreation:
    context = playwright.request.new_context(
        base_url=settings.app_url, extra_http_headers={"Cookie": "token=not-a-valid-token"}
    )
    try:
        creation = create_room(RoomClient(context), room_cleanup, room_payload())
        creation.response.body()  # read before dispose: disposing frees response bodies
        return creation
    finally:
        context.dispose()


@when("a visitor requests the details of that room", target_fixture="response")
def visitor_requests_room(anon_api: APIRequestContext, existing_room: dict[str, Any]) -> APIResponse:
    return RoomClient(anon_api).get_room(existing_room["roomid"])


@when("the admin deletes that room", target_fixture="response")
def admin_deletes_room(admin_api: APIRequestContext, existing_room: dict[str, Any]) -> APIResponse:
    return RoomClient(admin_api).delete_room(existing_room["roomid"])


# --- Then ----------------------------------------------------------------------------


@then("the room is created")
def room_created(creation: RoomCreation) -> None:
    expect_status(creation.response, 201)
    room = creation.response.json()
    assert isinstance(room.get("roomid"), int), f"Created room has no id: {room}"
    assert room.get("roomName") == creation.payload["roomName"], f"Unexpected room: {room}"


@then("visitors see the new room with its details")
def visitors_see_room(anon_api: APIRequestContext, creation: RoomCreation) -> None:
    listing = RoomClient(anon_api).list_rooms()
    expect_status(listing, 200)
    matches = rooms_named(listing, creation.payload["roomName"])
    assert len(matches) == 1, f"Expected 1 room named {creation.payload['roomName']!r}, found {len(matches)}"
    room, expected = matches[0], creation.payload
    for field in ("type", "roomPrice", "accessible", "features"):
        assert room[field] == expected[field], f"{field}: expected {expected[field]!r}, got {room[field]!r}"


@then(parsers.parse('the room is rejected with the message "{message}"'))
def room_rejected(creation: RoomCreation, message: str) -> None:
    expect_status(creation.response, 400)
    errors = creation.response.json().get("fieldErrors", [])
    assert message in errors, f"Expected error {message!r}, got {errors}"


@then("the request is forbidden")
def request_forbidden(creation: RoomCreation) -> None:
    expect_status(creation.response, 403)


@then("the details of that room are returned")
def room_details_returned(response: APIResponse, existing_room: dict[str, Any]) -> None:
    expect_status(response, 200)
    assert response.json().get("roomid") == existing_room["roomid"], f"Unexpected room: {response.json()}"


@then("the room no longer appears in the list of rooms")
def room_gone(response: APIResponse, anon_api: APIRequestContext, existing_room: dict[str, Any]) -> None:
    expect_status(response, 202)
    listing = RoomClient(anon_api).list_rooms()
    expect_status(listing, 200)
    assert not rooms_named(listing, existing_room["roomName"]), "The deleted room is still listed"


@then("the room is reported as not found")
def room_not_found(response: APIResponse) -> None:
    expect_status(response, 404)


# --- UI (hybrid: data prepared through the API, checked in the browser) ------------


@given("the admin is signed in to the admin area")
def admin_signed_in_to_admin_area(admin_signed_in: None) -> None:
    """The browser reuses the API admin session (cookie), so no login form is involved."""


@when("the admin opens the room list")
def admin_opens_room_list(admin_rooms_page: AdminRoomsPage) -> None:
    admin_rooms_page.open()


@then("the room is listed with its type and price")
def room_listed(admin_rooms_page: AdminRoomsPage, existing_room: dict[str, Any]) -> None:
    row = admin_rooms_page.room_row(existing_room["roomName"])
    expect(row).to_be_visible()
    expect(row).to_contain_text(existing_room["type"])
    expect(row).to_contain_text(str(existing_room["roomPrice"]))
