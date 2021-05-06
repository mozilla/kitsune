#!/bin/bash
set -e

DOCKER_REPO=${DOCKER_REPO:-itsre/sumo-kitsune}

for image in base base-dev staticfiles locales full-no-locales full;
do
	docker pull ${DOCKER_REPO}:${image}-latest || true
done
