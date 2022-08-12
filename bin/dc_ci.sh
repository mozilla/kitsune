#!/bin/bash -e

source docker/bin/set_git_env_vars.sh
export DOCKER_BUILDKIT=1

docker-compose -f docker-compose.yml -f docker/docker-compose.ci.yml "$@"
