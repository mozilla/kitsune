#!/bin/bash

set -exo pipefail

DOCKER_REPO=${DOCKER_REPO:-mozmeao/kitsune}
GIT_COMMIT=${GIT_COMMIT:-latest}
GIT_COMMIT_SHORT=${GIT_COMMIT_SHORT:-$GIT_COMMIT}
CONTAINER_NAME="kitsune-static-${GIT_COMMIT}"
IMAGE_NAME="${DOCKER_REPO}:full-${GIT_COMMIT_SHORT}"
TMP_DIR="s3-static"
TMP_DIR_HASHED="s3-static-hashed"

rm -rf "${TMP_DIR}"
rm -rf "${TMP_DIR_HASHED}"

# extract the static files
docker create --name "${CONTAINER_NAME}" "${IMAGE_NAME}"
docker cp "${CONTAINER_NAME}:/app/static" "${TMP_DIR}"
docker rm -f "${CONTAINER_NAME}"

# separate the hashed files into another directory
docker/bin/move_hashed_staticfiles.py "${TMP_DIR}" "${TMP_DIR_HASHED}"

for BUCKET in stage prod; do
    # hashed filenames
    aws s3 sync \
        --acl public-read \
        --cache-control "max-age=315360000, public, immutable" \
        --profile sumo-media \
        "./${TMP_DIR_HASHED}" "s3://sumo-${BUCKET}-media/static/"
    # non-hashed-filenames
    aws s3 sync \
        --acl public-read \
        --cache-control "max-age=21600, public" \
        --profile sumo-media \
        "./${TMP_DIR}" "s3://sumo-${BUCKET}-media/static/"
done

rm -rf "${TMP_DIR}"
rm -rf "${TMP_DIR_HASHED}"
