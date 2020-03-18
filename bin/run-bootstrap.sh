#!/bin/bash

set -ex

# install Node dependencies
npm run development && npm run production
# ensure the DB server is ready
urlwait
# run collectstatic
python manage.py collectstatic --noinput
# run DB migrations
python manage.py migrate
