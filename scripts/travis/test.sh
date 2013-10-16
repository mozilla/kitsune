#!/bin/bash
# pwd is the git repo.
set -e
date

# For XVFB Selenium tests.
export DISPLAY=:99.0

python manage.py test -v 2 \
  --noinput --logging-clear-handlers
  --with-xunit --with-fixture-bundling \
  --with-nicedots
echo 'Booyahkasha!'
