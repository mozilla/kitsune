#!/bin/bash

set -ex

# install Node dependencies
npm run development && npm run webpack:build
# run DB migrations
python manage.py migrate
