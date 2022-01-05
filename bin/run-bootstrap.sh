#!/bin/bash

set -ex

# install Node dependencies
npm run development && python manage.py nunjucks_precompile && npm run webpack:build
# run DB migrations
python manage.py migrate
