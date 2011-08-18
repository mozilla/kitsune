"""
Deployment for SUMO in production.

Requires commander (https://github.com/oremj/commander) which is installed on
the systems that need it.
"""

import os

from commander.deploy import task, hosts, hostgroups

SUMO_ROOT = "/data/sumo_python/src/prod"

@task
def update_code(ctx, tag):
    with ctx.lcd(SUMO_ROOT):
        ctx.local("git fetch -t")
        ctx.local("git checkout -f %s" % tag)
        ctx.local("git submodule sync")
        ctx.local("git submodule update --init --recursive")
        ctx.local("python2.6 manage.py compress_assets")


@task
def update_locales(ctx):
    with ctx.lcd(os.path.join(SUMO_ROOT, 'locale')):
        ctx.local("svn up")
        ctx.local("./compile-mo.sh .")


@task
def schematic(ctx):
    with ctx.lcd(SUMO_ROOT):
        ctx.local("python2.6 ./vendor/src/schematic/schematic migrations")


@task
def update_sumo(ctx, tag):
    """Do typical sumo update"""
    update_code(tag)
    update_locales()
    schematic()
