# =========================================
# Stage 1: Build Frontend Assets in Node.js
# =========================================
FROM node:22-bookworm AS frontend-builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN cp .env-build .env && \
    mkdir -p jsi18n/jsi18n && \
    npm run webpack:build:prod && \
    npm run webpack:build:pre-render && \
    npm run webpack:test

# ===================================
# Stage 2: Common Python dependencies
# ===================================
FROM python:3.11-bookworm AS python-base

WORKDIR /app
EXPOSE 8000

ENV LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"

RUN useradd -d /app -M --uid 1000 --shell /bin/bash kitsune

RUN set -xe \
    && apt-get update && apt-get install -y --no-install-recommends \
    gettext build-essential \
    libxml2-dev libxslt1-dev zlib1g-dev git \
    libjpeg-dev libffi-dev libssl-dev libxslt1.1 \
    optipng postgresql zip \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.7.20 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync --frozen --extra dev --no-install-project

# =================================
# Stage 3: Development Image Target
# =================================
FROM python-base AS dev

# Copy source code and install the project itself
COPY . .
RUN uv sync --frozen --extra dev

# =============================
# Stage 4: Testing Image Target
# =============================
FROM python-base AS test

COPY --from=frontend-builder /app/dist /app/dist
COPY . .
RUN uv sync --frozen --extra dev

RUN cp .env-test .env && \
    ./scripts/l10n-fetch-lint-compile.sh && \
    ./manage.py compilejsi18n && \
    ./manage.py collectstatic --noinput

# ======================================
# Stage 5: Build Production Dependencies
# ======================================
FROM python-base AS prod-deps

COPY --from=frontend-builder /app/dist /app/dist
COPY . .

RUN rm -rf .venv && uv venv && uv sync --frozen --no-dev --extra prod --no-install-project
RUN ./scripts/l10n-fetch-lint-compile.sh && \
    ./manage.py compilejsi18n && \
    ./manage.py collectstatic --noinput

# =====================================
# Stage 5: Final Clean Production Image
# =====================================
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

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    libxslt1.1 optipng postgresql && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /app/media && chown kitsune:kitsune /app/media

USER kitsune

ARG GIT_SHA=head
ENV GIT_SHA ${GIT_SHA}