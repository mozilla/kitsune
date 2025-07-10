#######################
# Common dependencies #
#######################
FROM python:3.11-bookworm AS base

WORKDIR /app
EXPOSE 8000

ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"

RUN useradd -d /app -M --uid 1000 --shell /bin/bash kitsune

RUN set -xe \
    && apt-get update && apt-get install apt-transport-https \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    gettext build-essential \
    libxml2-dev libxslt1-dev zlib1g-dev git \
    libjpeg-dev libffi-dev libssl-dev libxslt1.1 \
    optipng postgresql zip \
    # clean up
    && rm -rf /var/lib/apt/lists/*

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.7.20 /uv /uvx /bin/

COPY ./scripts/install_nodejs.sh ./
COPY pyproject.toml uv.lock ./
RUN ./install_nodejs.sh && rm ./install_nodejs.sh
RUN uv venv && uv sync --frozen --extra dev --no-install-project

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

# Recreate virtual environment with only production dependencies and prod extra
RUN rm -rf .venv && uv venv && uv sync --frozen --no-dev --extra prod --no-install-project

RUN ./scripts/l10n-fetch-lint-compile.sh && \
    ./manage.py compilejsi18n && \
    npm run webpack:build:pre-render && \
    ./manage.py collectstatic --noinput

##########################
# Clean production image #
##########################
FROM python:3.11-slim-bookworm AS prod

WORKDIR /app

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv" \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 1000 kitsune && useradd -g kitsune --uid 1000 --shell /usr/sbin/nologin kitsune

COPY --chown=kitsune:kitsune . .
COPY --from=prod-deps --chown=kitsune:kitsune /app/.venv /app/.venv
COPY --from=prod-deps --chown=kitsune:kitsune /app/locale /app/locale
COPY --from=prod-deps --chown=kitsune:kitsune /app/static /app/static
COPY --from=prod-deps --chown=kitsune:kitsune /app/dist /app/dist

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
