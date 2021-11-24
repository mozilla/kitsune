#!/bin/bash
set -e

DOCKER_REPO=${DOCKER_REPO:-itsre/sumo-kitsune}
GIT_SHA=${GIT_SHA:-latest}

if ! ([ "$DOCKER_USERNAME" ] || [ -f ~/.docker/config.json ]);
then
    echo "No docker configuration, exiting."
    exit 0;
fi

if [ "$DOCKER_USERNAME" ];
then
    docker login -u "${DOCKER_USERNAME}" -p "${DOCKER_PASSWORD}"
fi

for image in base base-dev staticfiles locales full-no-locales full;
do
	docker push ${DOCKER_REPO}:${image}-${GIT_SHA}

    if [ $GIT_BRANCH == "main" ];
    then
	    docker push ${DOCKER_REPO}:${image}-latest
    fi
done
