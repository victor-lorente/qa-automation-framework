# Single entry point for humans and CI. Uses the project venv directly,
# so no `source .venv/bin/activate` is needed.

PYTHON  ?= python3
VENV    := .venv
BIN     := $(VENV)/bin
COMPOSE := docker compose -f docker/docker-compose.sut.yml

.PHONY: help install app-up app-down app-logs clean-reports test-local test-remote report

help:  ## List available targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-12s %s\n", $$1, $$2}'

install:  ## Create the venv, install pinned dependencies and Chromium
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --quiet --upgrade pip
	$(BIN)/pip install --quiet -r requirements.txt
	$(BIN)/playwright install --with-deps chromium

app-up:  ## Pull pinned RBP images and start them; waits until every service is healthy
	$(COMPOSE) pull --quiet
	$(COMPOSE) up -d --wait --wait-timeout 300

app-down:  ## Stop and remove the RBP containers
	$(COMPOSE) down --remove-orphans

app-logs:  ## Save container status and logs to reports/ (used by CI on failure)
	mkdir -p reports
	$(COMPOSE) ps -a > reports/sut-ps.txt
	$(COMPOSE) logs --no-color --timestamps > reports/sut-logs.txt

clean-reports:  ## Delete previous reports, so each run's output is self-contained
	rm -rf reports

test-local: clean-reports  ## Full suite against the local Docker SUT
	$(BIN)/pytest --env local

test-remote: clean-reports  ## Read-only suite against the public site (mutating tests are skipped)
	$(BIN)/pytest --env remote

report:  ## Open the last HTML report in the default browser
	$(BIN)/python -m webbrowser "file://$(CURDIR)/reports/report.html"
