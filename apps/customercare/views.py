import calendar
from datetime import datetime
from email.utils import parsedate, formatdate
import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotFound, HttpResponseServerError)
from django.views.decorators.http import require_POST, require_GET
from django.utils.datastructures import SortedDict

from babel.numbers import format_number
import bleach
import jingo
from session_csrf import anonymous_csrf
from tower import ugettext as _, ugettext_lazy as _lazy
import tweepy

from customercare.models import Tweet, Reply
import twitter


log = logging.getLogger('k.customercare')

MAX_TWEETS = 20
FILTERS = SortedDict([('recent', _lazy('Most Recent')),
                      ('unanswered', _lazy('Unanswered')),
                      ('answered', _lazy('Answered')),
                      ('all', _lazy('All'))])


CANNED_RESPONSES = [
    {'title': _lazy("Welcome and Thanks"),
     'responses':
     [{'title': _lazy("Thanks for using Firefox"),
       # L10n: This is a reply tweet, so it must fit in 140 characters.
       'response': _lazy("thanks for using Firefox! You're not just a user, "
                         "but part of a community that's 400M strong "
                         "http://mzl.la/e8xdv5")
        },
        {'title': _lazy("Tips &amp; tricks"),
        # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("getting started with Firefox? Here are some tips "
                           "&amp; tricks for getting the most out of it "
                           "http://mzl.la/c0B9P2")
        },
        {'title': _lazy("We're a non-profit organization"),
        # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("hey, I'm a Mozilla volunteer. Did you know there "
                           "are 1000s of us worldwide? More here "
                           "http://mzl.la/cvlwvd")
        },
        {'title': _lazy("Welcome to our community"),
        # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("Thanx for joining Moz! You're now part of our "
                           "global community. We're here if you need help "
                           "http://mzl.la/bMDof6")
        }]
    },
    {'title': _lazy("Using Firefox"),
     'responses':
     [{'title': _lazy("Add-on reviews"),
        # L10n: This is a reply tweet, so it must fit in 140 characters.
       'response': _lazy("getting started with Firefox? Add-ons personalize it"
                         " w cool features &amp; function. Some faves "
                         "http://mzl.la/cGypVI")
        },
        {'title': _lazy("Customize Firefox with add-ons"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("have you tried add-ons? Cool apps for shopping, "
                           "music, news, whatever you do online. Start here: "
                           "http://mzl.la/blOuoD")
        },
        {'title': _lazy("Firefox Panorama"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("heard about Firefox Panorama? It groups + displays"
                           " your tabs, eliminating clutter. Try it "
                           "http://mzl.la/d21MyY")
        },
        {'title': _lazy("Firefox Sync"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("tried Firefox Sync? It's awesome! Switch computers"
                           " &amp; it saves open tabs, pwords, history. Try it"
                           " http://mzl.la/aHHUYA")
        },
        {'title': _lazy("Update plugins and add-ons"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("have you updated your plug-ins and add-ons? Should"
                           " work out the kinks. Here's the place to refresh "
                           "http://mzl.la/cGCg12")
        },
        {'title': _lazy("Upgrade Firefox"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("hey, maybe you need to upgrade Firefox? New "
                           "version is speedier with a lot more going on: "
                           "http://mzl.la/9wJe30")
        }]
    },
    {'title': _lazy("Support"),
     'responses':
     [{'title': _lazy("Ask SUMO"),
        # L10n: This is a reply tweet, so it must fit in 140 characters.
       'response': _lazy("maybe ask SUMO about this issue? Firefox's community"
                         " support team. They'll know what's up: "
                         "http://mzl.la/bMDof6")
        },
        {'title': _lazy("Firefox doesn't behave"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("sorry your Firefox doesn't behave. Check out the "
                           "tips here http://mzl.la/bNps7F")
        },
        {'title': _lazy("Firefox is slow"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("you can make your Firefox fast again. Try out "
                           "these steps http://mzl.la/9bB1FY")
        },
        {'title': _lazy("Fix crashes"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("sorry your Firefox is hanging :( Here are quick "
                           "fixes to prevent this again http://mzl.la/atSsFt")
        },
        {'title': _lazy("High RAM usage"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("Firefox sometimes uses more memory than it should."
                           " Try one of these easy fixes http://mzl.la/fPTNo8")
        },
        {'title': _lazy("Quick Firefox fixes"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("have you tried Firefox support? If their quick "
                           "fixes don't help, volunteers can assist! "
                           "http://mzl.la/9V9uWd")
        },
        {'title': _lazy("Slow Firefox startup"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("Firefox needs a refresh. Here are tips to make "
                           "Firefox load faster http://mzl.la/r0mGyN")
        }]
    },
    {'title': _lazy("Get Involved"),
     'responses':
     [{'title': _lazy("Become a beta tester"),
       # L10n: This is a reply tweet, so it must fit in 140 characters.
       'response': _lazy("become a beta tester! Help develop the next Firefox."
                         "You don't have to be a techie to contribute: "
                         "http://mzl.la/d23n7a")
        },
        {'title': _lazy("Get involved with Mozilla"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("Want a better web? Join the Mozilla movement. "
                           "There is something to do for everyone. Get started"
                           " http://mzl.la/cufJmX")
        },
        {'title': _lazy("Join Drumbeat"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("want to spark a movement? Mozilla Drumbeat is your"
                           " chance to keep the web open and free. More info "
                           "http://mzl.la/aIXCLA")
        },
        {'title': _lazy("Mozilla Developer Network"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("help make the web better! Build web pages, apps "
                           "&amp; add-ons here: Mozilla Developer Network "
                           "http://mzl.la/9gQfrn")
        },
        {'title': _lazy("Report a bug"),
         # L10n: This is a reply tweet, so it must fit in 140 characters.
         'response': _lazy("Thanks for finding a bug. Make everyone's Firefox"
                           " experience better by reporting. It's easy "
                           "http://mzl.la/bcujVc")
        }]
    }]


def _tweet_for_template(tweet):
    """Return the dict needed for tweets.html to render a tweet + replies."""
    data = json.loads(tweet.raw_json)

    parsed_date = parsedate(data['created_at'])
    date = datetime(*parsed_date[0:6])

    # Recursively fetch replies.
    if settings.CC_SHOW_REPLIES:
        # If ever slow, optimize to do fewer queries.
        replies = _get_tweets(limit=0, reply_to=tweet)
    else:
        replies = None

    return {'profile_img': bleach.clean(data['profile_image_url']),
            'user': bleach.clean(data['from_user']),
            'text': bleach.clean(data['text']),
            'id': tweet.pk,
            'date': date,
            'reply_count': len(replies) if replies else 0,
            'replies': replies,
            'reply_to': tweet.reply_to and tweet.reply_to.pk,
            'hidden': tweet.hidden}


def _get_tweets(locale=settings.LANGUAGE_CODE, limit=MAX_TWEETS, max_id=None,
                reply_to=None, filter=None):
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
    # Uncached so we can immediately see our reply if we switch to the Answered
    # filter:
    q = Tweet.uncached.filter(locale=locale, reply_to=reply_to)
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

    return [_tweet_for_template(tweet) for tweet in q]


@require_GET
def more_tweets(request):
    """AJAX view returning a list of tweets."""
    max_id = request.GET.get('max_id')

    raw_filter = request.GET.get('filter')
    filter = raw_filter if raw_filter in FILTERS else 'recent'

    return jingo.render(request, 'customercare/tweets.html',
                        {'tweets': _get_tweets(locale=request.locale,
                                               max_id=max_id,
                                               filter=filter)})


@require_GET
@anonymous_csrf  # Need this so the anon csrf gets set for forms rendered.
@twitter.auth_wanted
def landing(request):
    """Customer Care Landing page."""

    twitter = request.twitter

    # Stats. See customercare.cron.get_customercare_stats.
    activity = cache.get(settings.CC_TWEET_ACTIVITY_CACHE_KEY)
    if activity and 'resultset' in activity:
        activity_stats = []
        for act in activity['resultset']:
            if act is None:  # Sometimes we get bad data here.
                continue
            activity_stats.append((act[0], {
                'requests': format_number(act[1], locale='en_US'),
                'replies': format_number(act[2], locale='en_US'),
                'perc': act[3] * 100,
            }))
    else:
        activity_stats = []

    contributors = cache.get(settings.CC_TOP_CONTRIB_CACHE_KEY)
    if contributors and 'resultset' in contributors:
        contributor_stats = {}
        for contrib in contributors['resultset']:
            # Create one list per time period
            period = contrib[1]
            if not contributor_stats.get(period):
                contributor_stats[period] = []
            elif len(contributor_stats[period]) == 16:
                # Show a max. of 16 people.
                continue

            contributor_stats[period].append({
                'name': contrib[2],
                'username': contrib[3],
                'count': contrib[4],
                'avatar': contributors['avatars'].get(contrib[3]),
            })
    else:
        contributor_stats = {}

    return jingo.render(request, 'customercare/landing.html', {
        'activity_stats': activity_stats,
        'contributor_stats': contributor_stats,
        'canned_responses': CANNED_RESPONSES,
        'tweets': _get_tweets(locale=request.locale),
        'authed': twitter.authed,
        'twitter_user': (twitter.api.auth.get_username() if
                         twitter.authed else None),
        'filters': FILTERS,
    })


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
        result = request.twitter.api.update_status(content, reply_to_id)
    except tweepy.TweepError, e:
        # L10n: {message} is an error coming from our twitter api library
        return HttpResponseBadRequest(
            _('An error occured: {message}').format(message=e))

    # Store reply in database.

    # If tweepy's status models actually implemented a dictionary, it would
    # be too boring.
    status = dict(result.__dict__)
    author = dict(result.author.__dict__)

    # Raw JSON blob data
    raw_tweet_data = {
        'id': status['id'],
        'text': status['text'],
        'created_at': formatdate(calendar.timegm(
            status['created_at'].timetuple())),
        'iso_language_code': author['lang'],
        'from_user_id': author['id'],
        'from_user': author['screen_name'],
        'profile_image_url': author['profile_image_url'],
    }

    # The tweet with id `reply_to_id` will not be missing from the DB unless
    # the purge cron job has run since the user loaded the form and we are
    # replying to a deleted tweet. TODO: Catch integrity error and log or
    # something.
    tweet = Tweet.objects.create(pk=status['id'],
                         raw_json=json.dumps(raw_tweet_data),
                         locale=author['lang'],
                         created=status['created_at'],
                         reply_to_id=reply_to_id)

    # Record in our Reply table.
    Reply.objects.create(
        user=request.user if request.user.is_authenticated() else None,
        twitter_username=author['screen_name'],
        tweet_id=status['id'],
        raw_json=json.dumps(raw_tweet_data),
        locale=author['lang'],
        created=status['created_at'],
        reply_to_tweet_id=reply_to_id
    )

    # We could optimize by not encoding and then decoding JSON.
    return jingo.render(request, 'customercare/tweets.html',
        {'tweets': [_tweet_for_template(tweet)]})


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
