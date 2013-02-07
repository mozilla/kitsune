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
    parser.add_option("-p", "--python", default="/usr/bin/python2.6",
                      help="Python interpreter to use")

    (opts, args) = parser.parse_args()

    if not opts.kitsune:
        parser.error("-k must be defined")

    # To pick up the right PyOpenSSL:
    python_path = 'PYTHONPATH=/usr/local/lib64/python2.6/site-packages'

    ctx = {'django': 'cd %s; %s %s manage.py' % (
        opts.kitsune, python_path, opts.python),}
    ctx['cron'] = '%s cron' % ctx['django']

    if opts.user:
        for k, v in ctx.iteritems():
            ctx[k] = '%s %s' % (opts.user, v)

    # Needs to stay below the opts.user injection.
    ctx['python'] = opts.python

    print Template(TEMPLATE).render(**ctx)


if __name__ == "__main__":
    main()
