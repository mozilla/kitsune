#!/bin/bash -e

source docker/bin/set_git_env_vars.sh
export LOCALE_ENV=production

docker-compose "$@"
