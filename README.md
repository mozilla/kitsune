# Kitsune

Kitsune is the platform that powers [SuMo (support.mozilla.org)](https://support.mozilla.org)

It is a [Django](http://www.djangoproject.com/) application. There is
[documentation](https://kitsune.readthedocs.io/) online.

You can access the staging site at <https://support.allizom.org/>

See [what's deployed](https://whatsdeployed.io/s-J18)

## Code of Conduct
By participating in this project, you're agreeing to uphold the [Mozilla Community Participation Guidelines](https://www.mozilla.org/en-US/about/governance/policies/participation/). If you need to report a problem, please see our [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) guide.

## Development

To get Kitsune running locally all you really need is to have [Docker](https://www.docker.com/products/docker-desktop) and [Docker Compose](https://docs.docker.com/compose/install/) installed,
and follow the following steps.

1. Fork this repository & clone it to your local machine.
   ```
   git clone https://github.com/mozilla/kitsune.git
   ```

2. Pull base Kitsune Docker images, run `collectstatic`, create your database, and install node and bower packages.
   ```
   make init
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

### Compiling LESS files

By default, the `.less` files do not compile in local development because it impacts load times on OSX. If you are working on `.less` files, you can enable compilation with the following environment variable:

  ```
  echo "PIPELINE_COLLECTOR_ENABLED=True" >> .env
  ```

### The Admin

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

### Get Search Working

First, make sure you have run the "Create some data" step above.

1. Enter the web container: `docker-compose exec web bash`
2. Build the indicies: `./manage.py esreindex` (You may need to pass the `--delete` flag)
3. Precompile the nunjucks templates: `./manage.py nunjucks_precompile`
