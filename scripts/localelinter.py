#!/usr/bin/env python

import itertools
import optparse
import os
import re
import sys

try:
    import polib  # from http://bitbucket.org/izi/polib
except ImportError:
    print 'You need to install polib.  Do:'
    print ''
    print '   pip install polib'
    sys.exit()


USAGE = 'usage: %prog [FILE|DIR]'


INTERP_RE = re.compile(
    r'('
    r'(?:%(?:[(]\S+?[)])?[#0+-]?[\.\d\*]*[hlL]?[diouxXeEfFgGcrs%])'
    r'|'
    r'(?:\{\S+?\})'
    r')')


def asciify(thing):
    if isinstance(thing, basestring):
        return thing.encode('ascii', 'replace')
    elif isinstance(thing, (list, tuple)):
        return [asciify(s) for s in thing]
    return repr(thing)


def extract_tokens(msg):
    try:
        tokens = [token for token in INTERP_RE.findall(msg)]
        tokens.sort()
        return tuple(tokens)
    except TypeError:
        print 'TYPEERROR', repr(msg)


def equal(id_tokens, str_tokens):
    if str_tokens is None:
        # This means they haven't translated the msgid, so there's
        # no entry. I'm pretty sure this only applies to plurals.
        return True

    id_tokens = list(id_tokens)
    str_tokens = list(str_tokens)

    for id_token, str_token in itertools.izip_longest(
        id_tokens, str_tokens, fillvalue=None):
        if id_token is None or str_token is None:
            return False
        if id_token != str_token:
            return False
    return True


def verify(msgid, id_text, id_tokens, str_text, str_tokens, index):
    # If the token lists aren't equal and there's a msgstr, then
    # that's a problem. If there's no msgstr, it means it hasn't been
    # translated.
    if not equal(id_tokens, str_tokens) and str_text.strip():
        print ('\nError for msgid: {msgid}\n'
               'tokens: {id_tokens} VS. {str_tokens}\n'
               '{key}: {id_text}\n'
               'msgstr{index}: {str_text}'.format(
                index='[{index}]'.format(index=index) if index is not None else '',
                key='id' if index in (None, '0') else 'plural',
                msgid=asciify(msgid),
                id_text=asciify(id_text),
                id_tokens=', '.join(asciify(id_tokens)),
                str_text=asciify(str_text),
                str_tokens=', '.join(asciify(str_tokens))))
        return False

    return True


def verify_file(fname):
    """Verifies file fname

    This prints to stdout errors it found in fname. It returns the
    number of errors.

    """
    if not fname.endswith('.po'):
        print '{fname} is not a .po file.'.format(fname=fname)
        return 1

    print 'Working on {fname}'.format(fname=fname)

    po = polib.pofile(fname)

    count = 0
    bad_count = 0

    for entry in po:
        if not entry.msgid_plural:
            if not entry.msgid and entry.msgstr:
                continue
            id_tokens = extract_tokens(entry.msgid)
            str_tokens = extract_tokens(entry.msgstr)

            if not verify(entry.msgid, entry.msgid, id_tokens, entry.msgstr,
                    str_tokens, None):
                bad_count += 1

        else:
            for key in sorted(entry.msgstr_plural.keys()):
                if key == '0':
                    # This is the 1 case.
                    text = entry.msgid
                else:
                    text = entry.msgid_plural
                id_tokens = extract_tokens(text)

                str_tokens = extract_tokens(entry.msgstr_plural[key])
                if not verify(entry.msgid, text, id_tokens,
                              entry.msgstr_plural[key], str_tokens, key):
                    bad_count += 1

        count += 1

    print ('\nVerified {count} messages in {fname}. '
           '{badcount} possible errors.'.format(
            count=count, fname=fname, badcount=bad_count))

    return bad_count


def verify_directory(dir):
    po_files = {}
    for root, dirs, files in os.walk(dir):
        for fn in files:
            if not fn.endswith('.po'):
                continue

            fn = os.path.join(root, fn)

            po_files[fn] = verify_file(fn)
            print '---'

    total_errors = sum(val for key, val in po_files.items())
    if total_errors == 0:
        return 0

    print 'Problem locale files:'
    po_files = sorted([(val, key) for key, val in po_files.items()],
                      reverse=True)
    for val, key in po_files:
        if val:
            print '{val:>5} {key}'.format(key=key, val=val)

    return 1


if __name__ == '__main__':
    parser = optparse.OptionParser(usage=USAGE)
    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(1)

    if os.path.isdir(args[0]):
        sys.exit(verify_directory(args[0]))

    # Return 0 if everything was fine or 1 if there were errors.
    sys.exit(verify_file(args[0]) != 0)
