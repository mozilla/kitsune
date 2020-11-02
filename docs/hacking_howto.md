# Development Setup

## Summary

```eval_rst
This chapter helps you get an installation of Kitsune up and running.

If you have any problems getting Kitsune running, let us know. See :ref:`contact-us-chapter`.
```

## Getting up and running

To get Kitsune running locally all you really need is to have [Docker](https://www.docker.com/products/docker-desktop) and [Docker Compose](https://docs.docker.com/compose/install/) installed,
and follow the following steps.

1. Fork this repository & clone it to your local machine.
   ```
   git clone https://github.com/mozilla/kitsune.git
   ```

2. Pull base Kitsune Docker images, run `collectstatic`, create your database, and install node packages.
   ```
   make init
   make build
   ```
  If you have low bandwidth, you may get a **timeout** error, see [issue#4511](https://github.com/mozilla/kitsune/issues/4511) for more information. You can change default pip's timeout value (which is 60 seconds) by running:

  ```
  make build PIP_TIMEOUT=300
  ```

  In above command, we are setting default value of [PIP_DEFAULT_TIMEOUT](https://pip.pypa.io/en/stable/user_guide/#environment-variables) to 5 minutes, change it according to your need.

3. Run Kitsune.
   ```
   make run
   ```
   This will produce a lot of output (mostly warnings at present). When you see the following the server will be ready:
   ```
   web_1              | Starting development server at http://0.0.0.0:8000/
   web_1              | Quit the server with CONTROL-C.
   ```

The running instance will be located at http://localhost:8000/ unless you specified otherwise,
and the administrative control panel will be at http://localhost:8000/admin/.

Another way you might choose to run the app (step 3 above) is by getting a shell in the container and then manually
running the Django dev server from there. This should make frequent restarts of the server a lot
faster and easier if you need to do that:

```
make runshell
bin/run-dev.sh
```

The end result of this method should be the same as using `make run`, but will potentially aid in debugging
and act much more like developing without Docker as you may be used to. You should use `make runshell` here
instead of `make shell` as the latter does not bind port 8000 which you need to be able to load the site.

Run `make help` to see other helpful commands.

Finally you can run the development server with instance reloading through
browser-sync.

```
npm start
```

The running instance in this case will be located at http://localhost:3000/.

## Admin interface

After the above you can do some optional steps if you want to use the admin:

* Enable the admin control panel
  ```
  echo "ENABLE_ADMIN=True" >> .env
  ```

* Create a superuser
  ```
  docker-compose exec web ./manage.py createsuperuser
  ```

* Create some data
  ```
  docker-compose exec web ./manage.py generatedata
  ```

* Update product details
  ```
  docker-compose exec web ./manage.py update_product_details
  ```

## Get search working

First, make sure you have run the "Create some data" step above.

1. Enter into the web container
    ```
    docker-compose exec web bash
    ```

2. Build the indicies
    ```
    $ ./manage.py esreindex
    ```
  (You may need to pass the `--delete` flag.)

3. Precompile the nunjucks templates
    ```
    $ ./manage.py nunjucks_precompile
    ```

4. Now, exit from web's bash shell
    ```
    $ exit
    ```

## Further setup

### Install Sample Data

```eval_rst
We include some sample data to get you started. You can install it by
running this command::

    docker-compose exec web ./manage.py generatedata
```

### Install linting tools

```eval_rst
Kitsune uses `Yelps Pre-commit <https://pre-commit.com/>`_ for linting. It is
installed as a part of the dev dependencies in ``requirements/dev.txt``. To
install it as a Git pre-commit hook, run it::

   $ venv/bin/pre-commit install

After this, every time you commit, Pre-commit will check your changes for style
problems. To run it manually, you can use the command::

   $ venv/bin/pre-commit run

which will run the checks for only your changes, or if you want to run the lint
checks for all files::

   $ venv/bin/pre-commit run --all-files

For more details see the `Pre-commit docs <https://pre-commit.com/>`_.
```

### Product Details Initialization

```eval_rst
One of the packages Kitsune uses, ``product_details``, needs to fetch
JSON files containing historical Firefox version data and write them
within its package directory. To set this up, run this command to do
the initial fetch::

    docker-compose exec web ./manage.py update_product_details
```

### Pre-compiling JavaScript Templates

```eval_rst
We use nunjucks to render Jinja-style templates for front-end use. These
templates get updated from time to time and you will need to pre-compile them
to ensure that they render correctly::

      docker-compose exec web ./manage.py nunjucks_precompile
```

### Using Django Debug Toolbar

[Django Debug Toolbar](https://github.com/jazzband/django-debug-toolbar)
provides some very useful information when debugging various things in Django,
especially slow running SQL queries.

To enable it, ensure `DEBUG` and `USE_DEBUG_TOOLBAR` are enabled in `.env`:

```
DEBUG=True
USE_DEBUG_TOOLBAR=True
```

If you are using it to debug slow running SQL queries,
you may want to disable the [MariaDB query cache](https://mariadb.com/kb/en/query-cache/).
Do that by adding the following lines under the `services.mariadb.entrypoint` key in `docker-compose.yml`:

```
- --query-cache-type=0
- --query-cache-size=0
```

And restart the database:

```
docker-compose restart mariadb
```

## Running the tests

Running the test suite is easy:
```
./bin/run-unit-tests.sh
```

```eval_rst
For more information, see the :ref:`test documentation
<tests-chapter>`.
```
