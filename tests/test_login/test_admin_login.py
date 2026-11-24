from playwright.sync_api import APIRequestContext, APIResponse
from pytest_bdd import parsers, scenarios, then, when

from core.api_clients.auth_client import AuthClient
from core.config import Settings
from core.utils.http_checks import expect_status

scenarios("login/admin_login.feature")


@when("the admin logs in with valid credentials", target_fixture="login_response")
def admin_logs_in(anon_api: APIRequestContext, settings: Settings) -> APIResponse:
    return AuthClient(anon_api).login(
        settings.admin_user, settings.admin_password.get_secret_value()
    )


@when(
    parsers.re(r'someone logs in with username "(?P<username>[^"]*)" and password "(?P<password>[^"]*)"'),
    target_fixture="login_response",
)
def someone_logs_in(anon_api: APIRequestContext, username: str, password: str) -> APIResponse:
    return AuthClient(anon_api).login(username, password)


@then("the login is accepted")
def login_accepted(login_response: APIResponse) -> None:
    expect_status(login_response, 200)
    token = login_response.json().get("token")
    # Never print the token itself.
    assert isinstance(token, str) and token, "Login response has no non-empty 'token'"


@then("the session token is valid")
def token_is_valid(login_response: APIResponse, anon_api: APIRequestContext) -> None:
    response = AuthClient(anon_api).validate(login_response.json()["token"])
    expect_status(response, 200)
    assert response.json() == {"valid": True}, f"Unexpected validate body: {response.json()}"


@then("the login is rejected as invalid credentials")
def login_rejected(login_response: APIResponse) -> None:
    expect_status(login_response, 401)
    assert login_response.json() == {"error": "Invalid credentials"}, (
        f"Unexpected error body: {login_response.json()}"
    )
