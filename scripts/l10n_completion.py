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


USAGE = 'usage: %prog [OPTIONS] LOCALES-DIR VERBOSE-OUTPUT-FILE SUMMARY-OUTPUT-FILE'


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
            app_to_translations.setdefault(
                path, []).append(poentry.translated())

    all_total = 0
    all_translated = 0

    data = {}
    for app, tr_list in app_to_translations.items():
        total = len(tr_list)
        translated = len([tr for tr in tr_list if tr])

        data[app] = {
            'total': total,
            'translated': translated,
        }

        all_total += total
        all_translated += translated

    return {
        lang: {
            'total': all_total,
            'translated': all_translated,
            'apps': data
        }
    }


def merge_trees(data, new_data):
    """Merges values from second tree into the first

    This takes care to add values of the same key where appropriate.

    """
    for key, val in new_data.items():
        if isinstance(val, dict):
            if key not in data:
                data[key] = new_data[key]
            else:
                merge_trees(data[key], new_data[key])

        else:
            if key not in data:
                data[key] = val
            else:
                data[key] = data[key] + val


def calculate_percents(data):
    """Traverses a tree and calculates percents at appropriate levels"""
    # calculate the percent for this node if appropriate
    if 'translated' in data and 'total' in data:
        total = float(data['total'])
        translated = float(data['translated'])
        data['percent'] = int((100.00 / total) * translated)

    # traverse the tree to calculate additional percents
    for key, val in data.items():
        if isinstance(val, dict):
            calculate_percents(val)


def get_completion_data(locale_files):
    """Given a list of .po files, returns a dict of all completion data

    :returns: dict: locale -> completion data

    """
    data = {}

    for fn in locale_files:
        new_data = get_completion_data_for_file(fn)
        merge_trees(data, new_data)

    calculate_percents(data)

    return data


def main(argv):
    parser = OptionParser(usage=USAGE)
    parser.add_option(
        '--truncate',
        action='store', type='int', dest='truncate', default=0)

    (options, args) = parser.parse_args(argv)

    if len(args) != 3:
        parser.error('Incorrect number of args.')
        return 1

    locales_dir = args[0]
    verbose_file = args[1]
    summary_file = args[2]

    # Get list of locales dirs
    locale_files = get_locale_files(locales_dir)

    # Generate completion data
    new_data = [
        {
            'created': time.time(),
            'locales': get_completion_data(locale_files)
        }
    ]
    data = new_data

    if os.path.exists(verbose_file):
        with open(verbose_file, 'rb') as fp:
            old_data = json.load(fp)

        old_data.append(new_data[0])
        data = old_data

    if options.truncate and len(data) > options.truncate:
        print 'Truncating ...'
        data = data[len(data) - options.truncate:]

    with open(verbose_file, 'wb') as fp:
        json.dump(data, fp)

    # Remove all the apps data for the summary file.
    for locale in new_data[0]['locales'].values():
        locale.pop('apps', None)

    # The summary file gets no historic data. Sorry.
    with open(summary_file, 'wb') as fp:
        json.dump(new_data[0], fp)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
