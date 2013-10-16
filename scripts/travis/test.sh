#!/bin/bash
# pwd is the git repo.
set -e

# For XVFB Selenium tests.
export DISPLAY=:99.0

python manage.py test \
  --noinput --logging-clear-handlers \
  --with-fixture-bundling \
  --with-nicedots
echo 'Booyahkasha!'
