#!/usr/bin/env python
import json
import logging
import subprocess
import sys
import textwrap
import xmlrpclib


USAGE = 'Usage: year_in_review.py [--json] <YEAR>'


# Note: Most of the bugzila api code comes from Scrumbugz.

cache = {}
log = logging.getLogger(__name__)
BZ_URL = 'http://bugzilla.mozilla.org/xmlrpc.cgi'
SESSION_COOKIES_CACHE_KEY = 'bugzilla-session-cookies'

PRODUCTS = [
    'support.mozilla.org'
]
BZ_RESOLUTIONS = [
    '',
    'FIXED',
    'INVALID',
    'WONTFIX',
    'DUPLICATE',
    'WORKSFORME',
    'INCOMPLETE',
    'SUPPORT',
    'EXPIRED',
    'MOVED'
]
BZ_FIELDS = [
    'id',
    'status',
    'resolution',
    'summary',
    'whiteboard',
    'assigned_to',
    'priority',
    'severity',
    'product',
    'component',
    'blocks',
    'depends_on',
    'creator',
    'creation_time',
    'last_change_time',
    'target_milestone',
]
UNWANTED_COMPONENT_FIELDS = [
    'sort_key',
    'is_active',
    'default_qa_contact',
    'default_assigned_to',
    'description'
]


class SessionTransport(xmlrpclib.SafeTransport):
    """
    XML-RPC HTTPS transport that stores auth cookies in the cache.
    """
    _session_cookies = None

    @property
    def session_cookies(self):
        if self._session_cookies is None:
            cookie = cache.get(SESSION_COOKIES_CACHE_KEY)
            if cookie:
                self._session_cookies = cookie
        return self._session_cookies

    def parse_response(self, response):
        cookies = self.get_cookies(response)
        if cookies:
            self._session_cookies = cookies
            cache.set(SESSION_COOKIES_CACHE_KEY,
                      self._session_cookies, 0)
            log.debug('Got cookie: %s', self._session_cookies)
        return xmlrpclib.Transport.parse_response(self, response)

    def send_host(self, connection, host):
        cookies = self.session_cookies
        if cookies:
            for cookie in cookies:
                connection.putheader('Cookie', cookie)
                log.debug('Sent cookie: %s', cookie)
        return xmlrpclib.Transport.send_host(self, connection, host)

    def get_cookies(self, response):
        cookie_headers = None
        if hasattr(response, 'msg'):
            cookies = response.msg.getheaders('set-cookie')
            if cookies:
                log.debug('Full cookies: %s', cookies)
                cookie_headers = [c.split(';', 1)[0] for c in cookies]
        return cookie_headers


class BugzillaAPI(xmlrpclib.ServerProxy):
    def get_bug_ids(self, **kwargs):
        """Return list of ids of bugs from a search."""
        kwargs.update({
            'include_fields': ['id'],
        })
        log.debug('Searching bugs with kwargs: %s', kwargs)
        bugs = self.Bug.search(kwargs)
        return [bug['id'] for bug in bugs.get('bugs', [])]

    def get_bugs(self, **kwargs):
        defaults = {
            'include_fields': BZ_FIELDS,
            }
        get_history = kwargs.pop('history', True)
        get_comments = kwargs.pop('comments', True)
        defaults.update(kwargs)
        if 'ids' in defaults:
            defaults['permissive'] = True
            log.debug('Getting bugs with kwargs: %s', defaults)
            bugs = self.Bug.get(defaults)
        else:
            log.debug('Searching bugs with kwargs: %s', defaults)
            bugs = self.Bug.search(defaults)

        bug_ids = [bug['id'] for bug in bugs.get('bugs', [])]

        if not bug_ids:
            return bugs

        # mix in history and comments
        history = comments = {}
        if get_history:
            history = self.get_history(bug_ids)
        if get_comments:
            comments = self.get_comments(bug_ids)
        for bug in bugs['bugs']:
            bug['history'] = history.get(bug['id'], [])
            bug['comments'] = comments.get(bug['id'], {}).get('comments', [])
            bug['comments_count'] = len(comments.get(bug['id'], {})
                                        .get('comments', []))
        return bugs

    def get_history(self, bug_ids):
        log.debug('Getting history for bugs: %s', bug_ids)
        try:
            history = self.Bug.history({'ids': bug_ids}).get('bugs')
        except xmlrpclib.Fault:
            log.exception('Problem getting history for bug ids: %s', bug_ids)
            return {}
        return dict((h['id'], h['history']) for h in history)

    def get_comments(self, bug_ids):
        log.debug('Getting comments for bugs: %s', bug_ids)
        try:
            comments = self.Bug.comments({
                'ids': bug_ids,
                'include_fields': ['id', 'creator', 'time', 'text'],
                }).get('bugs')
        except xmlrpclib.Fault:
            log.exception('Problem getting comments for bug ids: %s', bug_ids)
            return {}
        return dict((int(bid), cids) for bid, cids in comments.iteritems())


def wrap(text, indent='    '):
    text = text.split('\n\n')
    text = [textwrap.fill(part, expand_tabs=True, initial_indent=indent,
                          subsequent_indent=indent)
            for part in text]
    return '\n\n'.join(text)


def parse_whiteboard(whiteboard):
    bits = {
        'u': '',
        'c': '',
        'p': '',
        's': ''
        }

    for part in whiteboard.split(' '):
        part = part.split('=')
        if len(part) != 2:
            continue

        if part[0] in bits:
            bits[part[0]] = part[1]

    return bits


def bugzilla_stats(year):
    stats = []

    bugzilla = BugzillaAPI(
        BZ_URL,
        transport=SessionTransport(use_datetime=True),
        allow_none=True)

    # -------------------------------------------
    # Bugs created this year
    # -------------------------------------------
    bugs = bugzilla.get_bugs(
        product=PRODUCTS,
        creation_time='%s-01-01' % year,
        include_fields=['id', 'creator', 'creation_time'],
        history=False,
        comments=False)
    bugs = bugs['bugs']

    total = 0
    creators = {}
    for bug in bugs:
        # We can only get creation_time >= somedate, so we need to nix
        # the bugs that are after the year we're looking for.
        if bug['creation_time'].year != int(year):
            continue
        total += 1
        creators[bug['creator']] = creators.get(bug['creator'], 0) + 1

    creators = sorted(creators.items(), key=lambda item: item[1], reverse=True)

    stats.append(('Bugs created', {
        'total': total,
        'breakdown': [
            {'name': mem[0].split('@')[0], 'count': mem[1]}
            for mem in creators[:10]]
    }))

    # -------------------------------------------
    # Bugs resolved this year
    # -------------------------------------------
    bugs = bugzilla.get_bugs(
        product=PRODUCTS,
        last_change_time='%s-01-01' % year,
        include_fields=['id', 'summary', 'assigned_to', 'last_change_time', 'resolution'],
        status=['RESOLVED', 'VERIFIED', 'CLOSED'],
        history=True,
        comments=False)
    bugs = bugs['bugs']

    total = 0
    peeps = {}
    resolutions = {}

    traceback_bugs = []
    research_bugs = []
    tracker_bugs = []

    for bug in bugs:
        # We can only get last_change_time >= somedate, so we need to
        # nix the bugs that are after the year we're looking for.
        if bug['last_change_time'].year != int(year):
            continue

        if bug['summary'].lower().startswith('[traceback]'):
            traceback_bugs.append(bug)
        if bug['summary'].lower().startswith('[research]'):
            research_bugs.append(bug)
        if bug['summary'].lower().startswith('[tracker]'):
            tracker_bugs.append(bug)

        for hist in bug['history']:
            for change in hist['changes']:
                if not change['field_name'] == 'resolution':
                    continue
                # I think this history item comes from clearing the
                # resolution. i.e. reopening.
                if change['added'] == '':
                    continue

                total += 1

                # If the bug is marked FIXED, we assume that whoever
                # it was assigned to should get the "credit". If it
                # wasn't marked FIXED, then it's probably someone
                # doing triage and so whoever changed the resolution
                # should get "credit".
                if (change['added'] == 'FIXED'
                    and not 'nobody' in bug['assigned_to']):
                    person = bug['assigned_to']
                else:
                    person = hist['who']

                peeps_dict = peeps.setdefault(person, {})
                key = change['added']
                peeps_dict[key] = peeps_dict.get(key, 0) + 1

                resolutions[change['added']] = resolutions.get(
                    change['added'], 0) + 1

    peeps = sorted(peeps.items(), key=lambda item: sum(item[1].values()), reverse=True)
    stats.append(('Bugs resolved', {
        'total': total,
        'breakdown': [
            {'name': mem[0].split('@')[0],
             'total': sum(mem[1].values()),
             'breakdown': mem[1].items()}
            for mem in peeps[:10]
        ]
    }))

    # -------------------------------------------
    # Resolution stats
    # -------------------------------------------

    resolutions = sorted(resolutions.items(), key=lambda item: item[1])
    stats.append(('Bugs resolved breakdown', resolutions))

    # -------------------------------------------
    # Research bugs
    # -------------------------------------------

    stats.append(('Research bugs', [
        {'id': bug['id'], 'summary': bug['summary']}
        for bug in research_bugs
    ]))


    # -------------------------------------------
    # Trackers
    # -------------------------------------------

    stats.append(('Tracker bugs', [
        {'id': bug['id'], 'summary': bug['summary']}
        for bug in tracker_bugs
    ]))

    return stats


def git(*args):
    return subprocess.check_output(args)


def git_stats(year):
    stats = []

    # Get the shas for all the commits we're going to look at.
    all_commits = subprocess.check_output([
        'git', 'log',
        '--after=%s-01-01' % year,
        '--before=%s-01-01' % (int(year) + 1),
        '--format=%H'
    ])

    all_commits = all_commits.splitlines()

    # Person -> # commits
    committers = {}

    # Person -> (# files changed, # inserted, # deleted)
    changes = {}

    for commit in all_commits:
        author = git('git', 'log', '--format=%an',
                     '{0}~..{1}'.format(commit, commit))

        author = author.strip()
        # FIXME - this is lame. what's going on is that there are
        # merge commits which have multiple authors, so we just grab
        # the second one.
        if '\n' in author:
            author = author.splitlines()[1]

        committers[author] = committers.get(author, 0) + 1

        diff_data = git('git', 'diff', '--numstat', '--find-copies-harder',
                        '{0}~..{1}'.format(commit, commit))
        total_added = 0
        total_deleted = 0
        total_files = 0

        for line in diff_data.splitlines():
            added, deleted, fn = line.split('\t')
            if fn.startswith('vendor/'):
                continue
            if added != '-':
                total_added += int(added)
            if deleted != '-':
                total_deleted += int(deleted)
            total_files += 1

        old_changes = changes.get(author, (0, 0, 0))
        changes[author] = (
            old_changes[0] + total_added,
            old_changes[1] + total_deleted,
            old_changes[2] + total_files
        )

    print 'Total commits:', len(all_commits)
    print ''

    committers = sorted(
        committers.items(), key=lambda item: item[1], reverse=True)

    committers_data = []
    for person, count in committers:
        committers_data.append({
            'name': person,
            'data': {
                'commits': count,
                'added': changes[person][0],
                'deleted': changes[person][1],
                'files': changes[person][2]
            }
        })


    stats.append(('Git commit data', {
            'total commits': len(all_commits),
            'total lines added': sum([item[0] for item in changes.values()]),
            'total lines deleted': sum([item[1] for item in changes.values()]),
            'total files changed': sum([item[2] for item in changes.values()])
    }))

    stats.append(('Git committer data', committers_data))

    return stats


def main(argv):
    # XXX: This helps debug bugzilla xmlrpc bits.
    # logging.basicConfig(level=logging.DEBUG)

    do_json = False

    if not argv:
        print USAGE
        print 'Error: Must specify the year. e.g. 2012'
        return 1

    if '--json' in argv:
        print '>>> OMGWTFBBQ! You want it in JSON!'
        do_json = True
        argv.remove('--json')

    year = argv[0]

    output = []
    output.append(('Year', year))

    print '>>> Generating bugzilla stats....'
    output.extend(bugzilla_stats(year))

    print '>>> Generating git stats....'
    output.extend(git_stats(year))

    print ''

    if do_json:
        print json.dumps(output, indent=2)

    else:
        for mem in output:
            print ''
            print mem[0]
            print '=' * len(mem[0])
            print ''
            # FIXME - this is gross
            print json.dumps(mem[1], indent=2)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
