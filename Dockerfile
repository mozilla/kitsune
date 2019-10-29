################################
# Node builder
#
FROM node:12 as node-builder
WORKDIR /app
COPY ./package.json ./package-lock.json ./
RUN npm i
COPY ./kitsune/sumo/static/sumo ./kitsune/sumo/static/sumo/
COPY ./kss-template ./kss-template/
COPY ./kss-config.json .
RUN npm run build

################################
# Python dependencies builder
#
FROM python:2-stretch AS base

WORKDIR /app
EXPOSE 8000

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"

RUN virtualenv /venv
RUN useradd -d /app -M --uid 1000 --shell /usr/sbin/nologin kitsune

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            gettext build-essential \
            libxml2-dev libxslt1-dev zlib1g-dev git \
            libjpeg-dev libffi-dev libssl-dev libxslt1.1 \
            libmariadbclient-dev mariadb-client && \
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

RUN apt-get update && apt-get install apt-transport-https optipng && \
    rm -rf /var/lib/apt/lists/*


################################
# Staticfiles builder
#
FROM base-dev AS staticfiles

COPY package.json bower.json /app/

RUN yarn install && yarn cache clean
RUN ./node_modules/.bin/bower install --allow-root

COPY . .

RUN cp .env-build .env && \
    ./manage.py nunjucks_precompile && \
    ./manage.py compilejsi18n && \
    ./manage.py collectstatic --noinput


################################
# Fetch locales
#
FROM python:2-stretch AS locales

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
FROM python:2-slim-stretch AS full-no-locales

WORKDIR /app

EXPOSE 8000

ENV PATH="/venv/bin:$PATH"
ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libmariadbclient18 optipng mariadb-client \
    libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 kitsune && useradd -g kitsune --uid 1000 --shell /usr/sbin/nologin kitsune

COPY --from=base --chown=kitsune:kitsune /venv /venv
COPY --from=node-builder --chown=kitsune:kitsune /app/static /app/static
COPY --from=staticfiles --chown=kitsune:kitsune /app/jsi18n /app/jsi18n
COPY --from=staticfiles --chown=kitsune:kitsune /app/bower_components /app/bower_components

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
