#!/bin/bash

set -ex

# Install and setup localization
./scripts/l10n-fetch-lint-compile.sh

# If flag --optipng-fix is passed
if [[ $* == *--optipng-fix* ]]; then
    # Install fix for optipng on mac silicon
    export CPPFLAGS=-DPNG_ARM_NEON_OPT=0
fi

# Collect the JavaScript catalog files.
python manage.py compilejsi18n

# Install Node dependencies, run the weback build, and pre-render the svelte templates.
npm run development && npm run webpack:build && npm run webpack:build:pre-render
# Run the DB migrations.
python manage.py migrate
