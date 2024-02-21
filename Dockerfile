#######################
# Common dependencies #
#######################
FROM python:3.11.7-bookworm AS base

WORKDIR /app
EXPOSE 8000

ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    POETRY_VERSION=1.6.1 \
    PIP_VERSION=23.2.1

RUN useradd -d /app -M --uid 1000 --shell /bin/bash kitsune

RUN set -xe \
    && apt-get update && apt-get install apt-transport-https \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    gettext build-essential \
    libxml2-dev libxslt1-dev zlib1g-dev git \
    libjpeg-dev libffi-dev libssl-dev libxslt1.1 \
    optipng postgresql zip \
    # python
    && python -m venv /venv \
    && pip install --upgrade pip==${PIP_VERSION} \
    && pip install --upgrade poetry==${POETRY_VERSION} \
    && poetry config virtualenvs.create false \
    # clean up
    && rm -rf /var/lib/apt/lists/*

COPY ./scripts/install_nodejs.sh ./
COPY pyproject.toml poetry.lock ./
RUN ./install_nodejs.sh && rm ./install_nodejs.sh
RUN poetry install

#########################
# Frontend dependencies #
#########################
FROM base AS base-frontend

COPY package*.json ./
RUN npm run install-prod

COPY . .
RUN cp .env-build .env && \
    npm run webpack:build:prod


#################
# Testing image #
#################
FROM base-frontend AS test

RUN cp .env-test .env && \
    ./scripts/l10n-fetch-lint-compile.sh && \
    ./manage.py compilejsi18n && \
    npm run webpack:build:pre-render && \
    ./manage.py collectstatic --noinput


##########################
# Production dependences #
##########################
FROM base-frontend AS prod-deps

RUN ./scripts/l10n-fetch-lint-compile.sh && \
    find ./locale ! -name '*.mo' -type f -delete && \
    ./manage.py compilejsi18n && \
    # minify jsi18n files:
    find jsi18n/ -name "*.js" -exec sh -c 'npx terser "$1" -o "${1%.js}-min.js"' sh {} \; && \
    npm run webpack:build:pre-render && \
    ./manage.py collectstatic --noinput
RUN poetry install --no-dev


##########################
# Clean production image #
##########################
FROM python:3.11.7-slim-bookworm AS prod

WORKDIR /app

EXPOSE 8000

ENV PATH="/venv/bin:$PATH" \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 1000 kitsune && useradd -g kitsune --uid 1000 --shell /usr/sbin/nologin kitsune

COPY --from=prod-deps --chown=kitsune:kitsune /venv /venv
COPY --from=prod-deps --chown=kitsune:kitsune /app/locale /app/locale
COPY --from=prod-deps --chown=kitsune:kitsune /app/static /app/static
COPY --from=prod-deps --chown=kitsune:kitsune /app/dist /app/dist

COPY --chown=kitsune:kitsune . .

# apt-get after copying everything to ensure we're always getting the latest packages in the prod image
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    libxslt1.1 optipng postgresql && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /app/media && chown kitsune:kitsune /app/media

USER kitsune

ARG GIT_SHA=head
ENV GIT_SHA ${GIT_SHA}
