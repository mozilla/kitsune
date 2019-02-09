#!/usr/bin/env python

from __future__ import print_function, unicode_literals

import json
import os
import sys
from textwrap import dedent


def get_hashed_filenames(static_path):
    json_file = '{}/staticfiles.json'.format(static_path)
    with open(json_file) as jsonf:
        staticfiles = json.load(jsonf)

    return staticfiles['paths'].values()


def move_hashed_files(static_path, hashed_path):
    filenames = get_hashed_filenames(static_path)
    moved_count = 0
    for filename in filenames:
        # some filenames in the file are in the form
        # fontawesome/fonts/fontawesome-webfont.f7c2b4b747b1.eot?v=4.3.0
        # we can skip these as they're duplicated
        if '?' in filename:
            continue

        src_fn = os.path.join(static_path, filename)
        dst_fn = os.path.join(hashed_path, filename)
        if not os.path.exists(os.path.dirname(dst_fn)):
            os.makedirs(os.path.dirname(dst_fn))

        os.rename(src_fn, dst_fn)
        moved_count += 1

    return moved_count


def main(static_path, hashed_path):
    moved = move_hashed_files(static_path, hashed_path)
    print('Successfully moved {} files'.format(moved))


if __name__ == '__main__':
    try:
        main(sys.argv[1], sys.argv[2])
    except IndexError:
        sys.exit(dedent("""\
            ERROR: source and destination directory arguments required.

            Usage: move_hashed_staticfiles.py <source_dir> <dest_dir>

            Moves hashed static files from source_dir to dest_dir based on the
            map of staticfiles in `source_dir/staticfiles.json`.
        """))
