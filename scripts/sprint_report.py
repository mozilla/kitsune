#!/usr/bin/env python
import logging
import sys
import textwrap
import xmlrpclib


USAGE = 'Usage: sprint_report.py <SPRINT>'
HEADER = 'sprint_report.py: your friendly report view of the sprint!'


# Note: Most of the bugzila api code comes from Scrumbugz.

cache = {}
log = logging.getLogger(__name__)
BZ_URL = 'http://bugzilla.mozilla.org/xmlrpc.cgi'
SESSION_COOKIES_CACHE_KEY = 'bugzilla-session-cookies'

BZ_RESOLUTIONS = ['', 'FIXED', 'INVALID', 'WONTFIX', 'DUPLICATE',
                  'WORKSFORME', 'DUPLICATE']
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
        get_history = kwargs.pop('history', True)
        get_comments = kwargs.pop('comments', True)
        kwargs.update({
            'include_fields': BZ_FIELDS,
        })
        if 'ids' in kwargs:
            kwargs['permissive'] = True
            log.debug('Getting bugs with kwargs: %s', kwargs)
            bugs = self.Bug.get(kwargs)
        else:
            if 'whiteboard' not in kwargs:
                kwargs['whiteboard'] = ['u=', 'c=', 'p=']
            log.debug('Searching bugs with kwargs: %s', kwargs)
            bugs = self.Bug.search(kwargs)

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


def sprint_stats(bugs):
    """Print bugs stats block."""
    # Return dict of bugs stats
    #
    # * total points
    # * breakdown of points by component
    # * breakdown of points by focus
    # * breakdown of points by priority
    # * other things?


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


def get_history(bugs, sprint):
    history = []

    for bug in bugs:
        for item in bug.get('history', []):
            for change in item.get('changes', []):
                added = parse_whiteboard(change['added'])
                removed = parse_whiteboard(change['removed'])

                if ((change['field_name'] == 'status_whiteboard'
                     and removed['s'] != sprint
                     and added['s'] == sprint)):

                    history.append((
                            item['when'],
                            bug,
                            item['who'],
                            removed['s'],
                            added['s']
                            ))

    return history


def sprint_timeline(bugs, sprint):
    """Print timeline block."""
    timeline = []

    history = get_history(bugs, sprint)

    # Try to associate the change that added the sprint to the
    # whiteboard with a comment.
    for when, bug, who, removed, added in history:
        reason = 'NO COMMENT'
        for comment in bug.get('comments', []):
            if comment['time'] == when and comment['creator'] == who:
                reason = comment['text']
                break

        timeline.append((
                when,
                bug['id'],
                who,
                removed,
                added,
                reason
                ))

    timeline.sort(key=lambda item: item[0])
    for mem in timeline:
        print '%s: %s: %s' % (mem[0], mem[1], mem[2])
        print '    %s -> %s' % (mem[3] if mem[3] else 'unassigned', mem[4])
        print wrap(mem[5])
        print ''


def print_header(text):
    print text
    print '=' * len(text)
    print ''


def main(argv):
    # logging.basicConfig(level=logging.DEBUG)

    if not argv:
        print USAGE
        print 'Error: Must specify the sprint to report on. e.g. 2012.19'
        return 1

    sprint = argv[0]

    print HEADER

    print ''
    print 'Working on %s' % sprint
    print ''

    bugzilla = BugzillaAPI(
        BZ_URL,
        transport=SessionTransport(use_datetime=True),
        allow_none=True)

    bugs = bugzilla.get_bugs(
        product=['support.mozilla.org'],
        whiteboard=['s=' + sprint],
        resolution=BZ_RESOLUTIONS,
        history=True,
        comments=True)
    bugs = bugs['bugs']

    print_header('Timeline')
    sprint_timeline(bugs, sprint)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
