#!/bin/bash
# pwd is the git repo.
set -e


./scripts/mocha.sh

python manage.py test \
  --noinput --logging-clear-handlers \
  --no-skip \
  --with-nicedots
echo 'Booyahkasha!'
