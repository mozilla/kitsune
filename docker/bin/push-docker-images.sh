#!/bin/bash
# Push all generated docker images to dockerhub
set -e

DOCKER_REPO=${DOCKER_REPO:-itsre/sumo-kitsune-travis}
GIT_SHA=$(git rev-parse HEAD)
GIT_SHA_SHORT=${GIT_SHA::6}

if ! ([ "$DOCKER_USERNAME" ] || [ -f ~/.docker/config.json ]);
then
    echo "No docker configuration, exiting."
    exit 0;
fi

if [ "$DOCKER_USERNAME" ];
then
    docker login -u "${DOCKER_USERNAME}" -p "${DOCKER_PASSWORD}"
fi

for image in base base-dev staticfiles locales full-no-locales full; do
#    docker tag ${image}-${GIT_SHA_SHORT} $DOCKER_REPO/${image}-${GIT_SHA_SHORT}
	docker push ${DOCKER_REPO}:${image}-${GIT_SHA_SHORT}

    if [ "$(git branch --show-current)" == "master" ];
    then
	    docker push ${DOCKER_REPO}:${image}-latest
    fi
done
