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

See [what's deployed](https://whatsdeployed.io/s-J18)


## Development

To setup a local Kitsune development environment:

 #. Fork this repository & clone it to your local machine.

 #. Download base Kitsune docker images:

    docker pull mozmeao/kitsune:base-latest
    docker pull mozmeao/kitsune:base-dev-latest

 #. Build Kitsune docker images. (Only needed on initial build or when packages change)

    docker-compose -f docker-compose.yml -f docker/composefiles/build.yml build base
    docker-compose -f docker-compose.yml -f docker/composefiles/build.yml build dev

 #. Copy .env-dist to .env

    cp .env-dist .env

 #. Create your database

    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web ./manage.py migrate

 #. Install node and bower packages

    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web npm install
    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web ./node_modules/.bin/bower install --allow-root

#. (Optional) Enable the admin control panel

    echo "ENABLE_ADMIN=True" >> .env

#. Run Kitsune

    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml up web

The running instance will be located at http://0.0.0.0:8000/ unless you specified otherwise, and the administrative control panel will be at http://0.0.0.0:8000/admin.

#. (Optional) Create a superuser

    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml exec web ./manage.py createsuperuser

#. (Optional) Create some data

    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml exec web ./manage.py generatedata

#. (Optional) Update product details

    docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml exec web ./manage.py update_product_details
