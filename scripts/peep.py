#!/usr/bin/env python
"""peep ("prudently examine every package") verifies that packages conform to a
trusted, locally stored hash and only then installs them::

    peep install -r requirements.txt

This makes your deployments verifiably repeatable without having to maintain a
local PyPI mirror or use a vendor lib. Just update the version numbers and
hashes in requirements.txt, and you're all set.

"""
from __future__ import print_function
from base64 import urlsafe_b64encode
from contextlib import contextmanager
from hashlib import sha256
from itertools import chain
from linecache import getline
from optparse import OptionParser
from os import listdir
from os.path import join, basename, splitext
import re
import shlex
from shutil import rmtree
from sys import argv, exit
from tempfile import mkdtemp
from urlparse import urlparse

from pkg_resources import require, VersionConflict, DistributionNotFound

# We don't admit our dependency on pip in setup.py, lest a naive user simply
# say `pip install peep.tar.gz` and thus pull down an untrusted copy of pip
# from PyPI. Instead, we make sure it's installed and new enough here and spit
# out an error message if not:
def activate(specifier):
    """Make a compatible version of pip importable. Raise a RuntimeError if we
    couldn't."""
    try:
        for distro in require(specifier):
            distro.activate()
    except (VersionConflict, DistributionNotFound):
        raise RuntimeError('The installed version of pip is too old; peep '
                           'requires ' + specifier)

activate('pip>=0.6.2')  # Before 0.6.2, the log module wasn't there, so some
                        # of our monkeypatching fails. It probably wouldn't be
                        # much work to support even earlier, though.

import pip
from pip.log import logger
from pip.req import parse_requirements


__version__ = 1, 2, 0


ITS_FINE_ITS_FINE = 0
SOMETHING_WENT_WRONG = 1
# "Traditional" for command-line errors according to optparse docs:
COMMAND_LINE_ERROR = 2

ARCHIVE_EXTENSIONS = ('.tar.bz2', '.tar.gz', '.tgz', '.tar', '.zip')

class PipException(Exception):
    """When I delegated to pip, it exited with an error."""

    def __init__(self, error_code):
        self.error_code = error_code


def encoded_hash(sha):
    """Return a short, 7-bit-safe representation of a hash.

    If you pass a sha256, this results in the hash algorithm that the Wheel
    format (PEP 427) uses, except here it's intended to be run across the
    downloaded archive before unpacking.

    """
    return urlsafe_b64encode(sha.digest()).decode('ascii').rstrip('=')


@contextmanager
def ephemeral_dir():
    dir = mkdtemp(prefix='peep-')
    try:
        yield dir
    finally:
        rmtree(dir)


def run_pip(initial_args):
    """Delegate to pip the given args (starting with the subcommand), and raise
    ``PipException`` if something goes wrong."""
    status_code = pip.main(initial_args=initial_args)

    # Clear out the registrations in the pip "logger" singleton. Otherwise,
    # loggers keep getting appended to it with every run. Pip assumes only one
    # command invocation will happen per interpreter lifetime.
    logger.consumers = []

    if status_code:
        raise PipException(status_code)


def pip_download(req, argv, temp_path):
    """Download a package, and return its filename.

    :arg req: The InstallRequirement which describes the package
    :arg argv: Arguments to be passed along to pip, starting after the
        subcommand
    :arg temp_path: The path to the directory to download to

    """
    # Get the original line out of the reqs file:
    line = getline(*requirements_path_and_line(req))

    # Remove any requirement file args.
    argv = (['install', '--no-deps', '--download', temp_path] +
            list(requirement_args(argv, want_other=True)) +  # other args
            shlex.split(line))  # ['nose==1.3.0']. split() removes trailing \n.

    # Remember what was in the dir so we can backtrack and tell what we've
    # downloaded (disgusting):
    old_contents = set(listdir(temp_path))

    # pip downloads the tarball into a second temp dir it creates, then it
    # copies it to our specified download dir, then it unpacks it into the
    # build dir in the venv (probably to read metadata out of it), then it
    # deletes that. Don't be afraid: the tarball we're hashing is the pristine
    # one downloaded from PyPI, not a fresh tarring of unpacked files.
    run_pip(argv)

    return (set(listdir(temp_path)) - old_contents).pop()


def pip_install_archives_from(temp_path):
    """pip install the archives from the ``temp_path`` dir, omitting
    dependencies."""
    # TODO: Make this preserve any pip options passed in, but strip off -r
    # options and other things that don't make sense at this point in the
    # process.
    for filename in listdir(temp_path):
        archive_path = join(temp_path, filename)
        run_pip(['install', '--no-deps', archive_path])


def hash_of_file(path):
    """Return the hash of a downloaded file."""
    with open(path, 'rb') as archive:
        sha = sha256()
        while True:
            data = archive.read(2 ** 20)
            if not data:
                break
            sha.update(data)
    return encoded_hash(sha)


def is_git_sha(text):
    """Returns True if this is probably a git sha"""
    # Handle both the full sha as well as the 7-character abbrviation
    if len(text) in (40, 7):
        try:
            int(text, 16)
            return True
        except ValueError:
            pass
    return False


def filename_from_url(url):
    parsed = urlparse(url)
    path = parsed.path
    return path.split('/')[-1]


def is_always_unsatisfied(req):
    """Returns whether this requirement is always unsatisfied

    This would happen in cases where we can't determine the version
    from the filename.

    """
    # If this is a github sha tarball, then it is always unsatisfied
    # because the url has a commit sha in it and not the version
    # number.
    url = req.url
    if url:
        filename = filename_from_url(url)
        if filename.endswith(ARCHIVE_EXTENSIONS):
            filename, ext = splitext(filename)
            if is_git_sha(filename):
                return True
    return False


def version_of_download(filename, package_name):
    """Deduce the version number of a downloaded package from its filename.

    :arg project_name: The ``unsafe_name`` of the requirement

    """
    def version_of_archive(filename, package_name):
        # Since we know the project_name, we can strip that off the left, strip
        # any archive extensions off the right, and take the rest as the
        # version.
        for ext in ARCHIVE_EXTENSIONS:
            if filename.endswith(ext):
                filename = filename[:-len(ext)]
                break
        # Handle github sha tarball downloads.
        if is_git_sha(filename):
            filename = package_name + '-' + filename
        if not filename.replace('_', '-').startswith(package_name):
            # TODO: Should we replace runs of [^a-zA-Z0-9.], not just _, with -?
            give_up(filename, package_name)
        return filename[len(package_name) + 1:]  # Strip off '-' before version.

    def version_of_wheel(filename, package_name):
        # For Wheel files (http://legacy.python.org/dev/peps/pep-0427/#file-
        # name-convention) we know the format bits are '-' separated.
        whl_package_name, version, _rest = filename.split('-', 2)
        # Do the alteration to package_name from PEP 427:
        our_package_name = re.sub(r'[^\w\d.]+', '_', package_name, re.UNICODE)
        if whl_package_name != our_package_name:
            give_up(filename, whl_package_name)
        return version

    def give_up(filename, package_name):
            raise RuntimeError("The archive '%s' didn't start with the package name '%s', so I couldn't figure out the version number. My bad; improve me." %
                               (filename, package_name))

    return (version_of_wheel if filename.endswith('.whl')
            else version_of_archive)(filename, package_name)


def requirement_args(argv, want_paths=False, want_other=False):
    """Return an iterable of filtered arguments.

    :arg want_paths: If True, the returned iterable includes the paths to any
        requirements files following a ``-r`` or ``--requirement`` option.
    :arg want_other: If True, the returned iterable includes the args that are
        not a requirement-file path or a ``-r`` or ``--requirement`` flag.

    """
    was_r = False
    for arg in argv:
        # Allow for requirements files named "-r", don't freak out if there's a
        # trailing "-r", etc.
        if was_r:
            if want_paths:
                yield arg
            was_r = False
        elif arg in ['-r', '--requirement']:
            was_r = True
        else:
            if want_other:
                yield arg


def requirements_path_and_line(req):
    """Return the path and line number of the file from which an
    InstallRequirement came."""
    path, line = (re.match(r'-r (.*) \(line (\d+)\)$',
                  req.comes_from).groups())
    return path, int(line)


def hashes_of_requirements(requirements):
    """Return a map of package names to lists of known-good hashes, given
    multiple requirements files."""
    def hashes_above(path, line_number):
        """Yield hashes from contiguous comment lines before line
        ``line_number``."""
        for line_number in range(line_number - 1, 0, -1):
            # If we hit a non-comment line, abort:
            line = getline(path, line_number)
            if not line.startswith('#'):
                break

            # If it's a hash line, add it to the pile:
            if line.startswith('# sha256: '):
                yield line.split(':', 1)[1].strip()

    expected_hashes = {}
    missing_hashes_req = []

    for req in requirements:  # InstallRequirements
        path, line_number = requirements_path_and_line(req)
        hashes = list(hashes_above(path, line_number))
        if hashes:
            hashes.reverse()  # because we read them backwards
            expected_hashes[req.name] = hashes
        else:
            missing_hashes_req.append(req)
    return expected_hashes, missing_hashes_req


def hash_mismatches(expected_hash_map, downloaded_hashes):
    """Yield the list of allowed hashes, package name, and download-hash of
    each package whose download-hash didn't match one allowed for it in the
    requirements file.

    If a package is missing from ``download_hashes``, ignore it; that means
    it's already installed and we're not risking anything.

    """
    for package_name, expected_hashes in expected_hash_map.items():
        try:
            hash_of_download = downloaded_hashes[package_name]
        except KeyError:
            pass
        else:
            if hash_of_download not in expected_hashes:
                yield expected_hashes, package_name, hash_of_download


def peep_hash(argv):
    """Return the peep hash of one or more files, returning a shell status code
    or raising a PipException.

    :arg argv: The commandline args, starting after the subcommand

    """
    parser = OptionParser(
        usage='usage: %prog hash file [file ...]',
        description='Print a peep hash line for one or more files: for '
                    'example, "# sha256: '
                    'oz42dZy6Gowxw8AelDtO4gRgTW_xPdooH484k7I5EOY".')
    _, paths = parser.parse_args(args=argv)
    if paths:
        for path in paths:
            print('# sha256:', hash_of_file(path))
        return ITS_FINE_ITS_FINE
    else:
        parser.print_usage()
        return COMMAND_LINE_ERROR


class EmptyOptions(object):
    """Fake optparse options for compatibility with pip<1.2

    pip<1.2 had a bug in parse_requirments() in which the ``options`` kwarg
    was required. We work around that by passing it a mock object.

    """
    default_vcs = None
    skip_requirements_regex = None


def peep_install(argv):
    """Perform the ``peep install`` subcommand, returning a shell status code
    or raising a PipException.

    :arg argv: The commandline args, starting after the subcommand

    """
    req_paths = list(requirement_args(argv, want_paths=True))
    if not req_paths:
        print("You have to specify one or more requirements files with the -r option, because")
        print("otherwise there's nowhere for peep to look up the hashes.")
        return COMMAND_LINE_ERROR

    # We're a "peep install" command, and we have some requirement paths.
    requirements = list(chain(*(parse_requirements(path,
                                                   options=EmptyOptions())
                                for path in req_paths)))
    downloaded_hashes, downloaded_versions, satisfied_reqs, malformed_reqs = {}, {}, [], []

    with ephemeral_dir() as temp_path:
        for req in requirements:
            if not req.req or not req.req.project_name:
                malformed_reqs.append('Unable to determine package name from URL %s; add #egg=' % req.url)
                continue

            req.check_if_exists()
            if req.satisfied_by and not is_always_unsatisfied(req):
                # This is already installed or we don't know the
                # version number from the requirement line, so we can
                # never know if this is satisfied.
                satisfied_reqs.append(req)
            else:
                name = req.req.project_name  # unsafe name
                archive_filename = pip_download(req, argv, temp_path)
                downloaded_hashes[name] = hash_of_file(join(temp_path, archive_filename))
                downloaded_versions[name] = version_of_download(archive_filename, name)

        expected_hashes, missing_hashes_reqs = hashes_of_requirements(requirements)
        mismatches = list(hash_mismatches(expected_hashes, downloaded_hashes))

        # Remove satisfied_reqs from missing_hashes, preserving order:
        satisfied_req_names = set(req.name for req in satisfied_reqs)
        missing_hashes_reqs = [req for req in missing_hashes_reqs if req.name not in satisfied_req_names]

        # Skip a line after pip's "Cleaning up..." so the important stuff
        # stands out:
        if mismatches or missing_hashes_reqs or malformed_reqs:
            print()

        # Mismatched hashes:
        if mismatches:
            print("THE FOLLOWING PACKAGES DIDN'T MATCH THE HASHES SPECIFIED IN THE REQUIREMENTS")
            print("FILE. If you have updated the package versions, update the hashes. If not,")
            print("freak out, because someone has tampered with the packages.\n")
        for expected_hashes, package_name, hash_of_download in mismatches:
            hash_of_download = downloaded_hashes[package_name]
            preamble = '    %s: expected%s' % (
                    package_name,
                    ' one of' if len(expected_hashes) > 1 else '')
            print(preamble, end=' ')
            print(('\n' + ' ' * (len(preamble) + 1)).join(expected_hashes))
            print(' ' * (len(preamble) - 4), 'got', hash_of_download)
        if mismatches:
            print()  # Skip a line before "Not proceeding..."

        # Missing hashes:
        if missing_hashes_reqs:
            print('The following packages had no hashes specified in the requirements file, which')
            print('leaves them open to tampering. Vet these packages to your satisfaction, then')
            print('add these "sha256" lines like so:\n')
        for req in missing_hashes_reqs:
            print('# sha256: %s' % downloaded_hashes[req.name])
            if req.url:
                line = req.url
                if req.name not in filename_from_url(req.url):
                    line = '%s#egg=%s' % (line, req.name)
            else:
                line = '%s==%s' % (req.name, downloaded_versions[req.name])
            print(line + '\n')

        if malformed_reqs:
            print('The following requirements could not be processed:')
            print('*', '\n* '.join(malformed_reqs))

        if mismatches or missing_hashes_reqs or malformed_reqs:
            print('-------------------------------')
            print('Not proceeding to installation.')
            return SOMETHING_WENT_WRONG
        else:
            pip_install_archives_from(temp_path)

            if satisfied_reqs:
                print("These packages were already installed, so we didn't need to download or build")
                print("them again. If you installed them with peep in the first place, you should be")
                print("safe. If not, uninstall them, then re-attempt your install with peep.")
                for req in satisfied_reqs:
                    print('   ', req.req)

    return ITS_FINE_ITS_FINE


def main():
    """Be the top-level entrypoint. Return a shell status code."""
    commands = {'hash': peep_hash,
                'install': peep_install}
    try:
        if len(argv) >= 2 and argv[1] in commands:
            return commands[argv[1]](argv[2:])
        else:
            # Fall through to top-level pip main() for everything else:
            return pip.main()
    except PipException as exc:
        return exc.error_code

if __name__ == '__main__':
    exit(main())
