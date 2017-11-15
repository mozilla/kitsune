FROM python:2-stretch
WORKDIR /app

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN groupadd --gid 1000 kitsune && useradd -g kitsune --uid 1000 --shell /usr/sbin/nologin kitsune

RUN apt-get update && apt-get install apt-transport-https && \
    echo "deb https://deb.nodesource.com/node_0.10 jessie main" >> /etc/apt/sources.list && \
    curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
            gettext build-essential \
            libxml2-dev libxslt1-dev zlib1g-dev git \
            libjpeg-dev libffi-dev libssl-dev libxslt1.1 \
            libmariadbclient-dev mariadb-client optipng \
            nodejs=0.10.48-1nodesource1~jessie1 && \
    rm -rf /var/lib/apt/lists/*

COPY ./requirements /app/requirements

RUN pip install --no-cache-dir -r requirements/default.txt --require-hashes
RUN pip install --no-cache-dir -r requirements/dev.txt --require-hashes
RUN pip install --no-cache-dir -r requirements/test.txt --require-hashes

COPY ./package.json /app/package.json
COPY ./bower.json /app/bower.json

RUN npm install

RUN ./node_modules/.bin/bower install --allow-root
RUN chown -R kitsune /app
USER kitsune
