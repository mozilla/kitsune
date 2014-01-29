#!/usr/bin/env python

"""

Goes through locale files and gives a breakdown of percentage
translated by app for each locale.

Requires:

* polib

For usage help, type::

   $ python l10n_completion.py --help

"""

from optparse import OptionParser
import json
import os
import site

# Add site path to pick up libs
SCRIPTS_DIR = os.path.dirname(__file__)
site.addsitedir(os.path.join(SCRIPTS_DIR, '..', 'vendor'))


import sys
import time

import polib


USAGE = 'usage: %prog [OPTIONS] OUTPUT-FILE LOCALES-DIR'


def get_language(fn):
    """Given a filename, returns the locale it applies to"""
    # FIXME - this expects the fn to be '.../XX/LC_MESSAGES/messages.po'
    return fn.split(os.sep)[-3]


def get_locale_files(localedir):
    """Given a locale dir, returns a list of all .po files in that tree"""
    po_files = []
    for root, dirs, files in os.walk(localedir):
        po_files.extend(
            [os.path.join(root, fn) for fn in files
             if fn.endswith('.po')])

    return po_files


def get_completion_data_for_file(fn):
    """Parses .po file and returns completion data for that .po file

    :returns: dict with keys total, translated and percent

    """
    app_to_translations = {}

    lang = get_language(fn)

    try:
        pofile = polib.pofile(fn)
    except IOError as ioe:
        print 'Error opening file: {fn}'.format(fn=fn)
        print ioe.message
        return 1

    for poentry in pofile:
        if poentry.obsolete:
            continue

        for occ in poentry.occurrences:
            path = occ[0].split(os.sep)
            if path[0] == 'kitsune':
                path = path[1]
            else:
                path = 'vendor/' + path[2]
            app_to_translations.setdefault(path, []).append(poentry.translated())

    data = {}
    for app, tr_list in app_to_translations.items():
        total = len(tr_list)
        translated = len([tr for tr in tr_list if tr])

        data[app] = {
            'total': total,
            'translated': translated,
            'percent': int((100.00 / float(total)) * float(translated))
        }
    return {lang: data}


def get_completion_data(locale_files):
    """Given a list of .po files, returns a dict of all completion data

    :returns: dict: locale -> completion data

    """
    data = {}

    for fn in locale_files:
        data.update(get_completion_data_for_file(fn))

    return data


def main(argv):
    parser = OptionParser(usage=USAGE)
    parser.add_option(
        '--truncate',
        action='store', type='int', dest='truncate', default=0)

    (options, args) = parser.parse_args(argv)

    if len(args) != 2:
        parser.error('Incorrect number of args.')
        return 1

    output_file = args[0]
    locales_dir = args[1]

    # Get list of locales dirs
    locale_files = get_locale_files(locales_dir)

    # Generate completion data
    data = [
        {
            'created': time.time(),
            'locales': get_completion_data(locale_files)
        }
    ]

    if os.path.exists(output_file):
        with open(output_file, 'rb') as fp:
            old_data = json.load(fp)

        old_data.append(data[0])
        data = old_data

    if options.truncate and len(data) > options.truncate:
        print 'Truncating ...'
        data = data[len(data) - options.truncate:]

    with open(output_file, 'wb') as fp:
        json.dump(data, fp)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
