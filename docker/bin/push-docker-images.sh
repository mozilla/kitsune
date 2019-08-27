#!/bin/bash
set -e

DOCKER_REPO=${DOCKER_REPO:-itsre/sumo-kitsune}
if [ -n "$GIT_SHA" ]; then
    GIT_SHA_SHORT=${GIT_SHA::7}
else
    GIT_SHA_SHORT="-latest"
fi

if ! ([ "$DOCKER_USERNAME" ] || [ -f ~/.docker/config.json ]);
then
    echo "No docker configuration, exiting."
    exit 0;
fi

if [ "$DOCKER_USERNAME" ];
then
    docker login -u "${DOCKER_USERNAME}" -p "${DOCKER_PASSWORD}"
fi

echo "git shas available"
printenv | grep -i git

for image in base base-dev staticfiles locales full-no-locales full;
do
	docker push ${image} ${DOCKER_REPO}:${image}-${GIT_SHA_SHORT}

    if [ $GIT_BRANCH == "master" ];
    then
	    docker push ${DOCKER_REPO}:${image}-latest
    fi
done
