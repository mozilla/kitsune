#!/bin/bash

# Run this from the project root--not from this directory!

set -x

if [[ -d locale ]]; then
    cd locale
    git pull
    cd ..
else
    git clone https://github.com/mozilla-l10n/sumo-l10n.git locale
fi

docker-compose run lint-l10n > kitsune/sumo/static/postatus.txt

if [[ "$?" -eq 0 && "$1" == "--push" ]]; then
    cd locale
    git push git@github.com:mozmeao/sumo-l10n-prod.git
    cd ..
fi
