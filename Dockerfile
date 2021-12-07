#######################
# Common dependencies #
#######################
FROM python:3.9-bullseye AS base

WORKDIR /app
EXPOSE 8000

ARG PIP_DEFAULT_TIMEOUT=60
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"

RUN python -m venv /venv
RUN pip install --upgrade "pip==21.3.1"
RUN useradd -d /app -M --uid 1000 --shell /usr/sbin/nologin kitsune

RUN apt-get update && apt-get install apt-transport-https && \
    curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gettext build-essential \
    libxml2-dev libxslt1-dev zlib1g-dev git \
    libjpeg-dev libffi-dev libssl-dev libxslt1.1 \
    libmariadb3 mariadb-client \
    optipng nodejs zip && \
    rm -rf /var/lib/apt/lists/*

COPY ./requirements/*.txt /app/requirements/
RUN pip install --no-cache-dir --require-hashes -r requirements/default.txt


#####################
# Development image #
#####################
FROM base AS dev

RUN pip install --no-cache-dir --require-hashes -r requirements/dev.txt


#########################
# Frontend dependencies #
#########################
FROM base AS base-frontend

COPY package*.json .
COPY prepare_django_assets.js .
RUN npm run install-prod && npm run copy:protocol && npm run postinstall

COPY kitsune/sumo/static/sumo/scss kitsune/sumo/static/sumo/scss
RUN npm run build:scss && npm run build:postcss

COPY . .
RUN cp .env-build .env && \
    ./manage.py nunjucks_precompile


########################
# Testing dependencies #
########################
FROM base AS test-deps

RUN pip install --no-cache-dir --require-hashes -r requirements/test.txt


#################
# Testing image #
#################
FROM base-frontend AS test

COPY --from=test-deps /venv /venv

RUN cp .env-test .env && \
    ./manage.py compilejsi18n && \
    ./manage.py collectstatic --noinput


##########################
# Production dependences #
##########################
FROM base-frontend AS prod-deps

RUN ./scripts/l10n-fetch-lint-compile.sh && \
    find ./locale ! -name '*.mo' -type f -delete && \
    ./manage.py compilejsi18n && \
    # minify jsi18n files:
    find jsi18n/ -name "*.js" -exec sh -c 'npx uglifyjs "$1" -o "${1%.js}-min.js"' sh {} \; && \
    ./manage.py collectstatic --noinput && \
    npx svgo -r -f static


##########################
# Clean production image #
##########################
FROM python:3.9-slim-bullseye AS prod

WORKDIR /app

EXPOSE 8000

ENV PATH="/venv/bin:$PATH"
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN groupadd --gid 1000 kitsune && useradd -g kitsune --uid 1000 --shell /usr/sbin/nologin kitsune

COPY --from=prod-deps --chown=kitsune:kitsune /venv /venv
COPY --from=prod-deps --chown=kitsune:kitsune /app/locale /app/locale
COPY --from=prod-deps --chown=kitsune:kitsune /app/static /app/static

COPY --chown=kitsune:kitsune . .

# apt-get after copying everything to ensure we're always getting the latest packages in the prod image
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    libmariadb3 optipng mariadb-client \
    libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /app/media && chown kitsune:kitsune /app/media

USER kitsune

ARG GIT_SHA=head
ENV GIT_SHA ${GIT_SHA}
