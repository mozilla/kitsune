#!/bin/bash

set -ex

# install Node dependencies
yarn
# install bower dependencies
./node_modules/.bin/bower install --allow-root
# ensure the DB server is ready
urlwait
# run collectstatic
python manage.py collectstatic --noinput
# run DB migrations
python manage.py migrate
