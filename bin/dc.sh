#!/bin/bash -e

source docker/bin/set_git_env_vars.sh

docker-compose -f docker-compose.yml -f docker-compose.ci.yml "$@"
