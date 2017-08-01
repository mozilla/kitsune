#!/bin/bash
# pwd is the git repo.
set -e

# Installing dependencies for UI tests
if [[ $TEST_SUITE == "ui" ]]; then
  sudo pip install tox
fi

if [[ $TEST_SUITE == "lint" ]]; then
    sudo pip install -r requirements/dev.txt
fi

if [[ $TEST_SUITE == "docker" ]]; then
  sudo pip install docker-compose
fi
