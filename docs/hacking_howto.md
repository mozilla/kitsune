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
2. Create a `.env` file (if one doesn't already exist).
    ```
    make .env
    ```
3. Pull base Kitsune Docker images, install node packages and build the Webpack bundle, and create your database.

    ```
    make init
    make build
    ```

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

Then you can run the Webpack build with instant reloading through browser-sync:

```
npm start
```

The running instance in this case will be located at http://localhost:3000/.

## Further setup

### Admin interface

After the above you can do some optional steps if you want to use the admin:

-   Enable the admin control panel

    ```
    echo "ENABLE_ADMIN=True" >> .env
    ```

-   Create a superuser

    ```
    docker-compose exec web ./manage.py createsuperuser
    ```

-   Create a profile for this user

    ```
    $ ./manage.py shell_plus
    In [1]: u = User.objects.get(username="superuser")
    In [2]: Profile(user=u).save()
    ```

-   Log in to the admin panel: http://localhost:8000/admin

### Enable development login

If you need to log in as a normal user,
add `ENABLE_DEV_LOGIN=True` to your `.env` file.

You can create a normal user like so:

```
docker-compose exec web ./manage.py shell_plus
In [1]: u = User(username="foobar")
In [2]: u.save()
In [3]: Profile(user=u).save()
```

You can then log in as that user by visiting: `http://localhost:8000/user/foobar/become`

### Install Sample Data

```eval_rst
We include some sample data to get you started. You can install it by
running this command::

    docker-compose exec web ./manage.py generatedata
```

### Get AAQ working

1.  Add a product with a slug matching one of the product values in `kitsune/questions/config.py`.
    You can do this through the admin interface at `/admin/products/product/add/`.

        For instance, with a `config.py` value like:

        ```python
        ...
        "name": _lazy("Firefox"),
        "product": "firefox",
        ...
        ```

        Create a product in the admin interface with its `slug` set to `firefox`.

2.  Add a topic matching a category from that product config,
    and associate it with the product you just created.
    You can do this through the admin interface at `/admin/products/topic/add/`.

        For instance, with a category with a `config.py` value like:

        ```python
        ...
        "topic": "download-and-install",
        ...
        ```

        Create a topic in the admin interface with its `slug` set to `download-and-install` and its product set to the product you just created.

3.  Finally add an AAQ locale for that product.
    You can do this through the admin interface at `/admin/questions/questionlocale/add/`.

### Get search working

First, make sure you have run the "Install Sample Data" step above,
or have entered data yourself through the admin interface.

1. Enter into the web container

    ```
    docker-compose exec web bash
    ```

2. Build the indicies

    ```
    $ ./manage.py es_init && ./manage.py es_reindex
    ```

3. Now, exit from web's bash shell
    ```
    $ exit
    ```

```eval_rst
.. Note::
  If after running these commands,
  search doesn't seem to be working,
  make sure you're not running any ad-blocking extensions in your browser.
  They may be blocking the `analytics.js` script which search depends on.
```

### Install linting tools

Kitsune uses [pre-commit](https://pre-commit.com) for linting.
Install it globally,
or in a venv,
outside of the docker container with:

```
$ pip install pre-commit
```

Then set up its git pre-commit hook:

```
$ pre-commit install
```

After this,
every time you commit,
pre-commit will check your changes for style problems.
To run it manually you can use the command:

```
$ pre-commit run
```

which will run the checks for only your changes,
or if you want to run the lint checks for all files:

```
$ pre-commit run --all-files
```

For more details see the [pre-commit docs](https://pre-commit.com).

### Product Details Initialization

```eval_rst
One of the packages Kitsune uses, ``product_details``, needs to fetch
JSON files containing historical Firefox version data and write them
within its package directory. To set this up, run this command to do
the initial fetch::

    docker-compose exec web ./manage.py update_product_details
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
