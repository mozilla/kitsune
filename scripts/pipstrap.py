#!/usr/bin/env python
"""A small script that can act as a trust root for installing pip 8

Embed this in your project, and your VCS checkout is all you have to trust. In
a post-peep era, this lets you claw your way to a hash-checking version of pip,
with which you can install the rest of your dependencies safely. All it assumes
is Python 2.7 or better and *some* version of pip already installed. If
anything goes wrong, it will exit with a non-zero status code.

"""
# This is here so embedded copies are MIT-compliant:
# Copyright (c) 2016 Erik Rose
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
from __future__ import print_function
from hashlib import sha256
from os.path import join
from pipes import quote
from shutil import rmtree
from subprocess import check_output
from sys import exit
from tempfile import mkdtemp
try:
    from urllib2 import build_opener, HTTPHandler, HTTPSHandler
except ImportError:
    from urllib.request import build_opener, HTTPHandler, HTTPSHandler
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse  # 3.4


PACKAGES = [
    # Pip has no dependencies, as it vendors everything:
    ('https://pypi.python.org/packages/source/p/pip/pip-8.0.2.tar.gz',
     '46f4bd0d8dfd51125a554568d646fe4200a3c2c6c36b9f2d06d2212148439521'),
    # This version of setuptools has only optional dependencies:
    ('https://pypi.python.org/packages/source/s/setuptools/'
     'setuptools-19.4.tar.gz',
     '214bf29933f47cf25e6faa569f710731728a07a19cae91ea64f826051f68a8cf'),
    # We require Python 2.7 or later because we don't support wheel's
    # conditional dep on argparse. This version of wheel has no other
    # dependencies:
    ('https://pypi.python.org/packages/source/w/wheel/wheel-0.26.0.tar.gz',
     'eaad353805c180a47545a256e6508835b65a8e830ba1093ed8162f19a50a530c')
]


class HashError(Exception):
    def __str__(self):
        url, path, actual, expected = self.args
        return ('{url} did not match the expected hash {expected}. Instead, '
                'it was {actual}. The file (left at {path}) may have been '
                'tampered with.'.format(**locals()))


def hashed_download(url, temp, digest):
    """Download ``url`` to ``temp``, make sure it has the SHA-256 ``digest``,
    and return its path."""
    # Based on pip 1.4.1's URLOpener but with cert verification removed
    def opener():
        opener = build_opener(HTTPSHandler())
        # Strip out HTTPHandler to prevent MITM spoof:
        for handler in opener.handlers:
            if isinstance(handler, HTTPHandler):
                opener.handlers.remove(handler)
        return opener

    def read_chunks(response, chunk_size):
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            yield chunk

    response = opener().open(url)
    path = join(temp, urlparse(url).path.split('/')[-1])
    actual_hash = sha256()
    with open(path, 'wb') as file:
        for chunk in read_chunks(response, 4096):
            file.write(chunk)
            actual_hash.update(chunk)

    actual_digest = actual_hash.hexdigest()
    if actual_digest != digest:
        raise HashError(url, path, actual_digest, digest)
    return path


def main():
    temp = mkdtemp(prefix='pipstrap-')
    try:
        downloads = [hashed_download(url, temp, digest)
                     for url, digest in PACKAGES]
        check_output('pip install --no-index --no-deps -U ' +
                     ' '.join(quote(d) for d in downloads),
                     shell=True)
    except HashError as exc:
        print(exc)
    except Exception:
        rmtree(temp)
        raise
    else:
        rmtree(temp)
        return 0
    return 1


if __name__ == '__main__':
    exit(main())
