#!/bin/bash
set -e

source docker/bin/set_git_env_vars.sh
DOCKER_REPO=${DOCKER_REPO:-mozmeao/kitsune}

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
	IMAGE_NAME="${DOCKER_REPO}:${image}-${GIT_COMMIT_SHORT}"
	IMAGE_NAME_LATEST="${DOCKER_REPO}:${image}-latest"
	docker tag "$IMAGE_NAME" "$IMAGE_NAME_LATEST"
    docker push "$IMAGE_NAME_LATEST"
done
