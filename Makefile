DC_CI = "bin/dc.sh"
DC = $(shell which docker-compose)

default: help
	@echo ""
	@echo "You need to specify a subcommand."
	@exit 1

help:
	@echo "build         - build docker images for dev"
	@echo "run           - docker-compose up the entire system for dev"
	@echo ""
	@echo "pull          - pull the latest production images from Docker Hub"
	@echo "init          - initialize the database and install Node and Bower packages"
	@echo "djshell       - start a Django Python shell (ipython)"
	@echo "dbshell       - start a MySQL shell"
	@echo "shell         - start a bash shell"
	@echo "runshell      - start a bash shell with ports bound so you can run the server"
	@echo "clean         - remove all build, test, coverage and Python artifacts"
	@echo "rebuild       - force a rebuild of all of the docker images"
	@echo "lint          - check style with flake8, jshint, and stylelint"
	@echo "test          - run tests against local files"
	@echo "test-image    - run tests against files in docker image"
	@echo "docs          - generate Sphinx HTML documentation"
	@echo "build-ci      - build docker images for use in our CI pipeline"
	@echo "test-ci       - run tests against files in docker image built by CI"

.env:
	@if [ ! -f .env ]; then \
		echo "Copying .env-dist to .env..."; \
		cp .env-dist .env; \
	fi

.docker-build:
	${MAKE} build

.docker-build-pull:
	${MAKE} pull

.docker-build-full:
	${MAKE} build-full

build: .docker-build-pull
	${DC} build base-dev
	touch .docker-build

build-full: .docker-build-pull
	${DC} build full
#   tag other images
	${DC} build base base-dev staticfiles locales full-no-locales
	touch .docker-build-full

pull: .env
	-GIT_COMMIT_SHORT= ${DC} pull base base-dev staticfiles locales full-no-locales full mariadb elasticsearch redis
	touch .docker-build-pull

push-image: .env
	GIT_COMMIT_SHORT= ${DC} pull base base-dev staticfiles locales full-no-locales full mariadb elasticsearch redis
	# docker-compose automatically tags images it builds
	${DC} push itsre/sumo-kitsune-travis:${GIT_COMMIT_SHORT}

rebuild: clean build

run: .docker-build-pull
	${DC} up web

init: .docker-build-pull
	${DC} run web bin/run-bootstrap.sh

shell: .docker-build-pull
	${DC} run web bash

runshell: .docker-build-pull
	${DC} run --service-ports web bash

djshell: .docker-build-pull
	${DC} run web python manage.py shell

dbshell: .docker-build-pull
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
	-rm -rf node_modules bower_components

lint: .docker-build-pull
	${DC} run test flake8 kitsune

test: .docker-build-pull
	${DC} run test

test-js: .docker-build-pull
	${DC} run test-js

test-image: .docker-build-full
	${DC} run test-image

lint-image: .docker-build-full
	${DC} run test-image flake8 kitsune

lint-l10n: .env
	@GIT_COMMIT_SHORT= ${DC} pull base > /dev/null 2>&1
	@GIT_COMMIT_SHORT= ${DC} run lint-l10n

docs: .docker-build-pull
	${DC} run web $(MAKE) -C docs/ clean
	${DC} run web $(MAKE) -C docs/ html

###############
# For use in CI
###############
.docker-build-ci:
	${MAKE} build-ci

build-ci: .docker-build-pull
	${DC_CI} build full
#	tag intermediate images using cache
	${DC_CI} build base base-dev staticfiles locales full-no-locales
	touch .docker-build-ci

test-ci: .docker-build-ci
	${DC_CI} run test-image

test-js-ci: .docker-build-ci
	${DC_CI} run test-image-js

lint-ci: .docker-build-ci
	${DC_CI} run test-image flake8 kitsune

.PHONY: default clean build build-full pull docs init lint run djshell dbshell runshell shell test test-image lint-image lint-l10n rebuild build-ci test-ci test-js-ci lint-ci
