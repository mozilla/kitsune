# ===================================
# Stage 1: Common Python dependencies
# ===================================
FROM python:3.14-bookworm AS python-base

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
# Stage 2: Prepare gettext catalogs
# =================================
FROM python-base AS l10n-generator

COPY scripts/l10n-fetch-lint-compile.sh scripts/dennis_shim.py ./scripts/

# Git ADD keys the cache on the resolved commit, following the default branch unless pinned.
ARG L10N_REV
ADD --keep-git-dir=true https://github.com/mozilla-l10n/sumo-l10n.git#${L10N_REV} /app/locale
RUN mkdir -p kitsune/sumo/static && \
    ./scripts/l10n-fetch-lint-compile.sh && \
    rm -rf /app/locale/.git

# =================================
# Stage 3: Generate jsi18n files
# =================================
FROM python-base AS jsi18n-generator

COPY . .
RUN uv sync --frozen --extra dev

COPY --from=l10n-generator /app/locale /app/locale
COPY --from=l10n-generator /app/kitsune/sumo/static/postatus.txt /app/kitsune/sumo/static/postatus.txt

RUN cp .env-build .env && \
    ./manage.py compilejsi18n

# ==================================
# Stage 4: Frontend Builder (Node.js)
# ==================================
FROM node:22-bookworm AS frontend-builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
COPY --from=jsi18n-generator /app/jsi18n ./jsi18n

RUN cp .env-build .env && \
    npm run webpack:build:prod && \
    npm run webpack:build:pre-render

# =================================
# Stage 5: Development Image Target
# =================================
FROM python-base AS dev

# Copy source code and install the project itself
COPY . .
RUN uv sync --frozen --extra dev

# =============================
# Stage 6: Testing Image Target
# =============================
FROM python-base AS test

COPY --from=frontend-builder /app/dist /app/dist
COPY . .
RUN uv sync --frozen --extra dev

COPY --from=jsi18n-generator /app/locale /app/locale
COPY --from=jsi18n-generator /app/jsi18n /app/jsi18n
COPY --from=jsi18n-generator /app/kitsune/sumo/static/postatus.txt /app/kitsune/sumo/static/postatus.txt

RUN cp .env-test .env && \
    ./manage.py collectstatic --noinput

# ======================================
# Stage 7: Build Production Dependencies
# ======================================
FROM python-base AS prod-deps

COPY --from=frontend-builder /app/dist /app/dist
COPY . .

RUN rm -rf .venv && uv venv && uv sync --frozen --no-dev --extra prod --no-install-project

COPY --from=l10n-generator /app/locale /app/locale
COPY --from=l10n-generator /app/kitsune/sumo/static/postatus.txt /app/kitsune/sumo/static/postatus.txt

RUN cp .env-build .env && \
    ./manage.py compilejsi18n && \
    ./manage.py collectstatic --noinput

# =====================================
# Stage 8: Final Clean Production Image
# =====================================
FROM python:3.14-slim-bookworm AS prod

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
ENV GIT_SHA=${GIT_SHA}
