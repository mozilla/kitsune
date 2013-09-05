#!/bin/bash
# pwd is the git repo.
set -e

echo "Failure!"

./irc "Travis #${TRAVIS_BUILD_NUMBER} FAILURE"
