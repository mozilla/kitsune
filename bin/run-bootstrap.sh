#!/bin/bash

set -ex

# install Node dependencies
npm install
# ensure the DB server is ready
urlwait
# run collectstatic
#python manage.py collectstatic
# run DB migrations
python manage.py migrate
