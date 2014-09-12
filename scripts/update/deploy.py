"""
Deployment for SUMO in production.

Requires commander (https://github.com/oremj/commander) which is installed on
the systems that need it.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hostgroups

import commander_settings as settings


# Setup virtualenv path.
venv_bin_path = os.path.join(settings.SRC_DIR, 'virtualenv', 'bin')
os.environ['PATH'] = venv_bin_path + os.pathsep + os.environ['PATH']
os.environ['DJANGO_SETTINGS_MODULE'] = 'kitsune.settings_local'


@task
def update_code(ctx, tag):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("git fetch")
        ctx.local("git checkout -f %s" % tag)
        ctx.local("git submodule sync")
        ctx.local("git submodule update --init --recursive")


@task
def update_locales(ctx):
    with ctx.lcd(os.path.join(settings.SRC_DIR, 'locale')):
        ctx.local("svn up")

    # Run the script that lints the .po files and compiles to .mo the
    # the ones that don't have egregious errors in them. This prints
    # stdout to the deploy log and also to media/postatus.txt so
    # others can see what happened.
    with ctx.lcd(settings.SRC_DIR):
        ctx.local('date > media/postatus.txt')
        ctx.local('./scripts/compile-linted-mo.sh | /usr/bin/tee -a media/postatus.txt')
        ctx.local('python manage.py compilejsi18n')


@task
def update_assets(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python manage.py nunjucks_precompile")
        ctx.local("python manage.py collectstatic --noinput")
        ctx.local("LANG=en_US.UTF-8 python manage.py compress_assets")


@task
def db_migrations(ctx):
    with ctx.lcd(settings.SRC_DIR):
        # This runs schematic and south migrations.
        ctx.local('schematic migrations')
        ctx.local('python manage.py migrate')


@task
def install_cron(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python ./scripts/crontab/gen-crons.py -k %s -u apache > /etc/cron.d/.%s" %
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


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def prime_app(ctx):
    ctx.remote("for i in {1..10}; do curl -so /dev/null -H 'Host: %s' -I http://localhost:81/ & sleep 1; done" % settings.REMOTE_HOSTNAME)


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
        ctx.local("git submodule status")
        print '\n\n\n\n\n' + os.environ['PATH'] + '\n\n\n\n\n'
        ctx.local("python manage.py migrate --list")
        with ctx.lcd("locale"):
            ctx.local("svn info")
            ctx.local("svn status")

        ctx.local("git rev-parse HEAD > media/revision.txt")


@task
def setup_dependencies(ctx):
    with ctx.lcd(settings.SRC_DIR):
        # Creating a virtualenv tries to open virtualenv/bin/python for
        # writing, but because virtualenv is using it, it fails.
        # So we delete it and let virtualenv create a new one.
        ctx.local('rm -f virtualenv/bin/python')
        ctx.local('virtualenv --no-site-packages virtualenv')

        # Activate virtualenv to append to path.
        activate_env = os.path.join(settings.SRC_DIR, 'virtualenv', 'bin', 'activate_this.py')
        execfile(activate_env, dict(__file__=activate_env))

        ctx.local('python scripts/peep.py install -r requirements/git.txt')
        ctx.local('python scripts/peep.py install -r requirements/pypi.txt')
        ctx.local('virtualenv --relocatable virtualenv')

        # Enable system site package lookup.
        ctx.local('rm -f virtualenv/lib/python2.6/no-global-site-packages.txt')

        # Re-activate virtualenv
        activate_env = os.path.join(settings.SRC_DIR, 'virtualenv', 'bin', 'activate_this.py')
        execfile(activate_env, dict(__file__=activate_env))



@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    update_code(ref)
    setup_dependencies()
    update_info()


@task
def update(ctx):
    update_assets()
    update_locales()
    db_migrations()


@task
def deploy(ctx):
    install_cron()
    checkin_changes()
    deploy_app()
    # Prime app adds more requests the the filling or full queue. Users
    # will see slow responses either way. It probably doesn't help much.
    # Skipping for now.
    # prime_app()
    update_celery()


@task
def update_sumo(ctx, tag):
    """Do typical sumo update"""
    pre_update(tag)
    update()
