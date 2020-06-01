################################
# Frontend dependencies builder
#
FROM node:12 AS frontend-base

WORKDIR /app
COPY ["./package.json", "./package-lock.json", "prepare_django_assets.js", "/app/"]
COPY ./kitsune/sumo/static/sumo /app/kitsune/sumo/static/sumo
RUN npm run production

################################
# Python dependencies builder
#
FROM python:3.8-buster AS base

WORKDIR /app
EXPOSE 8000

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"

RUN pip install --upgrade pip"==20.0.1"
RUN python -m venv /venv
RUN useradd -d /app -M --uid 1000 --shell /usr/sbin/nologin kitsune

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            gettext build-essential \
            libxml2-dev libxslt1-dev zlib1g-dev git \
            libjpeg-dev libffi-dev libssl-dev libxslt1.1 \
            libmariadb3 mariadb-client && \
    rm -rf /var/lib/apt/lists/*

COPY ./requirements/*.txt /app/requirements/

RUN pip install --no-cache-dir --require-hashes -r requirements/default.txt && \
    pip install --no-cache-dir --require-hashes -r requirements/dev.txt && \
    pip install --no-cache-dir --require-hashes -r requirements/test.txt

ARG GIT_SHA=head
ENV GIT_SHA=${GIT_SHA}


################################
# Developer image
#
FROM base AS base-dev
RUN apt-get update && apt-get install apt-transport-https && \
    curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get update && apt-get install -y --no-install-recommends optipng nodejs && \
    rm -rf /var/lib/apt/lists/*


################################
# Staticfiles builder
#
FROM base-dev AS staticfiles

COPY --from=frontend-base --chown=kitsune:kitsune /app/assets /app/assets
COPY --from=frontend-base --chown=kitsune:kitsune /app/node_modules /app/node_modules

COPY . .

RUN cp .env-build .env && \
    ./manage.py nunjucks_precompile && \
    ./manage.py compilejsi18n && \
    ./manage.py collectstatic --noinput && \
    npx svgo -r -f static


################################
# Fetch locales
#
FROM python:3.8-buster AS locales

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends  gettext

ENV PATH="/venv/bin:$PATH"

COPY --from=base /venv /venv

COPY . .

ARG LOCALE_ENV=master
ENV LOCALE_ENV=${LOCALE_ENV}
RUN ./docker/bin/fetch-l10n-files.sh
RUN ./scripts/compile-linted-mo.sh && \
    find ./locale ! -name '*.mo' -type f -delete

ARG GIT_SHA=head
ENV GIT_SHA ${GIT_SHA}


################################
# Full prod image sans locales
#
FROM python:3.8-slim-buster AS full-no-locales

WORKDIR /app

EXPOSE 8000

ENV PATH="/venv/bin:$PATH"
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libmariadb3 optipng mariadb-client \
    libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 kitsune && useradd -g kitsune --uid 1000 --shell /usr/sbin/nologin kitsune

COPY --from=base --chown=kitsune:kitsune /venv /venv
COPY --from=staticfiles --chown=kitsune:kitsune /app/static /app/static
COPY --from=staticfiles --chown=kitsune:kitsune /app/jsi18n /app/jsi18n

COPY --chown=kitsune:kitsune . .

RUN mkdir /app/media && chown kitsune:kitsune /app/media

USER kitsune

ARG GIT_SHA=head
ENV GIT_SHA ${GIT_SHA}


################################
# Full final prod image
#
FROM full-no-locales AS full

USER root
COPY --from=locales --chown=kitsune:kitsune /app/locale /app/locale
USER kitsune
