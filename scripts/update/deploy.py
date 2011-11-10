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


@task
def update_code(ctx, tag):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("git fetch -t")
        ctx.local("git checkout -f %s" % tag)
        ctx.local("git submodule sync")
        ctx.local("git submodule update --init --recursive")
        ctx.local("python2.6 manage.py compress_assets")


@task
def update_locales(ctx):
    with ctx.lcd(os.path.join(settings.SRC_DIR, 'locale')):
        ctx.local("svn up")
        ctx.local("./compile-mo.sh .")


@task
def schematic(ctx):
    with ctx.lcd(settings.SRC_DIR):
        ctx.local("python2.6 ./vendor/src/schematic/schematic migrations")


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
    ctx.remote("/bin/touch %s" % settings.REMOTE_WSGI)


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
    update_locales()
    schematic()


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
