#!/bin/bash
# pwd is the git repo.
set -e

# For XVFB Selenium tests.
export DISPLAY=:99.0

./scripts/mocha.sh

python manage.py test \
  --noinput --logging-clear-handlers \
  --no-skip \
  --with-nicedots
echo 'Booyahkasha!'
