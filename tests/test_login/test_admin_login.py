import re

from playwright.sync_api import APIRequestContext, APIResponse, Page, expect
from pytest_bdd import parsers, scenarios, then, when

from core.api_clients.auth_client import AuthClient, session_token
from core.config import Settings
from core.page_objects.admin.login_page import AdminLoginPage
from core.page_objects.components.admin_nav import AdminNav
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
    # Never print the token itself.
    assert session_token(login_response), "Login response did not set a 'token' session cookie"


@then("the session token is valid")
def token_is_valid(login_response: APIResponse, anon_api: APIRequestContext) -> None:
    response = AuthClient(anon_api).validate(session_token(login_response) or "")
    expect_status(response, 200)


@then("the login is rejected as invalid credentials")
def login_rejected(login_response: APIResponse) -> None:
    expect_status(login_response, 403)
    assert session_token(login_response) is None, "A rejected login must not open a session"


# --- UI ------------------------------------------------------------------------------


@when("the admin logs in through the login form")
def admin_logs_in_through_form(admin_login_page: AdminLoginPage, settings: Settings) -> None:
    admin_login_page.open()
    admin_login_page.login_as(settings.admin_user, settings.admin_password.get_secret_value())


@when(parsers.parse('the admin logs in through the login form with password "{password}"'))
def admin_logs_in_through_form_with(
    admin_login_page: AdminLoginPage, settings: Settings, password: str
) -> None:
    admin_login_page.open()
    admin_login_page.login_as(settings.admin_user, password)


@then("the admin area is shown")
def admin_area_shown(admin_nav: AdminNav, page: Page) -> None:
    expect(page).to_have_url(re.compile(r"/admin/rooms$"))
    expect(admin_nav.rooms_link).to_be_visible()


@then("the login form reports invalid credentials")
def login_form_reports_error(admin_login_page: AdminLoginPage) -> None:
    expect(admin_login_page.error_message).to_be_visible()


@then("the admin area is not shown")
def admin_area_not_shown(admin_nav: AdminNav) -> None:
    expect(admin_nav.rooms_link).not_to_be_visible()
