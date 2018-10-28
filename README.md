# Kitsune

Kitsune is the platform that powers [SuMo (support.mozilla.org)](https://support.mozilla.org)

It is a [Django](http://www.djangoproject.com/) application. There is a [documentation](https://kitsune.readthedocs.io/) online.

You can access the staging site at <https://support.allizom.org/>

See [what's deployed](https://whatsdeployed.io/s-J18)

## Development

To setup a local Kitsune development environment:

1. Fork this repository & clone it to your local machine.

1. Download base Kitsune docker images:
   ```
   docker pull mozmeao/kitsune:base-latest
   docker pull mozmeao/kitsune:base-dev-latest
   ```

1. Build Kitsune docker images. (Only needed on initial build or when packages change)
   ```
   docker-compose -f docker-compose.yml -f docker/composefiles/build.yml build base
   docker-compose -f docker-compose.yml -f docker/composefiles/build.yml build dev
   ```

1. Copy .env-dist to .env
   ```
   cp .env-dist .env
   ```

1. Create your database
   ```
   docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web ./manage.py migrate
   ```

1. Install node and bower packages
   ```
   docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web yarn
   docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml run web ./node_modules/.bin/bower install --allow-root
   ```

1. (Optional) Enable the admin control panel
   ```
   echo "ENABLE_ADMIN=True" >> .env
   ```

1. Run Kitsune
   ```
   docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml up web
   ```

   The running instance will be located at http://0.0.0.0:8000/ unless you specified otherwise, and the administrative control panel will be at http://0.0.0.0:8000/admin.

1. (Optional) Create a superuser
   ```
   docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml exec web ./manage.py createsuperuser
   ```

1. (Optional) Create some data
   ```
   docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml exec web ./manage.py generatedata
   ```

1. (Optional) Update product details
   ```
   docker-compose -f docker-compose.yml -f docker/composefiles/dev.yml exec web ./manage.py update_product_details
   ```

1. (Optional) Get search working

   First, make sure you have run the "Create some data" step above.

   1. Enter the web container: `docker exec -it kitsune_web_1 /bin/bash`
   2. Build the indicies: `./manage.py esreindex` (You may need to pass the `--delete` flag)
   3. Precompile the nunjucks templates: `./manage.py nunjucks_precompile`
