#!/bin/bash
# pwd is the git repo.
set -e

echo "Failure!"

./irc "Travis build #${TRAVIS_BUILD_NUMBER} FAILED."
