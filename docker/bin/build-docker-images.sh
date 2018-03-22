#!/bin/bash
set -e

DOCKER_REPO=${DOCKER_REPO:-mozmeao/kitsune}
GIT_SHA=${GIT_SHA:-auto}
LOCALE_ENV=${LOCALE_ENV:-master}

if [ $GIT_SHA == "auto" ];
then
   GIT_SHA_FULL=$(git rev-parse HEAD);
   GIT_SHA=${GIT_SHA_FULL:0:7};
fi

for image in base base-dev staticfiles locales full-no-locales full;
do
	docker build -t kitsune:${image}-latest \
                 -t ${DOCKER_REPO}:${image}-${GIT_SHA} \
                 -t ${DOCKER_REPO}:${image}-latest \
                 --cache-from ${DOCKER_REPO}:${image}-latest \
                 --cache-from kitsune:${image}-latest \
                 -f docker/dockerfiles/${image} \
                 --build-arg GIT_SHA=${GIT_SHA} \
                 --build-arg LOCALE_ENV=${LOCALE_ENV} .
done
