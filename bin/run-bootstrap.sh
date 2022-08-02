#!/bin/bash

set -ex

# Collect the JavaScript catalog files.
python manage.py compilejsi18n
# Install Node dependencies, run the weback build, and pre-render the svelte templates.
npm run development && npm run webpack:build && npm run webpack:build:pre-render
# Run the DB migrations.
python manage.py migrate
