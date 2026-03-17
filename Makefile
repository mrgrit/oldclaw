# Makefile for OldClaw

.PHONY: install lint compile test test-unit test-contract test-integration test-e2e test-all run-manager run-master run-subagent

PYTHON ?= python3
DATABASE_URL ?= postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw
TEST_ENV = DATABASE_URL='$(DATABASE_URL)' PYTHONPATH=.

install:
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m compileall apps packages tools tests

test:
	$(MAKE) test-all

compile:
	$(PYTHON) -m compileall apps packages tools tests

test-unit:
	$(TEST_ENV) $(PYTHON) -m unittest discover -s tests/unit -p 'test_*.py' -v

test-contract:
	$(TEST_ENV) $(PYTHON) -m unittest discover -s tests/contract -p 'test_*.py' -v

test-integration:
	$(TEST_ENV) $(PYTHON) -m unittest discover -s tests/integration -p 'test_*.py' -v

test-e2e:
	$(TEST_ENV) $(PYTHON) -m unittest discover -s tests/e2e -p 'test_*.py' -v

test-all:
	$(TEST_ENV) $(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

run-manager:
	$(PYTHON) -m uvicorn --app-dir apps/manager-api/src main:app --reload

run-master:
	$(PYTHON) -m uvicorn --app-dir apps/master-service/src main:app --reload

run-subagent:
	$(PYTHON) -m uvicorn --app-dir apps/subagent-runtime/src main:app --reload
