from __future__ import absolute_import

import os
import sys
import re

default_source_file = os.path.join(
    os.path.dirname(__file__),
    '../amqp/channel.py',
)

RE_COMMENTS = re.compile(
    '(?P<methodsig>def\s+(?P<mname>[a-zA-Z0-9_]+)\(.*?\)'
    ':\n+\s+""")(?P<comment>.*?)(?=""")',
    re.MULTILINE | re.DOTALL
)

USAGE = """\
Usage: %s <comments-file> <output-file> [<source-file>]\
"""


def update_comments(comments_file, impl_file, result_file):
    text_file = open(impl_file, 'r')
    source = text_file.read()

    comments = get_comments(comments_file)
    for def_name, comment in comments.items():
        source = replace_comment_per_def(
            source, result_file, def_name, comment
        )

    new_file = open(result_file, 'w+')
    new_file.write(source)


def get_comments(filename):
    text_file = open(filename, 'r')
    whole_source = text_file.read()
    comments = {}

    all_matches = RE_COMMENTS.finditer(whole_source)
    for match in all_matches:
        comments[match.group('mname')] = match.group('comment')
        #print('method: %s \ncomment: %s' % (
        #       match.group('mname'), match.group('comment')))

    return comments


def replace_comment_per_def(source, result_file, def_name, new_comment):
    regex = ('(?P<methodsig>def\s+' +
             def_name +
             '\(.*?\):\n+\s+""".*?\n).*?(?=""")')
    #print('method and comment:' + def_name + new_comment)
    result = re.sub(regex, '\g<methodsig>' + new_comment, source, 0,
                    re.MULTILINE | re.DOTALL)
    return result


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if len(argv) < 3:
        print(USAGE % argv[0])
        return 1

    impl_file = default_source_file
    if len(argv) >= 4:
        impl_file = argv[3]

    update_comments(argv[1], impl_file, argv[2])

if __name__ == '__main__':
    sys.exit(main())
