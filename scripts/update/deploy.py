"""
Deployment for SUMO in production.

Requires commander (https://github.com/oremj/commander) which is installed on
the systems that need it.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from commander.deploy import task, hosts, hostgroups

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
def update_sumo(ctx, tag):
    """Do typical sumo update"""
    update_code(tag)
    update_locales()
    schematic()
