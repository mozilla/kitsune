import calendar
from datetime import datetime, timedelta
import json
import logging
import re
import rfc822

from django.conf import settings
from django.db.utils import IntegrityError

import cronjobs
from multidb.pinning import pin_this_thread
from statsd import statsd

from kitsune.customercare.models import Tweet, TwitterAccount, Reply
from kitsune.sumo.redis_utils import redis_client, RedisError
from kitsune.sumo.utils import chunked
from kitsune.twitter import get_twitter_api


LINK_REGEX = re.compile('https?\:', re.IGNORECASE)
RT_REGEX = re.compile('^rt\W', re.IGNORECASE)

ALLOWED_USERS = [
    {'id': 2142731, 'username': 'Firefox'},
    {'id': 150793437, 'username': 'FirefoxBrasil'},
    {'id': 107272435, 'username': 'firefox_es'},
]

log = logging.getLogger('k.twitter')


def get_word_blacklist_regex():
    """
    Make a regex that looks kind of like r'\b(foo|bar|baz)\b'.

    This is a function so that it isn't calculated at import time,
    and so can be tested more easily.

    This doesn't use raw strings (r'') because the "mismatched" parens
    were confusing my syntax highlighter, which was confusing me.
    """
    return re.compile(
        '\\b(' +
        '|'.join(map(re.escape, settings.CC_WORD_BLACKLIST)) +
        ')\\b')


@cronjobs.register
def collect_tweets():
    # Don't (ab)use the twitter API from dev and stage.
    if settings.STAGE:
        return

    """Collect new tweets about Firefox."""
    with statsd.timer('customercare.tweets.time_elapsed'):
        t = get_twitter_api()

        search_options = {
            'q': ('firefox OR #fxinput OR @firefoxbrasil OR #firefoxos '
                  'OR @firefox_es'),
            'count': settings.CC_TWEETS_PERPAGE,  # Items per page.
            'result_type': 'recent',  # Retrieve tweets by date.
        }

        # If we already have some tweets, collect nothing older than what we
        # have.
        try:
            latest_tweet = Tweet.latest()
        except Tweet.DoesNotExist:
            log.debug('No existing tweets. Retrieving %d tweets from search.' %
                      settings.CC_TWEETS_PERPAGE)
        else:
            search_options['since_id'] = latest_tweet.tweet_id
            log.info('Retrieving tweets with id >= %s' % latest_tweet.tweet_id)

        # Retrieve Tweets
        results = t.search(**search_options)

        if len(results['statuses']) == 0:
            # Twitter returned 0 results.
            return

        # Drop tweets into DB
        for item in results['statuses']:
            # Apply filters to tweet before saving
            # Allow links in #fxinput tweets
            statsd.incr('customercare.tweet.collected')
            item = _filter_tweet(item,
                                 allow_links='#fxinput' in item['text'])
            if not item:
                continue

            created_date = datetime.utcfromtimestamp(calendar.timegm(
                rfc822.parsedate(item['created_at'])))

            item_lang = item['metadata'].get('iso_language_code', 'en')

            tweet = Tweet(tweet_id=item['id'], raw_json=json.dumps(item),
                          locale=item_lang, created=created_date)
            try:
                tweet.save()
                statsd.incr('customercare.tweet.saved')
            except IntegrityError:
                pass


@cronjobs.register
def purge_tweets():
    """Periodically purge old tweets for each locale.

    This does a lot of DELETEs on master, so it shouldn't run too frequently.
    Probably once every hour or more.

    """
    # Pin to master
    pin_this_thread()

    # Build list of tweets to delete, by id.
    for locale in settings.SUMO_LANGUAGES:
        locale = settings.LOCALES[locale].iso639_1
        # Some locales don't have an iso639_1 code, too bad for them.
        if not locale:
            continue
        oldest = _get_oldest_tweet(locale, settings.CC_MAX_TWEETS)
        if oldest:
            log.debug('Truncating tweet list: Removing tweets older than %s, '
                      'for [%s].' % (oldest.created, locale))
            Tweet.objects.filter(locale=locale,
                                 created__lte=oldest.created).delete()


def _get_oldest_tweet(locale, n=0):
    """Returns the nth oldest tweet per locale, defaults to newest."""
    try:
        return Tweet.objects.filter(locale=locale).order_by(
            '-created')[n]
    except IndexError:
        return None


def _filter_tweet(item, allow_links=False):
    """
    Apply some filters to an incoming tweet.

    May modify tweet. If None is returned, tweet will be discarded.
    Used to exclude replies and such from incoming tweets.
    """
    text = item['text'].lower()
    # No replies, except to ALLOWED_USERS
    allowed_user_ids = [u['id'] for u in ALLOWED_USERS]
    to_user_id = item.get('to_user_id')
    if to_user_id and to_user_id not in allowed_user_ids:
        statsd.incr('customercare.tweet.rejected.reply_or_mention')
        return None

    # No mentions, except of ALLOWED_USERS
    for user in item['entities']['user_mentions']:
        if user['id'] not in allowed_user_ids:
            statsd.incr('customercare.tweet.rejected.reply_or_mention')
            return None

    # No retweets
    if RT_REGEX.search(text) or text.find('(via ') > -1:
        statsd.incr('customercare.tweet.rejected.retweet')
        return None

    # No links
    if not allow_links and LINK_REGEX.search(text):
        statsd.incr('customercare.tweet.rejected.link')
        return None

    screen_name = item['user']['screen_name']

    # Django's caching system will save us here.
    IGNORED_USERS = set(
        TwitterAccount.objects
        .filter(ignored=True)
        .values_list('username', flat=True)
    )

    # Exclude filtered users
    if screen_name in IGNORED_USERS:
        statsd.incr('customercare.tweet.rejected.user')
        return None

    # Exlude users with firefox in the handle
    if 'firefox' in screen_name.lower():
        statsd.incr('customercare.tweet.rejected.firefox_in_handle')
        return None

    # Exclude problem words
    match = get_word_blacklist_regex().search(text)
    if match:
        bad_word = match.group(1)
        statsd.incr('customercare.tweet.rejected.blacklist_word.' + bad_word)
        return None

    return item


@cronjobs.register
def get_customercare_stats():
    """
    Generate customer care stats from the Replies table.

    This gets cached in Redis as a sorted list of contributors, stored as JSON.

    Example Top Contributor data:

    [
        {
            'twitter_username': 'username1',
            'avatar': 'http://twitter.com/path/to/the/avatar.png',
            'avatar_https': 'https://twitter.com/path/to/the/avatar.png',
            'all': 5211,
            '1m': 230,
            '1w': 33,
            '1d': 3,
        },
        { ... },
        { ... },
    ]
    """
    if settings.STAGE:
        return

    contributor_stats = {}

    now = datetime.now()
    one_month_ago = now - timedelta(days=30)
    one_week_ago = now - timedelta(days=7)
    yesterday = now - timedelta(days=1)

    for chunk in chunked(Reply.objects.all(), 2500, Reply.objects.count()):
        for reply in chunk:
            user = reply.twitter_username
            if user not in contributor_stats:
                raw = json.loads(reply.raw_json)
                if 'from_user' in raw:  # For tweets collected using v1 API
                    user_data = raw
                else:
                    user_data = raw['user']

                contributor_stats[user] = {
                    'twitter_username': user,
                    'avatar': user_data['profile_image_url'],
                    'avatar_https': user_data['profile_image_url_https'],
                    'all': 0, '1m': 0, '1w': 0, '1d': 0,
                }
            contributor = contributor_stats[reply.twitter_username]

            contributor['all'] += 1
            if reply.created > one_month_ago:
                contributor['1m'] += 1
                if reply.created > one_week_ago:
                    contributor['1w'] += 1
                    if reply.created > yesterday:
                        contributor['1d'] += 1

    sort_key = settings.CC_TOP_CONTRIB_SORT
    limit = settings.CC_TOP_CONTRIB_LIMIT
    # Sort by whatever is in settings, break ties with 'all'
    contributor_stats = sorted(contributor_stats.values(),
                               key=lambda c: (c[sort_key], c['all']),
                               reverse=True)[:limit]

    try:
        redis = redis_client(name='default')
        key = settings.CC_TOP_CONTRIB_CACHE_KEY
        redis.set(key, json.dumps(contributor_stats))
    except RedisError as e:
        statsd.incr('redis.error')
        log.error('Redis error: %s' % e)

    return contributor_stats
