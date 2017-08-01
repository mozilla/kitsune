#!/bin/bash
# pwd is the git repo.
set -e

# None of this is needed for lint tests.
if [[ $TEST_SUITE == "lint" ]]; then
  exit 0
fi

# Exporting UID shell variable as environment variable.
# https://github.com/docker/compose/issues/2380
export UID

echo "building and starting docker container"
docker-compose up -d --build mariadb  # Build, init DB (can be slow)
docker-compose up -d --build

echo "Updating product details"
docker-compose exec web python manage.py update_product_details

echo "Doing static dance."
docker-compose exec web ./manage.py nunjucks_precompile
docker-compose exec web ./manage.py compilejsi18n
docker-compose exec web ./manage.py collectstatic --noinput > /dev/null
