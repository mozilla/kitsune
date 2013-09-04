#!/bin/bash
# pwd is the git repo.
set -e

echo "Success!"

./irc "Travis #${TRAVIS_BUILD_NUMBER} SUCCESS"
