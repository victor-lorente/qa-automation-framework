# QA Automation Framework

Test automation framework built with **pytest**, **pytest-bdd** (Gherkin) and **Playwright for Python**,
covering API, UI and hybrid (API + UI) scenarios against a real multi-service web application.

> Status: **Phase 1 in progress**. Configuration, environment handling and the local test environment
> are in place; API clients, Page Objects and the first scenarios are being added.

## Highlights

- **BDD with Gherkin**: business-readable `.feature` files, each scenario tagged with a stable ID (`@QA-<n>`).
- **Layered architecture**: features → step definitions → Page Objects / API clients → config and fixtures.
- **Two environments**: a local Docker instance where everything runs, and the public deployment
  where only read-only tests run.
- **Safety guard**: tests tagged `@mutating` are skipped automatically against the public site.
- **Fail-fast configuration**: typed, validated settings (pydantic-settings); a wrong environment or
  missing credentials stops the run before any browser opens.
- **Reproducible test environment**: the application runs from published Docker images pinned by digest.

## Tech stack

| Area | Tool |
|------|------|
| Test runner | pytest |
| BDD | pytest-bdd |
| Browser and API automation | Playwright for Python (`APIRequestContext` for API) |
| Configuration | pydantic-settings + `.env` |
| Reporting | pytest-html |
| Test environment | Docker Compose |
| CI | GitHub Actions (planned) |

## System under test

[Restful Booker Platform](https://github.com/mwinteringham/restful-booker-platform) by
Mark Winteringham, licensed under **GPL-3.0**: a fake B&B website ("Shady Meadows B&B") made of six
Spring Boot services and a Next.js front end, built for practising testing.

- RBP is **not part of this repository**. [docker/docker-compose.sut.yml](docker/docker-compose.sut.yml)
  only references the images that RBP's own CI publishes to Docker Hub; the tests talk to it over HTTP.
- Pinned version: images published on 2026-11-26 from RBP commit
  [`2069ba1c`](https://github.com/mwinteringham/restful-booker-platform/commit/2069ba1c622c7327395d329eccdbe4e8ea90349f),
  referenced by digest (see the compose file).
- Public deployment (shared, used read-only): https://automationintesting.online

## Environments

| `ENV` | Target | What runs |
|-------|--------|-----------|
| `local` | RBP in Docker on your machine (`http://localhost`) | Everything, including tests that create, update or delete data |
| `remote` | https://automationintesting.online | Read-only tests only; `@mutating` tests are skipped with a clear reason |

## Getting started

### Prerequisites

- Python 3.13
- `make`
- For the local environment: a Docker Engine with Compose v2, e.g. Docker Desktop, OrbStack or Colima.
  On Windows, use WSL2.

### Setup

```bash
make install             # venv, pinned dependencies, Chromium
cp .env.example .env     # default values work for the local environment
```

### Run against the public site (no Docker needed)

```bash
make test-remote
```

### Run against a local instance

```bash
make app-up       # pulls the pinned images and waits until every service is healthy (~1 min first time)
make test-local
make app-down     # when you are done
```

### Report

```bash
make report       # opens reports/report.html
```

Run `make help` to list every target.

## Configuration

Settings are resolved in this order (highest first):

1. pytest options: `--env local|remote`, `--base-url <url>`
2. Environment variables (e.g. in CI)
3. `.env` file (see [.env.example](.env.example))
4. Defaults in [core/config.py](core/config.py)

Credentials are required and handled as secrets (masked in logs, redacted in the HTML report).

## Test selection

Every Gherkin tag is a pytest marker, and `--strict-markers` rejects unknown tags:

```bash
.venv/bin/pytest -m "api and not mutating"
.venv/bin/pytest -m "QA-12"
```

| Marker | Meaning |
|--------|---------|
| `api`, `ui`, `hybrid` | Layer under test |
| `infrastructure`, `login`, `validation` | Suite |
| `mutating` | Writes data; skipped when `ENV=remote` |
| `local_only` | Needs the local Docker instance; skipped when `ENV=remote` |
| `smoke`, `accessibility` | Optional subsets |
| `bug_<name>` | Known bug in the system under test: the scenario documents the expected behaviour and is reported as an expected failure (strict `xfail`, reason in `pytest.ini`). If the bug gets fixed, the run fails until the tag is removed |

## Project structure

```
├── conftest.py               # env selection, settings fixtures, mutating guard
├── core/
│   └── config.py             # typed settings (pydantic-settings)
├── docker/
│   └── docker-compose.sut.yml  # local test environment (pinned RBP images)
├── features/                 # Gherkin features (coming next)
├── tests/                    # step definitions (coming next)
├── Makefile
├── pytest.ini
└── requirements.txt
```

## Maintenance

### Updating the pinned RBP version

Resolve the digest of the current `latest` tag for each image and replace it in the compose file:

```bash
docker buildx imagetools inspect mwinteringham/restfulbookerplatform_auth:latest
```

Then run `make app-up` and the suite before opening a pull request.

### Alternative: build RBP from source

Use this if the published images stop being available or you need native arm64 images.
It needs several GB of free disk and takes several minutes:

```bash
git clone https://github.com/mwinteringham/restful-booker-platform.git .sut/restful-booker-platform
cd .sut/restful-booker-platform
git checkout 2069ba1c622c7327395d329eccdbe4e8ea90349f
docker run --rm -v "$PWD":/app -v "$HOME/.m2":/root/.m2 -w /app \
  maven:3.9-eclipse-temurin-26-alpine \
  mvn -q clean package -DskipTests -pl auth,booking,room,branding,report,message -am
docker compose up -d --build
```

`.sut/` is gitignored.
