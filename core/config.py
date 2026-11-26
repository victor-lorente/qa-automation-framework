"""Test-run configuration.

Single place where environment variables, the .env file and CLI overrides meet.
The rest of the framework receives a typed, immutable ``Settings`` object through
fixtures. This module must not import pytest, Playwright, page objects or API clients.

Source priority (highest first), provided by pydantic-settings:
    1. keyword arguments to ``load_settings`` (used for pytest CLI options)
    2. real environment variables (e.g. set by CI)
    3. the project's .env file
    4. defaults declared below
"""

from pathlib import Path
from typing import Literal

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

Environment = Literal["local", "remote"]

# Not secret, so they live in code instead of in per-environment files.
DEFAULT_URLS: dict[str, str] = {
    "local": "http://localhost",
    "remote": "https://automationintesting.online",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Absolute path: works no matter which directory pytest is started from.
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    env: Environment = "local"
    base_url: HttpUrl | None = None  # optional explicit override of DEFAULT_URLS
    admin_user: str  # required, no default
    admin_password: SecretStr  # required, masked in repr/logs/tracebacks

    @property
    def app_url(self) -> str:
        """Front-end URL without trailing slash; the API lives under f"{app_url}/api"."""
        return str(self.base_url or DEFAULT_URLS[self.env]).rstrip("/")


def load_settings(**overrides: object) -> Settings:
    """Build the settings; keyword overrides have the highest priority."""
    return Settings(**overrides)  # type: ignore[arg-type]
