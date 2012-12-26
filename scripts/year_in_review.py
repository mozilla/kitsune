#!/usr/bin/env python
import logging
import subprocess
import sys
import textwrap
import xmlrpclib


USAGE = 'Usage: year_in_review.py <YEAR>'
HEADER = 'year_in_review.py: find out what happened!'


# Note: Most of the bugzila api code comes from Scrumbugz.

cache = {}
log = logging.getLogger(__name__)
BZ_URL = 'http://bugzilla.mozilla.org/xmlrpc.cgi'
SESSION_COOKIES_CACHE_KEY = 'bugzilla-session-cookies'

BZ_RESOLUTIONS = ['', 'FIXED', 'INVALID', 'WONTFIX', 'DUPLICATE',
                  'WORKSFORME', 'INCOMPLETE', 'SUPPORT', 'EXPIRED',
                  'MOVED']
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


def print_bugzilla_stats(year):
    stats = {}

    bugzilla = BugzillaAPI(
        BZ_URL,
        transport=SessionTransport(use_datetime=True),
        allow_none=True)

    # created in year
    bugs = bugzilla.get_bugs(
        product=['support.mozilla.org'],
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

    stats['created'] = total
    creators = creators.items()
    creators.sort(key=lambda item: item[1])
    creators.reverse()
    stats['created_by'] = creators[:10]

    # resolved in year
    bugs = bugzilla.get_bugs(
        product=['support.mozilla.org'],
        last_change_time='%s-01-01' % year,
        include_fields=['id', 'creator', 'last_change_time', 'resolution'],
        status=['RESOLVED', 'VERIFIED', 'CLOSED'],
        history=True,
        comments=False)
    bugs = bugs['bugs']

    total = 0
    peeps = {}
    resolutions = {}

    for bug in bugs:
        # We can only get last_change_time >= somedate, so we need to
        # nix the bugs that are after the year we're looking for.
        if bug['last_change_time'].year != int(year):
            continue

        for hist in bug['history']:
            for change in hist['changes']:
                if not change['field_name'] == 'resolution':
                    continue
                # I think this history item comes from clearing the
                # resolution. i.e. reopening.
                if change['added'] == '':
                    continue

                total += 1
                peeps[hist['who']] = peeps.get(hist['who'], 0) + 1

                resolutions[change['added']] = resolutions.get(
                    change['added'], 0) + 1

    peeps = peeps.items()
    peeps.sort(key=lambda item: item[1])
    peeps.reverse()

    stats['resolved'] = total
    stats['resolved_people'] = peeps[:10]

    resolutions = resolutions.items()
    resolutions.sort(key=lambda item: item[1])
    stats['resolved_resolutions'] = resolutions

    print 'Bugs created:', stats['created']
    print ''
    for mem in stats['created_by']:
        print '  %30s : %s' % (mem[0], mem[1])

    print ''
    print 'Bugs resolved:', stats['resolved']
    print ''
    for mem in stats['resolved_people']:
        print '  %30s : %s' % (mem[0], mem[1])

    print ''
    for mem in stats['resolved_resolutions']:
        print '  %30s : %s' % (mem[0], mem[1])


def print_git_stats(year):
    stats = {}
    commits = subprocess.check_output(
        ['git', 'log',
         '--after=%s-01-01' % year,
         '--before=%s-01-01' % (int(year) + 1),
         '--format="%an"'])
    commits = commits.splitlines()

    stats['commits'] = len(commits)
    committers = {}
    for mem in commits:
        committers[mem] = committers.get(mem, 0) + 1

    committers = committers.items()
    committers.sort(key=lambda item: item[1])
    committers.reverse()
    stats['committers'] = committers

    print 'Total commits:', stats['commits']
    print ''
    for mem in stats['committers']:
        print '  %30s : %s' % (mem[0], mem[1])


def print_header(text):
    print ''
    print text
    print '=' * len(text)
    print ''


def main(argv):
    # XXX: This helps debug bugzilla xmlrpc bits.
    # logging.basicConfig(level=logging.DEBUG)

    if not argv:
        print USAGE
        print 'Error: Must specify the year. e.g. 2012'
        return 1

    year = argv[0]

    print HEADER

    print_header('Twas the year: %s' % year)

    print_header('Bugzilla')
    print_bugzilla_stats(year)

    print_header('git')
    print_git_stats(year)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
