from playwright.sync_api import APIRequestContext, APIResponse
from pytest_bdd import parsers, scenarios, then, when

from core.api_clients.branding_client import BrandingClient
from core.api_clients.health_client import HealthClient
from core.api_clients.room_client import RoomClient
from core.config import Settings
from core.utils.http_checks import expect_status

scenarios("infrastructure/platform_health.feature")


@when(parsers.parse('the health of the "{service}" service is checked'), target_fixture="response")
def check_service_health(anon_api: APIRequestContext, settings: Settings, service: str) -> APIResponse:
    return HealthClient(anon_api).check(settings.health_urls[service])


@when("a visitor requests the list of rooms", target_fixture="response")
def request_rooms(anon_api: APIRequestContext) -> APIResponse:
    return RoomClient(anon_api).list_rooms()


@when("a visitor requests the B&B details", target_fixture="response")
def request_branding(anon_api: APIRequestContext) -> APIResponse:
    return BrandingClient(anon_api).get_branding()


@then("the service reports it is up")
def service_is_up(response: APIResponse) -> None:
    expect_status(response, 200)
    assert response.json().get("status") == "UP", f"Unexpected health body: {response.json()}"


@then("a list of rooms is returned")
def rooms_returned(response: APIResponse) -> None:
    expect_status(response, 200)
    rooms = response.json().get("rooms")
    # A list, possibly empty: the public site is shared and its content can change.
    assert isinstance(rooms, list), f"'rooms' is not a list: {response.json()}"


@then("the B&B details include its name")
def branding_has_name(response: APIResponse) -> None:
    expect_status(response, 200)
    name = response.json().get("name")
    assert isinstance(name, str) and name.strip(), f"Branding has no name: {response.json()}"
