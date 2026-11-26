# CLAUDE.md — QA Automation Framework (pytest + pytest-bdd + Playwright)

## Purpose of this project
Portfolio project for Víctor Lorente (QA Automation Engineer, GitHub: `victor-lorente`).
It reproduces the **architecture and way of working** he used in professional QA automation
frameworks, applied to a public practice application so it can be shown in job applications.

- **Never** include code, names, domains, data or internals from any employer or client
  project. Only the architectural approach is reused.
- The repository must be runnable by anyone who clones it (recruiters, interviewers),
  following only the README.

## How to work with the user
- Talk to the user in **Spanish**. Write code, comments, Gherkin, commit messages and the README in **English**.
- The user is learning and will defend this project in interviews: explain *why* each piece
  exists, briefly, when you add it.
- **The user chooses the UI locators himself** (Playwright codegen / Playwright CRX / inspector).
  Do not invent selectors for Page Objects. If a locator is missing, leave a clear `TODO`
  and ask the user for it.
- Prefer small, reviewable steps. After each step, tell the user how to run/verify it.
- Do not commit or push unless the user asks.

### Important decisions → offer a research prompt
When a task reaches an **important design decision** (e.g. folder structure, auth strategy
for API/UI, test data and cleanup approach, reporting tool, parallelisation, how to handle
environments, CI strategy, naming conventions, choosing between two libraries/patterns):
1. Stop before implementing it and explain the decision briefly: the options, their
   trade-offs and your initial recommendation.
2. **Ask the user whether he wants a research prompt** to run in Claude Desktop, which will do
   an in-depth web search on current QA conventions and best practices for that specific question.
3. If he says yes, write the prompt in a single copy-ready block, in **Spanish**, containing:
   - the context: this project (pytest + pytest-bdd + Playwright Python, POM, BDD/Gherkin,
     local Docker + read-only remote, GitHub Actions, portfolio for QA Automation roles);
   - the exact question to answer and the options being considered;
   - what to look for: official documentation (Playwright, pytest, pytest-bdd), recognised
     QA sources and recent (last 1–2 years) industry practice, with sources cited;
   - the expected output: a short recommendation, pros/cons per option, a minimal example,
     and anything that would matter in a job interview.
4. Wait for the user to bring back the findings before deciding and implementing.
Do not offer this for minor or obvious choices.

## System under test (SUT)
**Restful Booker Platform** (RBP), open source by Mark Winteringham:
https://github.com/mwinteringham/restful-booker-platform — a fake B&B site
("Shady Meadows B&B") made of Spring Boot services plus a Next.js front end.

Facts verified locally AND on the public site (26 Nov 2026, RBP commit `2069ba1c`,
"routing-improvements"; local and remote run the same version):
- Front end (Next.js, service `rbp-assets`) served on **http://localhost** (container port 3003
  mapped to host port 80).
- **`/api/<service>/...` is a generic proxy to the Spring Boot services' own REST API**
  (`booking`, `room`, `branding`, `auth`, `report`, `message`). The front end's internal
  handlers live under `/ui-api/...`: never test those, they are the UI's backend-for-frontend.
- Auth:
  - `POST /api/auth/login` `{"username","password"}` → **200, empty body,
    `Set-Cookie: token=<value>; Path=/`** (no HttpOnly). Invalid/unknown/empty credentials →
    **403, empty body**. No body → 400.
  - Protected routes read the **cookie `token`**. No session or invalid token → **403**.
  - `POST /api/auth/validate` `{"token"}` (JSON body, not cookie) → 200 empty / 403.
  - `POST /api/auth/logout` **invalidates the token** → never log out with the shared session.
- Rooms: `GET /api/room` → `{"rooms": [...]}`; `GET /api/room/{id}` → the room;
  `POST /api/room` → **201 with the full room, including `roomid`**; validation errors →
  400 `{"error":"BAD_REQUEST","errorCode":400,"fieldErrors":[...]}`; `DELETE /api/room/{id}` → 202.
  Room names may repeat. Price must be 1..999; type one of Single/Double/Twin/Family/Suite.
- Known bug (current version): `GET /api/room/{id}` of a deleted room → 500 instead of 404.
- Health: `/api/<service>/actuator/health` → `{"status":"UP",...}` for all six services, in
  both environments (also directly on ports 3000–3006 locally, no longer needed).
- History: up to `efe2deb` (Oct 2026), `/api` were front-end handlers with a different
  contract (token in the login body, 401s) and `/api/<svc>/{id}` routes returned 500.
- Admin credentials: `admin` / `password`.
- Public deployment: **https://automationintesting.online** (shared with other users). It
  follows RBP trunk, so it can change without notice: when remote tests break unexpectedly,
  compare with the latest RBP commit and Docker Hub images first.

## Environments
| Env | Target | What may run |
|-----|--------|--------------|
| `local` | RBP running in Docker on the user's machine | Everything: API, UI, hybrid, tests that create/modify/delete data |
| `remote` | https://automationintesting.online | **Read-only only**: page loads, navigation, visible content, admin login (successful and failed; it only opens a session, no business data changes), `GET` API calls. Never create entities. Never log out with a shared token. |

- Tests that create, update or delete data are marked **`@mutating`**.
- `conftest.py` must **skip `mutating` tests automatically when `ENV=remote`**, with a clear
  skip reason. This guard is a key design point: production is never written to by accident.
- `infrastructure` health checks go through `/api/<service>/actuator/health` and run in both
  environments (read-only), plus public `GET` checks (`/api/room`, `/api/branding`).

## Running the SUT locally (Docker)
Decision (Nov 2026, after research): **use the images RBP's own CI publishes to Docker Hub**
("build once, promote"), not a local build. Requirements: any Docker Engine with Compose v2
(Docker Desktop, OrbStack, Colima). Java/Maven are NOT installed on the host.

```bash
make app-up     # docker compose -f docker/docker-compose.sut.yml pull + up -d --wait
make app-down
make app-logs   # container status + logs into reports/ (CI on failure)
```
- `docker/docker-compose.sut.yml` is **our own deployment config** (images, ports,
  healthchecks); it contains no RBP code. Project name `rbp`.
- Images (`mwinteringham/restfulbookerplatform_<svc>`) are **pinned by digest**, never by tag:
  `latest` moves with every push to RBP trunk and version tags are rare. Current digests =
  `latest` published 2026-11-26 from RBP commit `2069ba1c622c7327395d329eccdbe4e8ea90349f`
  (previous pin: `efe2deb`, Oct 2026). Update them deliberately
  (`docker buildx imagetools inspect <image>:latest`) in a PR, re-verifying the API contract.
- Images are **linux/amd64 only** (`platform: linux/amd64` in compose): native in CI,
  emulated with Rosetta on the user's Apple Silicon Mac. Works fine (cold `make app-up` ≈ 64 s).
- **Service names `rbp-<svc>` are a contract**: the assets image has backend URLs baked in
  (`http://rbp-booking:3000`, …). Do not rename them.
- Readiness: healthchecks on each actuator (`wget` in the Temurin Alpine images, `node -e fetch`
  in the Node assets image, `127.0.0.1` because Next.js listens on IPv4 only),
  `depends_on: service_healthy` and `up --wait --wait-timeout 300`. No sleeps.
- Testcontainers was considered and rejected: the environment lifecycle stays outside pytest
  (remote suite does not need it; local runs reuse one running environment).
- **Fallback (documented in README):** build from source at the pinned commit in `.sut/`
  (gitignored) with Maven in a container + RBP's own `docker compose up --build`. Use only if the
  images disappear or native arm64 is needed. Needs several GB of disk.
- RBP is GPL-3.0: reference its images, never copy its code; credit it in the README.
- Disk is tight on the user's Mac (~7 GB free, Nov 2026); avoid steps that need several GB.

## Architecture
Layers (each layer only depends on the ones below it):
1. **Gherkin features** (`features/`) — business-readable scenarios.
2. **Step definitions** (`tests/`) — glue code; no locators, no raw HTTP details.
3. **Page Objects** (`core/page_objects/`) and **API clients** (`core/api_clients/`).
4. **Config / fixtures / utils** (`conftest.py`, `core/config.py`, `core/utils/`) — must not
   depend on UI/API/test layers.

Planned structure (create incrementally):
```
qa-automation-framework/
├── CLAUDE.md
├── README.md
├── Makefile
├── requirements.txt          # pinned versions (==)
├── pytest.ini                # markers, addopts, --strict-markers, bdd_features_base_dir
├── .env.example              # ENV, BASE_URL, ADMIN_USER, ADMIN_PASSWORD, service URLs
├── conftest.py               # global fixtures, env handling, mutating guard, failure screenshots
├── core/
│   ├── config.py             # loads .env, resolves URLs per environment
│   ├── api_clients/          # one client per service, built on Playwright APIRequestContext
│   ├── page_objects/         # one class per page/component (base_page.py + pages)
│   └── utils/                # test data builders, helpers
├── features/
│   ├── infrastructure/       # service health
│   ├── login/                # admin login success and failure cases
│   └── validation/           # rooms, bookings, messages: API, UI and hybrid
├── tests/
│   ├── test_infrastructure/
│   ├── test_login/
│   └── test_validation/      # one test_*.py per .feature, calling scenarios("…feature")
├── reports/                  # generated, gitignored
└── .github/workflows/        # CI
```

## Conventions
**Gherkin**
- One `.feature` per functionality; one matching `test_<name>.py` that calls `scenarios(...)`.
- Every scenario has a stable ID tag **`@QA-<n>`** plus layer/suite tags
  (e.g. `@api @validation @mutating @QA-12`). Register all tags as markers so
  `--strict-markers` does not fail (register `QA-n` tags dynamically in `conftest.py`).
- Write steps in business language ("Given the admin is logged in"), not UI mechanics.

**Markers** (declare in `pytest.ini`)
- Layer: `api`, `ui`, `hybrid`
- Suite: `infrastructure`, `login`, `validation`
- Environment safety: `mutating` (skipped in remote), `local_only` (needs the local Docker
  SUT; skipped in remote; currently unused, kept for Docker-dependent checks). Both handled by `REMOTE_SKIPS` in the
  root `conftest.py`. Never make a test pass silently in remote (no `if env` in steps).
- Known SUT bugs: one marker per bug, `bug_<short_name>`, registered in `pytest.ini` with its
  description. The root `conftest.py` turns them into `xfail(strict=True)` with that reason;
  a fixed bug XPASSes and fails the run, forcing the tag's removal. Always check an xfail fails
  for the right reason (`pytest --runxfail -m QA-n`).
- Optional: `smoke`, `accessibility`
- Combine with `-m`, e.g. `-m "api and not mutating"`.

**Playwright / Page Objects**
- Locators live only in Page Object classes, never in steps.
- Prefer user-facing locators (`get_by_role`, `get_by_label`, `get_by_text`); use
  `data-testid`/CSS only when there is no accessible alternative.
- Use web-first assertions (`expect(locator).to_be_visible()`, `to_have_url`, `to_have_text`).
  **No `time.sleep` / fixed waits.**
- Page Object methods express user intent (`login_as(user, pwd)`), not generic clicks.
- No `if`/`try` in tests to hide failures; assert the expected state.

**API**
- Use Playwright `APIRequestContext` (`playwright.request.new_context(base_url=...)`),
  session-scoped where read-only, disposed in fixture teardown.
- Authenticate once via `POST /api/auth/login` and send the token as cookie `token=<value>`.
- Reuse the same auth for the browser (storage state / cookie injection) so UI tests do not
  log in through the form unless the login itself is under test.
- On failure, include method, URL, status and response body in the assertion message/report.

**Test data and isolation**
- Each test creates the data it needs with unique names (e.g. timestamp/uuid suffix) and
  deletes it in fixture teardown (`yield` + cleanup), even if the test fails.
- Tests must be independent and runnable in any order and in parallel.
- Prefer API for setup/cleanup; use the UI only for what is under test.

## Tooling and commands (target)
`requirements.txt` (pin exact versions when creating it): pytest, pytest-bdd,
pytest-playwright, pytest-html, python-dotenv. Later: pytest-xdist, pytest-rerunfailures,
allure-pytest-bdd (never allure-pytest, see Reporting), axe-playwright-python.

Makefile targets to provide:
```
make install        # python -m venv .venv, pip install -r requirements.txt, playwright install --with-deps chromium
make app-up         # pull pinned RBP images, docker compose up -d --wait (see "Running the SUT locally")
make app-down       # docker compose down
make test-local     # ENV=local, full suite
make test-remote    # ENV=remote, read-only suite (mutating skipped)
make report         # open reports/report.html
```

## Reporting
Decision (Nov 2026, after research): **two reports, different purposes.**
- **pytest-html** → `reports/report.html`: quick report that works with Python only (anyone who
  clones the repo). Keep it as is; do not invest more time in it.
- **Allure Report 3 + `allure-pytest-bdd`** → the showcase report, published on GitHub Pages
  with history. **Introduce it in the same branch as the first CI workflow** (history is its
  main value and needs CI); the UI screenshot hook comes with the first Page Objects PR.
- Verified (Nov 2026): `allure-pytest-bdd==2.16.2` works with pytest-bdd 9 (steps, Scenario
  Outline parameters and tags shown; only attachment is the INFO request log, no secrets).
- **Never install `allure-pytest` too**: it conflicts with `allure-pytest-bdd` (`--alluredir`
  registered twice).
- Allure 3 CLI is a Node package (no Java): `package.json` with `allure` pinned via
  `--save-exact`, installed by `npm ci` in `make install`; `allurerc.mjs` with
  `historyPath: reports/history.jsonl`. Allure 3.33 needs **Node >= 22.18**: pin Node with an
  `.nvmrc` (user has nvm; v22.13.1 installed in Nov 2026 must be upgraded, e.g. `nvm install 24`).
- **No `@allure.*` tags in `.feature` files**: map existing markers (`api`/`ui`/`hybrid`,
  `@QA-n`) to Allure labels in `conftest.py` (`allure.dynamic`). Gherkin stays tool-agnostic.
- Environment widget: write only non-secret values (`ENV`, app URL) to
  `allure-results/environment.properties`.
- CI: publish **only the remote suite** to Pages (official Pages actions; restore
  `history.jsonl` from the published site before generating). Local suite reports go as job
  artifacts. Nightly scheduled remote run so history grows.
- **Never publish Playwright traces** (they contain network traffic, headers and bodies):
  artifacts only, short retention. Never attach the login response or raw bodies; use the
  redacting `describe()` from `core/utils/http_checks.py`.
- Rejected: ReportPortal (needs its own server with DB + search engine), Allure TestOps (paid),
  Allure 2 (needs Java, manual history copying).
- `make clean-reports` wipes `reports/` before `make test-local` / `test-remote`.
- Behave-style console output via pytest-bdd hooks — nice to have.
- `reports/` is gitignored.

## Version control (Git)
Branching model: **`main` + `develop` + short-lived work branches**.

| Branch | Purpose | Created from | Merges into |
|--------|---------|--------------|-------------|
| `main` | Stable, released code only. Tagged versions. | — | — |
| `develop` | Integration branch: latest finished work. | `main` | `main` (release PR) |
| `feature/<short-name>` | New functionality (e.g. `feature/rooms-api-client`) | `develop` | `develop` |
| `fix/<short-name>` | Bug fixes (e.g. `fix/mutating-guard`) | `develop` | `develop` |
| `test/<short-name>` | New or changed test scenarios only | `develop` | `develop` |
| `ci/<short-name>`, `docs/<short-name>`, `chore/<short-name>` | Pipeline, documentation, maintenance | `develop` | `develop` |

Flow:
1. Before starting a task: `git checkout develop && git pull` and create the work branch
   (`git checkout -b feature/<name>`).
2. Commit in small steps with **Conventional Commits**:
   `feat:`, `fix:`, `test:`, `refactor:`, `docs:`, `ci:`, `chore:`
   (e.g. `feat: add rooms API client`, `test: add admin login failure scenarios`).
3. Push the branch and open a **Pull Request into `develop`** with a short description
   (what and why, how to run it). CI must be green before merging.
4. When a phase/milestone is complete: open a **release PR `develop` → `main`**, merge it,
   and tag the merge commit on `main` with a semantic version (`v0.1.0` = end of phase 1,
   `v0.2.0` = phase 2, patch versions for fixes).
5. Delete work branches after merging.

Rules:
- Never commit directly to `main` or `develop`; both are protected in GitHub
  (PR required, CI status check required).
- One branch per task; keep PRs small and focused.
- Claude: at the start of each task, propose the branch name and create it from `develop`
  (if the user agrees); at the end, propose the commit message(s) and the PR description.
  Still **do not commit, push or open PRs unless the user asks**.

## CI (GitHub Actions)
- On every pull request to `develop` or `main`, and on push to `develop` and `main`:
  `make install` + `make test-remote` (read-only, no Docker needed). This is the status
  check required by branch protection.
- Optional job: start RBP with Docker inside the runner and run `make test-local`.
- Always upload `reports/` as an artifact (`if: always()`).

## Scope
**Phase 1 (base):** structure, config/env, `mutating` guard, API client, infrastructure +
login + one validation flow (API and one hybrid), Page Objects with user-chosen locators,
pytest-html, Makefile, README, GitHub Actions (remote) **+ Allure 3 published on GitHub Pages
(moved from phase 2; same branch as the CI workflow)**.
**Phase 2:** xdist, rerunfailures, accessibility (axe), local job in CI,
behave-style output, more validation scenarios (bookings, messages, report).
