DC := $(shell command -v docker-compose 2> /dev/null)
ifeq (DC,)
DC = $(shell which docker-compose)
else
DC = $(shell which docker) compose
endif

default: help
	@echo ""
	@echo "You need to specify a subcommand."
	@exit 1

help:
	@echo "build         - build docker images for dev"
	@echo "start         - docker-compose up the entire system for dev"
	@echo ""
	@echo "init          - initialize the database and install Node packages"
	@echo "djshell       - start a Django Python shell (ipython)"
	@echo "dbshell       - start a PostgreSQL shell"
	@echo "shell         - start a bash shell"
	@echo "runshell      - start a bash shell with ports bound so you can run the server"
	@echo "clean         - remove all build, test, coverage and Python artifacts"
	@echo "rebuild       - force a rebuild of the dev docker image"
	@echo "format        - format source files"
	@echo "lint          - run pre-commit hooks"
	@echo "test          - run python tests"
	@echo "test-js       - run js tests"
	@echo "docs          - generate Sphinx HTML documentation"

.env:
	@echo "Copying .env-dist to .env...";
	cp -n .env-dist .env;

.docker-build: .env
	${MAKE} build

build:
	${DC} build web
	touch .docker-build

rebuild: clean build

start: .docker-build
	${DC} up web
run: start

init: .docker-build
	${DC} run web bin/run-bootstrap.sh

shell: .docker-build
	${DC} run web bash

runshell: .docker-build
	${DC} run --service-ports web bash

djshell: .docker-build
	${DC} run web python manage.py shell

dbshell: .docker-build
	${DC} run web python manage.py dbshell

clean:
#	python related things
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
#	test related things
	-rm -f .coverage
#	docs files
	-rm -rf docs/_build/
#	state files
	-rm -f .docker-build*
#	node stuff
	-rm -rf node_modules

lint: .docker-build
	${DC} run web pre-commit run --all-files

format: .docker-build
	${DC} run web black kitsune/

test: .docker-build
	${DC} run web ./bin/run-unit-tests.sh

test-js: .docker-build
	${DC} run web npm run webpack:test

docs: .docker-build
	${DC} run web $(MAKE) -C docs/ clean
	${DC} run web $(MAKE) -C docs/ html

.PHONY: build rebuild run init shell runshell djshell clean lint format test test-js docs
