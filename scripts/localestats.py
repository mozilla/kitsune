#!/usr/bin/env python

"""
Goes through the messages.pot file and gives a breakdown of
number of strings per app.

Requires:

* polib

Usage::

   $ python localestats.py <locales-dir>

"""

import os
import site

# Add site path to pick up other things
SCRIPTS_DIR = os.path.dirname(__file__)
site.addsitedir(os.path.join(SCRIPTS_DIR, '..', 'vendor'))


import sys
from collections import defaultdict

import polib


USAGE = 'usage: localestats.py <locales-dir>'


def main(argv):
    if not argv:
        print USAGE
        return 1

    fn = os.path.join(argv[0], 'templates', 'LC_MESSAGES', 'messages.pot')
    if not os.path.exists(fn):
        print USAGE
        return 1

    try:
        pofile = polib.pofile(fn)
    except IOError as ioe:
        print 'Error opening file: {fn}'.format(fn=fn)
        print ioe.message
        return 1

    app_string_count = defaultdict(int)
    for poentry in pofile.untranslated_entries():
        for occ in poentry.occurrences:
            path = occ[0]
            path = path.split(os.sep)
            if path[0] == 'kitsune':
                app_string_count[path[1]] += 1
            else:
                app_string_count['vendor/' + path[2]] += 1

    for key, val in sorted(app_string_count.items(), key=lambda item: item[1]):
        print '{0:22}: {1}'.format(key, val)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
