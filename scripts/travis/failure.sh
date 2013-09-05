#!/bin/bash
# pwd is the git repo.
set -e

echo "Failure!"

./irc "Travis FAILURE for build ${TRAVIS_REPO_SLUG}/${TRAVIS_BRANCH} #${TRAVIS_BUILD_NUMBER}."
