FROM quay.io/mozmar/base:latest
WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update
RUN apt-get update && apt-get install -y --no-install-recommends python2.7 libpython2.7 python-dev \
    python-pip gettext build-essential \
    libxml2-dev libxslt1-dev zlib1g-dev git\
    libjpeg-dev libffi-dev libssl-dev libxslt1.1\
    libmysqlclient-dev software-properties-common apt-transport-https

# Install mariadb-client 5.5
RUN apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 0xcbcb082a1bb943db
RUN add-apt-repository 'deb [arch=amd64,i386] http://sfo1.mirrors.digitalocean.com/mariadb/repo/5.5/debian wheezy main'
RUN apt-get update
RUN apt-get install -y --no-install-recommends  mariadb-client-5.5 libmariadbclient-dev

# Install nodejs older version 0.10.x
RUN curl -sL https://deb.nodesource.com/setup_0.10 | bash -
RUN apt-get install -y nodejs=0.10.48-1nodesource1~xenial1

# https://github.com/pypa/setuptools/issues/544
RUN pip install --upgrade setuptools
COPY ./requirements /app/requirements
COPY ./package.json /app/package.json
COPY ./bower.json /app/bower.json

RUN pip install -r requirements/default.txt --no-binary :all: --require-hashes
RUN pip install -r requirements/dev.txt --no-binary :all: --require-hashes

# Add a non root user and use it further
RUN groupadd --gid 1001 kitsune && useradd -g kitsune --uid 1001 --shell /usr/sbin/nologin kitsune
# Give permission to the created user to write in directory
RUN chown -R kitsune /app
# npm and bower tries to write in /home directory. So this permission is needed
RUN chown -R kitsune /home
USER kitsune

RUN npm install
RUN ./node_modules/.bin/bower install

ENV WEB_CONCURRENCY=4
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--timeout=120", "kuma.wsgi:application"]
ENV LANG=C.UTF-8
