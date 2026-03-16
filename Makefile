# Makefile for OldClaw

.PHONY: install lint test compile run-manager run-master run-subagent

PYTHON ?= python3

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m compileall apps packages tools

test:
	$(PYTHON) -m pytest -s -vv

compile:
	$(PYTHON) -m compileall apps packages tools

run-manager:
	$(PYTHON) -m uvicorn --app-dir apps/manager-api/src main:app --reload

run-master:
	$(PYTHON) -m uvicorn --app-dir apps/master-service/src main:app --reload

run-subagent:
	$(PYTHON) -m uvicorn --app-dir apps/subagent-runtime/src main:app --reload
