"""
Deployment for SUMO in production.

Requires commander (https://github.com/oremj/commander) which is installed on
the systems that need it.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hostgroups  # noqa
import commander_settings as settings  # noqa


# Setup environment
venv_bin_path = os.path.join(settings.SRC_DIR, 'virtualenv', 'bin')
os.environ['PATH'] = venv_bin_path + os.pathsep + os.environ['PATH']
os.environ['DJANGO_SETTINGS_MODULE'] = 'kitsune.settings_local'
if 'HOME' not in os.environ:
    print 'Setting HOME to "{0}" (wtf?)'.format(settings.SRC_DIR)
    os.environ['HOME'] = settings.SRC_DIR


@task
def update_code(ctx, tag):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("git fetch")
        ctx.local("git checkout -f %s" % tag)
        ctx.local("find -name '*.pyc' -delete")


@task
def update_locales(ctx):
    with ctx.lcd(os.path.join(settings.SRC_DIR, 'locale')):
        ctx.local('git pull origin master')

    # Run the script that lints the .po files and compiles to .mo the
    # the ones that don't have egregious errors in them. This prints
    # stdout to the deploy log and also to media/postatus.txt so
    # others can see what happened.
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('date > media/postatus.txt')
        ctx.local('./scripts/compile-linted-mo.sh | /usr/bin/tee -a media/postatus.txt')
        ctx.local('python2.7 manage.py compilejsi18n')


@task
def update_assets(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("git clean -fxd -- static")
        ctx.local("python2.7 manage.py nunjucks_precompile")
        ctx.local("./node_modules/.bin/bower install --allow-root")
        ctx.local("python2.7 manage.py collectstatic --noinput")


@task
def db_migrations(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('python2.7 manage.py migrate --noinput actstream --fake')
        ctx.local('python2.7 manage.py migrate --noinput authority --fake')
        ctx.local('python2.7 manage.py migrate --noinput')


@task
def install_cron(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python2.7 ./scripts/crontab/gen-crons.py -k %s -u apache > /etc/cron.d/.%s" %
                  (settings.WWW_DIR, settings.CRON_NAME))
        ctx.local("mv /etc/cron.d/.%s /etc/cron.d/%s" % (settings.CRON_NAME, settings.CRON_NAME))


@task
def checkin_changes(ctx):
    # Touching the wsgi file forces the app to reload.
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('touch wsgi/kitsune.wsgi')

    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def deploy_app(ctx):
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)

    # Instead of restarting apache, we just touch the wsgi file in `checkin_changes()`
    # ctx.remote('service httpd graceful')


@hostgroups(settings.CELERY_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def update_celery(ctx):
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote('/sbin/service %s restart' % settings.CELERY_SERVICE)


@task
def update_info(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("date")
        ctx.local("git branch")
        ctx.local("git log -3")
        ctx.local("git status")
        ctx.local("python2.7 manage.py migrate --list")

        with ctx.lcd("locale"):
            ctx.local("git branch")
            ctx.local("git log -3")
            ctx.local("git status")

        ctx.local("git rev-parse HEAD > media/revision.txt")


@task
def setup_dependencies(ctx):
    with ctx.lcd(settings.SRC_DIR):
        # Creating a virtualenv tries to open virtualenv/bin/python for
        # writing, but because virtualenv is using it, it fails.
        # So we delete it and let virtualenv create a new one.
        ctx.local('rm -f virtualenv/bin/python virtualenv/bin/python2.7')
        ctx.local('virtualenv-2.7 --no-site-packages virtualenv')

        # Activate virtualenv to append to the correct path to $PATH.
        activate_env = os.path.join(settings.SRC_DIR, 'virtualenv', 'bin', 'activate_this.py')
        execfile(activate_env, dict(__file__=activate_env))

        ctx.local('pip --version')
        ctx.local('./peep.sh install -r requirements/default.txt')
        ctx.local('./peep.sh install -r requirements/server.txt')
        # Make the virtualenv relocatable
        ctx.local('virtualenv-2.7 --relocatable virtualenv')

        # Fix lib64 symlink to be relative instead of absolute.
        ctx.local('rm -f virtualenv/lib64')
        with ctx.lcd('virtualenv'):
            ctx.local('ln -s lib lib64')

        # Install Node dependencies
        ctx.local('npm install --production --unsafe-perm')


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    update_code(ref)
    setup_dependencies()
    update_info()


@task
def update(ctx):
    update_locales()
    update_assets()
    db_migrations()


@task
def deploy(ctx):
    install_cron()
    checkin_changes()
    deploy_app()
    update_celery()


@task
def update_sumo(ctx, tag):
    """Do typical sumo update"""
    pre_update(tag)
    update()
