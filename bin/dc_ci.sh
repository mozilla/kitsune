#!/bin/bash -e

source docker/bin/set_git_env_vars.sh
export DOCKER_BUILDKIT=1

docker-compose -f compose.yaml -f docker/compose.ci.yaml "$@"
