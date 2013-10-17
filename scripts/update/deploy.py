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


@task
def update_assets(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python2.6 manage.py collectstatic --noinput")
        ctx.local("LANG=en_US.UTF-8 python2.6 manage.py compress_assets")


@task
def db_migrations(ctx):
    with ctx.lcd(settings.SRC_DIR):
        # This is a no-op after the final 232 migration. We should
        # remove this at some point once we think all environments and
        # contributors have updated.
        ctx.local("python2.6 ./vendor/src/schematic/schematic migrations")

        # This performs South migrations.
        ctx.local("python2.6 manage.py migrate")


@task
def install_cron(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python2.6 ./scripts/crontab/gen-crons.py -k %s -u apache > /etc/cron.d/.%s" %
                  (settings.WWW_DIR, settings.CRON_NAME))
        ctx.local("mv /etc/cron.d/.%s /etc/cron.d/%s" % (settings.CRON_NAME, settings.CRON_NAME))


@task
def checkin_changes(ctx):
    ctx.local(settings.DEPLOY_SCRIPT)


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def deploy_app(ctx):
    ctx.remote(settings.REMOTE_UPDATE_SCRIPT)
    ctx.remote('service httpd graceful')


@hostgroups(settings.WEB_HOSTGROUP, remote_kwargs={'ssh_key': settings.SSH_KEY})
def prime_app(ctx):
    for http_port in range(80, 82):
        ctx.remote("for i in {1..10}; do curl -so /dev/null -H 'Host: %s' -I http://localhost:%s/ & sleep 1; done" % (settings.REMOTE_HOSTNAME, http_port))


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
        # TODO: Nix this when we nix schematic.
        ctx.local("python2.6 ./vendor/src/schematic/schematic -v migrations/")
        ctx.local("python2.6 manage.py migrate --list")
        with ctx.lcd("locale"):
            ctx.local("svn info")
            ctx.local("svn status")

        ctx.local("git rev-parse HEAD > media/revision.txt")


@task
def pre_update(ctx, ref=settings.UPDATE_REF):
    update_code(ref)
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
    prime_app()
    update_celery()


@task
def update_sumo(ctx, tag):
    """Do typical sumo update"""
    pre_update(tag)
    update()
