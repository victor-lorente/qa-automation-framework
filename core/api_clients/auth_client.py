from playwright.sync_api import APIResponse

from core.api_clients.base_client import BaseClient


class AuthClient(BaseClient):
    LOGIN = "/api/auth/login"
    VALIDATE = "/api/auth/validate"
    LOGOUT = "/api/auth/logout"

    def login(self, username: str, password: str) -> APIResponse:
        """200 {"token": ...} on success; 401 {"error": "Invalid credentials"} otherwise.

        The token comes only in the body (no Set-Cookie); protected routes expect it
        as a cookie named ``token``.
        """
        return self._send("POST", self.LOGIN, data={"username": username, "password": password})

    def validate(self, token: str) -> APIResponse:
        """200 {"valid": true} for a live token. Expects the token in a JSON body, not a cookie."""
        return self._send("POST", self.VALIDATE, data={"token": token})
