#!/usr/bin/env python
import os
from optparse import OptionParser

from jinja2 import Template


TEMPLATE = open(os.path.join(os.path.dirname(__file__), 'crontab.tpl')).read()


def main():
    parser = OptionParser()
    parser.add_option("-k", "--kitsune",
                      help="Location of kitsune (required)")
    parser.add_option("-u", "--user",
                      help=("Prefix cron with this user. "
                           "Only define for cron.d style crontabs"))
    parser.add_option("-p", "--python", default="python",
                      help="Python interpreter to use")

    (opts, args) = parser.parse_args()

    if not opts.kitsune:
        parser.error("-k must be defined")

    ctx = {
        'django': 'cd %s; source virtualenv/bin/activate; %s -W ignore::DeprecationWarning manage.py' % (
            opts.kitsune, opts.python),
        'scripts': 'cd %s; source virtualenv/bin/activate; %s' % (
            opts.kitsune, opts.python),
    }
    ctx['cron'] = '%s cron' % ctx['django']
    # Source the venv, don't mess with manage.py
    ctx['rscripts'] = ctx['scripts']

    if opts.user:
        for k, v in ctx.iteritems():
            if k == 'rscripts':
                # rscripts get to run as whatever user is specified in crontab.tpl
                continue
            ctx[k] = '%s %s' % (opts.user, v)

    # Needs to stay below the opts.user injection.
    ctx['python'] = opts.python

    print Template(TEMPLATE).render(**ctx)


if __name__ == "__main__":
    main()
