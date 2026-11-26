"""Global pytest configuration: environment selection, settings, safety guards."""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.config import Settings, load_settings

SETTINGS_KEY = pytest.StashKey[Settings]()

# Stable scenario IDs used as Gherkin tags, e.g. @QA-12.
SCENARIO_ID_TAG = re.compile(r"@(QA-\d+)\b")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default=None,
        choices=("local", "remote"),
        help="Target environment (overrides ENV from environment variables / .env).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.stash[SETTINGS_KEY] = _load_settings_or_exit(config)
    _register_scenario_id_markers(config)


def _load_settings_or_exit(config: pytest.Config) -> Settings:
    """Fail fast with a readable message, before any browser or request is opened."""
    overrides: dict[str, object] = {}
    if env := config.getoption("--env"):
        overrides["env"] = env
    if cli_url := config.getoption("--base-url", default=None):  # from pytest-playwright
        overrides["base_url"] = cli_url
    try:
        return load_settings(**overrides)
    except ValidationError as exc:
        # include_input=False: never echo the received value (it could be a password).
        problems = "; ".join(
            f"{'.'.join(map(str, err['loc']))}: {err['msg']}"
            for err in exc.errors(include_input=False, include_url=False)
        )
        raise pytest.UsageError(
            f"Invalid test configuration -> {problems}. "
            "Copy .env.example to .env or set the environment variables."
        ) from None


def _register_scenario_id_markers(config: pytest.Config) -> None:
    """Register every @QA-<n> tag found in the feature files.

    Gherkin tags become pytest markers and --strict-markers rejects unregistered ones.
    IDs grow with every scenario, so they are discovered instead of listed in pytest.ini.
    """
    features_dir = Path(config.rootpath, config.getini("bdd_features_base_dir"))
    ids = {
        match
        for feature in features_dir.rglob("*.feature")
        for match in SCENARIO_ID_TAG.findall(feature.read_text(encoding="utf-8"))
    }
    for scenario_id in sorted(ids):
        config.addinivalue_line("markers", f"{scenario_id}: scenario ID")


def pytest_report_header(config: pytest.Config) -> str:
    settings = config.stash[SETTINGS_KEY]
    return f"environment: {settings.env} | app url: {settings.app_url}"


# Markers whose tests must never run against the public site, with the skip reason.
REMOTE_SKIPS: dict[str, str] = {
    # Safety guard: never write to the shared public deployment.
    "mutating": "mutating test: not run against the public site (ENV=remote)",
    # Capability guard: some checks need the local Docker SUT (e.g. container internals).
    "local_only": "local-only test: needs the local Docker SUT (ENV=remote)",
}


KNOWN_BUG_PREFIX = "bug_"


def _known_bugs(config: pytest.Config) -> dict[str, str]:
    """{marker name: description} for every registered "bug_*" marker in pytest.ini."""
    bugs = {}
    for line in config.getini("markers"):
        name, _, description = line.partition(":")
        if name.strip().startswith(KNOWN_BUG_PREFIX):
            bugs[name.strip()] = description.strip()
    return bugs


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Apply environment skips and known-bug expectations to the collected tests."""
    known_bugs = _known_bugs(config)
    is_remote = config.stash[SETTINGS_KEY].env == "remote"
    for item in items:
        # Known SUT bugs: expected to fail; strict, so a fixed bug (XPASS) fails the run
        # and forces removing the tag instead of leaving a stale expectation.
        for bug, description in known_bugs.items():
            if item.get_closest_marker(bug):
                item.add_marker(pytest.mark.xfail(reason=description, strict=True))
        # Environment guards: skip, with a clear reason, what must not run in remote.
        if is_remote:
            for marker_name, reason in REMOTE_SKIPS.items():
                if item.get_closest_marker(marker_name):
                    item.add_marker(pytest.mark.skip(reason=reason))
                    break


@pytest.fixture(scope="session")
def settings(pytestconfig: pytest.Config) -> Settings:
    return pytestconfig.stash[SETTINGS_KEY]


@pytest.fixture(scope="session")
def base_url(settings: Settings) -> str:
    """Overrides pytest-playwright's fixture so page.goto("/admin") uses our config."""
    return settings.app_url
