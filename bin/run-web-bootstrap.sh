#!/bin/bash

set -ex

# Install and setup localization
./scripts/l10n-fetch-lint-compile.sh

# Collect the JavaScript catalog files.
python manage.py compilejsi18n

# Run the DB migrations.
python manage.py migrate