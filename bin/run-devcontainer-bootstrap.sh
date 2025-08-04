#!/bin/bash

set -ex

# Install and setup localization
./scripts/l10n-fetch-lint-compile.sh

# Collect the JavaScript catalog files.
python manage.py compilejsi18n

# For devcontainer, we need to install node dependencies and build frontend assets
# Since we're in the dev target, node should be available
npm run development && npm run webpack:build && npm run webpack:build:pre-render

# Run the DB migrations.
python manage.py migrate