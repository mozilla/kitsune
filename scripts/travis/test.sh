#!/bin/bash
# pwd is the git repo.
set -e

echo 'Running Mocha tests'
docker-compose exec --user root web ./scripts/mocha.sh

echo 'Running django unit tests'
docker-compose exec web sh -c "REUSE_STATIC=1 ./manage.py test \
  --noinput --logging-clear-handlers \
  --no-skip \
  --with-nicedots"
echo 'Booyahkasha!'
