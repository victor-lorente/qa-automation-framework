from playwright.sync_api import APIResponse

from core.api_clients.base_client import BaseClient

SESSION_COOKIE = "token"


class AuthClient(BaseClient):
    """Auth service, through the front end's /api proxy (RBP >= 2069ba1c)."""

    LOGIN = "/api/auth/login"
    VALIDATE = "/api/auth/validate"
    LOGOUT = "/api/auth/logout"

    def login(self, username: str, password: str) -> APIResponse:
        """200 with an empty body and ``Set-Cookie: token=...; Path=/`` on success.

        Invalid credentials (wrong, unknown or empty): 403 with an empty body.
        The context stores the cookie, so later requests on it are authenticated.
        """
        return self._send("POST", self.LOGIN, data={"username": username, "password": password})

    def validate(self, token: str) -> APIResponse:
        """200 (empty body) for a live token, 403 otherwise. Token in a JSON body, not a cookie."""
        return self._send("POST", self.VALIDATE, data={"token": token})


def session_token(response: APIResponse) -> str | None:
    """The session token set by a login response, or None. Never log or print it."""
    for header in response.headers_array:
        if header["name"].lower() == "set-cookie":
            name, _, rest = header["value"].partition("=")
            if name.strip() == SESSION_COOKIE:
                return rest.split(";", 1)[0] or None
    return None
