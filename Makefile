# Atalhos de conveniencia para macOS e Linux.
# No Windows (ou em qualquer SO), use diretamente: python scripts/dev.py <tarefa>
#
# Todos os alvos delegam ao runner cross-platform scripts/dev.py, que e a
# fonte unica de verdade das tarefas.

PY ?= python

.PHONY: help format format-check lint lint-fix typecheck test test-cov build build-exe sync-skills check-skills check-architecture check-docs generate-feature smoke-package validate

help:
	@$(PY) scripts/dev.py help

format:
	@$(PY) scripts/dev.py format

format-check:
	@$(PY) scripts/dev.py format-check

lint:
	@$(PY) scripts/dev.py lint

lint-fix:
	@$(PY) scripts/dev.py lint-fix

typecheck:
	@$(PY) scripts/dev.py typecheck

test:
	@$(PY) scripts/dev.py test

test-cov:
	@$(PY) scripts/dev.py test-cov

build:
	@$(PY) scripts/dev.py build

build-exe:
	@$(PY) scripts/dev.py build-exe

sync-skills:
	@$(PY) scripts/dev.py sync-skills

check-skills:
	@$(PY) scripts/dev.py check-skills

check-architecture:
	@$(PY) scripts/dev.py check-architecture

check-docs:
	@$(PY) scripts/dev.py check-docs

generate-feature:
	@$(PY) scripts/dev.py generate-feature $(ARGS)

smoke-package:
	@$(PY) scripts/dev.py smoke-package

validate:
	@$(PY) scripts/dev.py validate
