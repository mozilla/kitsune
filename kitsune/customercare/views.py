import json
import logging
from datetime import datetime, timedelta
from email.utils import parsedate

from django.conf import settings
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotFound, HttpResponseServerError)
from django.shortcuts import render
from django.utils.datastructures import SortedDict
from django.views.decorators.http import require_POST, require_GET

import bleach
from session_csrf import anonymous_csrf
from statsd import statsd
from tower import ugettext as _, ugettext_lazy as _lazy
from twython import TwythonAuthError, TwythonError

from kitsune import twitter
from kitsune.customercare.models import Tweet, Reply
from kitsune.customercare.replies import get_common_replies
from kitsune.sumo.decorators import ssl_required
from kitsune.sumo.redis_utils import redis_client, RedisError


log = logging.getLogger('k.customercare')

MAX_TWEETS = 20
FILTERS = SortedDict([('recent', _lazy('Most Recent')),
                      ('unanswered', _lazy('Unanswered')),
                      ('answered', _lazy('Answered')),
                      ('all', _lazy('All'))])


def _tweet_for_template(tweet, https=False):
    """Return the dict needed for tweets.html to render a tweet + replies."""
    data = json.loads(tweet.raw_json)
    parsed_date = parsedate(data['created_at'])
    date = datetime(*parsed_date[0:6])

    # Recursively fetch replies.
    if settings.CC_SHOW_REPLIES:
        # If ever slow, optimize to do fewer queries.
        replies = _get_tweets(limit=0, reply_to=tweet, https=https)
    else:
        replies = None

    if 'from_user' in data:  # For tweets collected using v1 API
        user_data = data
        from_user = data['from_user']
    else:
        user_data = data['user']
        from_user = user_data['screen_name']

    if https:
        img = bleach.clean(user_data['profile_image_url_https'])
    else:
        img = bleach.clean(user_data['profile_image_url'])

    return {'profile_img': img,
            'user': from_user,
            'text': bleach.clean(data['text']),
            'id': tweet.pk,
            'date': date,
            'reply_count': len(replies) if replies else 0,
            'replies': replies,
            'reply_to': tweet.reply_to and tweet.reply_to.pk,
            'hidden': tweet.hidden}


def _get_tweets(locale=settings.LANGUAGE_CODE, limit=MAX_TWEETS, max_id=None,
                reply_to=None, filter=None, https=False):
    """
    Fetch a list of tweets.

    Args:
        limit: the maximum number of tweets returned
        max_id: Return tweets with tweet_id less than this.
        reply_to: Return only tweets that are replies to the given Tweet. If
            None, return only top-level (non-reply) tweets.
        filter: One of the keys from FILTERS
    """
    locale = settings.LOCALES[locale].iso639_1
    created_limit = datetime.now() - timedelta(days=settings.CC_TWEETS_DAYS)
    # Uncached so we can immediately see our reply if we switch to the Answered
    # filter:

    q = Tweet.uncached.filter(
        locale=locale,
        reply_to=reply_to,
        created__gt=created_limit)

    if max_id:
        q = q.filter(pk__lt=max_id)

    if filter != 'all':
        q = q.filter(hidden=False)
    if filter == 'unanswered':
        q = q.filter(replies__pk__isnull=True)
    elif filter == 'answered':
        q = q.filter(replies__pk__isnull=False)

    if limit:
        q = q[:limit]

    return [_tweet_for_template(tweet, https) for tweet in q]


def _count_answered_tweets(since=None):
    q = Reply.uncached.values('reply_to_tweet_id').distinct()

    if since:
        q = q.filter(created__gte=since)

    return q.count()


@require_GET
def more_tweets(request):
    """AJAX view returning a list of tweets."""
    max_id = request.GET.get('max_id')

    raw_filter = request.GET.get('filter')
    filter = raw_filter if raw_filter in FILTERS else 'recent'

    return render(request, 'customercare/tweets.html', {
        'tweets': _get_tweets(
            locale=request.LANGUAGE_CODE,
            max_id=max_id,
            filter=filter,
            https=request.is_secure())})


@ssl_required
@require_GET
@anonymous_csrf  # Need this so the anon csrf gets set for forms rendered.
@twitter.auth_wanted
def landing(request):
    """Customer Care Landing page."""

    # Get a redis client
    redis = None
    try:
        redis = redis_client(name='default')
    except RedisError as e:
        statsd.incr('redis.errror')
        log.error('Redis error: %s' % e)

    contributor_stats = redis and redis.get(settings.CC_TOP_CONTRIB_CACHE_KEY)
    if contributor_stats:
        contributor_stats = json.loads(contributor_stats)
        statsd.incr('customercare.stats.contributors.hit')
    else:
        statsd.incr('customercare.stats.contributors.miss')

    twitter_user = None
    if request.twitter.authed:
        try:
            credentials = request.twitter.api.verify_credentials()
        except (TwythonError, TwythonAuthError):
            # Bad oauth token. Create a new session so user re-auths.
            request.twitter = twitter.Session()
        else:
            twitter_user = credentials['screen_name']

    yesterday = datetime.now() - timedelta(days=1)

    recent_replied_count = _count_answered_tweets(since=yesterday)

    return render(request, 'customercare/landing.html', {
        'contributor_stats': contributor_stats,
        'canned_responses': get_common_replies(request.LANGUAGE_CODE),
        'tweets': _get_tweets(locale=request.LANGUAGE_CODE,
                              https=request.is_secure()),
        'authed': request.user.is_authenticated() and request.twitter.authed,
        'twitter_user': twitter_user,
        'filters': FILTERS,
        'goal': settings.CC_REPLIES_GOAL,
        'recent_replied_count': recent_replied_count})


@require_POST
@anonymous_csrf
@twitter.auth_required
def twitter_post(request):
    """Post a tweet, and return a rendering of it (and any replies)."""

    try:
        reply_to_id = int(request.POST.get('reply_to', ''))
    except ValueError:
        # L10n: the tweet needs to be a reply to another tweet.
        return HttpResponseBadRequest(_('Reply-to is empty'))

    content = request.POST.get('content', '')
    if len(content) == 0:
        # L10n: the tweet has no content.
        return HttpResponseBadRequest(_('Message is empty'))

    if len(content) > 140:
        return HttpResponseBadRequest(_('Message is too long'))

    try:
        credentials = request.twitter.api.verify_credentials()
        username = credentials['screen_name']
        if username in settings.CC_BANNED_USERS:
            return render(request, 'customercare/tweets.html',
                          {'tweets': []})
        result = request.twitter.api.update_status(
            status=content,
            in_reply_to_status_id=reply_to_id)
    except (TwythonError, TwythonAuthError), e:
        # L10n: {message} is an error coming from our twitter api library
        return HttpResponseBadRequest(
            _('An error occured: {message}').format(message=e))

    # Store reply in database.

    # If tweepy's status models actually implemented a dictionary, it would
    # be too boring.
    status = result
    author = result['user']
    created_at = datetime.strptime(status['created_at'],
                                   '%a %b %d %H:%M:%S +0000 %Y')

    # Raw JSON blob data
    # Note: The JSON for the tweet posted is different than what we get from
    # the search API. This makes it similar with the fields that we use.
    raw_tweet_data = {
        'id': status['id'],
        'text': status['text'],
        'created_at': status['created_at'],
        'iso_language_code': author['lang'],
        'from_user_id': author['id'],
        'from_user': author['screen_name'],
        'profile_image_url': author['profile_image_url'],
        'profile_image_url_https': author['profile_image_url_https'],
    }

    # The tweet with id `reply_to_id` will not be missing from the DB unless
    # the purge cron job has run since the user loaded the form and we are
    # replying to a deleted tweet. TODO: Catch integrity error and log or
    # something.
    tweet = Tweet.objects.create(pk=status['id'],
                                 raw_json=json.dumps(raw_tweet_data),
                                 locale=author['lang'],
                                 created=created_at,
                                 reply_to_id=reply_to_id)

    # Record in our Reply table.
    Reply.objects.create(
        user=request.user if request.user.is_authenticated() else None,
        twitter_username=author['screen_name'],
        tweet_id=status['id'],
        raw_json=json.dumps(raw_tweet_data),
        locale=author['lang'],
        created=created_at,
        reply_to_tweet_id=reply_to_id
    )

    # We could optimize by not encoding and then decoding JSON.
    return render(request, 'customercare/tweets.html', {
        'tweets': [_tweet_for_template(tweet, request.is_secure())]})


@require_POST
@anonymous_csrf
def hide_tweet(request):
    """
    Hide the tweet with a given ID. Only hides tweets that are not replies
    and do not have replies.

    Returns proper HTTP status codes.
    """
    # If feature disabled, bail.
    if not settings.CC_ALLOW_REMOVE:
        return HttpResponse(status=418)  # I'm a teapot.

    try:
        id = int(request.POST.get('id'))
    except (ValueError, TypeError):
        return HttpResponseBadRequest(_('Invalid ID.'))

    try:
        tweet = Tweet.objects.get(pk=id)
    except Tweet.DoesNotExist:
        return HttpResponseNotFound(_('Invalid ID.'))

    if (tweet.reply_to is not None or
            Tweet.objects.filter(reply_to=tweet).exists()):
        return HttpResponseBadRequest(_('Tweets that are replies or have '
                                        'replies must not be hidden.'))

    try:
        tweet.hidden = True
        tweet.save(force_update=True)
    except Exception, e:
        return HttpResponseServerError(
            _('An error occured: {message}').format(message=e))

    return HttpResponse('ok')
