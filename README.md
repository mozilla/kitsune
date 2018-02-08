# Kitsune


Kitsune is the platform that powers [SuMo
(support.mozilla.org)](https://support.mozilla.org)

It is a [Django](http://www.djangoproject.com/) application. There is
[documentation](https://kitsune.readthedocs.io/) online.

The *legacy* branch contains the codebase and deployment scripts for use
in the SCL3 datacenter. Only security fixes and changes to support
product launches are allowed to go in.

The *master* branch is where the active development of Kitsune happens
to modernize, containerize and bring to Kubernetes. Feature Pull
Requests are not allowed in unless related with the current effort to
move to Kubernetes.

You can access the staging site at <https://support.allizom.org/>

See [what's deployed](https://whatsdeployed.io/s-PRg)


## Development

To setup a local Kitsune development environment:

 #. Download base Kitsune docker images:

    docker pull mozmeao/kitsune:base-latest
    docker pull mozmeao/kitsune:base-dev-latest

 #. Build Kitsune docker images. (Optional. Needed when updating python packages)

    docker-compose -f docker-compose.yml -f docker/composefiles/build.yml build base
    docker-compose -f docker-compose.yml -f docker/composefiles/build.yml build dev

 #. Copy .env-dist to .env

    cp .env-dist .env

 #. Create your database

    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web ./manage.py migrate

 #. Install node and bower packages

    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web npm install
    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web ./node_modules/.bin/bower install --allow-root


To run Kitsune:

 #. docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml up web
