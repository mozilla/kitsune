#!/bin/bash

set -exo pipefail

LOCALE_ENV="${LOCALE_ENV:-main}"

if [[ "$LOCALE_ENV" == "main" ]]; then
    LOCALE_URL="https://github.com/mozilla-l10n/sumo-l10n/archive/master.tar.gz"
elif [[ "$LOCALE_ENV" == "production" ]]; then
    LOCALE_URL="https://github.com/mozilla-it/sumo-l10n-prod/archive/master.tar.gz"
else
    echo "Unknown value for LOCALE_ENV: $LOCALE_ENV"
    exit 1
fi

mkdir locale && curl -s -L "$LOCALE_URL" | tar xz --strip-components=1 -C locale
