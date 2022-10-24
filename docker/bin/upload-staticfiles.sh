#!/bin/bash

set -exo pipefail

GIT_COMMIT=${GIT_COMMIT:-latest}
GIT_COMMIT_SHORT=${GIT_COMMIT_SHORT:-$GIT_COMMIT}
CONTAINER_NAME="kitsune-static-${GIT_COMMIT}"
TMP_DIR="s3-static"
TMP_DIR_HASHED="s3-static-hashed"


function clean_tmp_dirs {
    rm -rf "${TMP_DIR}"
    rm -rf "${TMP_DIR_HASHED}"
}

function build_and_upload {
    # stage or prod
    target=$1

    clean_tmp_dirs

    # extract the static files
    docker create --name "${CONTAINER_NAME}" "mozilla/kitsune:${target}-${GIT_COMMIT_SHORT}"
    docker cp "${CONTAINER_NAME}:/app/static" "${TMP_DIR}"
    docker rm -f "${CONTAINER_NAME}"

    # separate the hashed files into another directory
    mkdir "${TMP_DIR_HASHED}"
    find ${TMP_DIR} -maxdepth 1 -type f -regextype sed -regex ".*\.[0-9a-f]\{16\}\..*" -exec mv -t ${TMP_DIR_HASHED} {} +

    # hashed filenames
    aws s3 sync \
        --only-show-errors \
        --acl public-read \
        --cache-control "max-age=315360000, public, immutable" \
        "./${TMP_DIR_HASHED}" "s3://mozit-sumo-${target}-media/static/"
    # non-hashed-filenames
    aws s3 sync \
        --only-show-errors \
        --acl public-read \
        --cache-control "max-age=21600, public" \
        "./${TMP_DIR}" "s3://mozit-sumo-${target}-media/static/"
}

build_and_upload stage
build_and_upload prod
clean_tmp_dirs
