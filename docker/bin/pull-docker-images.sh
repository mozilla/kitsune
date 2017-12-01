#!/bin/bash
set -e

DOCKER_REPO=${DOCKER_REPO:-mozmeao/kitsune}

for image in base staticfiles locales full-no-locales full;
do
	docker pull ${DOCKER_REPO}:${image}-latest || true
done
