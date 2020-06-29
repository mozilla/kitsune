import calendar
import json
import logging
import re
from datetime import datetime
from email import utils as email_utils

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from kitsune.customercare.models import Tweet, TwitterAccount
from kitsune.twitter import get_twitter_api

LINK_REGEX = re.compile(r"https?\:", re.IGNORECASE)
RT_REGEX = re.compile(r"^rt\W", re.IGNORECASE)

ALLOWED_USERS = [
    {"id": 2142731, "username": "Firefox"},
    {"id": 150793437, "username": "FirefoxBrasil"},
    {"id": 107272435, "username": "firefox_es"},
]
log = logging.getLogger("k.twitter")


def get_word_blacklist_regex():
    """
    Make a regex that looks kind of like r'\b(foo|bar|baz)\b'.

    This is a function so that it isn't calculated at import time,
    and so can be tested more easily.

    This doesn't use raw strings (r'') because the "mismatched" parens
    were confusing my syntax highlighter, which was confusing me.
    """
    return re.compile(
        "\\b(" + "|".join(map(re.escape, settings.CC_WORD_BLACKLIST)) + ")\\b"
    )


class Command(BaseCommand):
    def handle(self, **options):
        # Don't (ab)use the twitter API from dev and stage.
        if settings.STAGE:
            return

        """Collect new tweets about Firefox."""
        t = get_twitter_api()

        search_options = {
            "q": "firefox OR #fxinput OR @firefoxbrasil OR #firefoxos OR @firefox_es",
            "count": settings.CC_TWEETS_PERPAGE,  # Items per page.
            "result_type": "recent",  # Retrieve tweets by date.
        }

        # If we already have some tweets, collect nothing older than what we
        # have.
        try:
            latest_tweet = Tweet.latest()
        except Tweet.DoesNotExist:
            log.debug(
                "No existing tweets. Retrieving %d tweets from search."
                % settings.CC_TWEETS_PERPAGE
            )
        else:
            search_options["since_id"] = latest_tweet.tweet_id
            log.info("Retrieving tweets with id >= %s" % latest_tweet.tweet_id)

        # Retrieve Tweets
        results = t.search(**search_options)

        if len(results["statuses"]) == 0:
            # Twitter returned 0 results.
            return

        # Drop tweets into DB
        for item in results["statuses"]:
            # Apply filters to tweet before saving
            # Allow links in #fxinput tweets
            item = _filter_tweet(item, allow_links="#fxinput" in item["text"])
            if not item:
                continue

            created_date = datetime.utcfromtimestamp(
                calendar.timegm(email_utils.parsedate(item["created_at"]))
            )

            item_lang = item["metadata"].get("iso_language_code", "en")

            tweet = Tweet(
                tweet_id=item["id"],
                raw_json=json.dumps(item),
                locale=item_lang,
                created=created_date,
            )
            try:
                tweet.save()
            except IntegrityError:
                pass


def _filter_tweet(item, allow_links=False):
    """
    Apply some filters to an incoming tweet.

    May modify tweet. If None is returned, tweet will be discarded.
    Used to exclude replies and such from incoming tweets.
    """
    text = item["text"].lower()
    # No replies, except to ALLOWED_USERS
    allowed_user_ids = [u["id"] for u in ALLOWED_USERS]
    to_user_id = item.get("to_user_id")
    if to_user_id and to_user_id not in allowed_user_ids:
        return None

    # No mentions, except of ALLOWED_USERS
    for user in item["entities"]["user_mentions"]:
        if user["id"] not in allowed_user_ids:
            return None

    # No retweets
    if RT_REGEX.search(text) or text.find("(via ") > -1:
        return None

    # No links
    if not allow_links and LINK_REGEX.search(text):
        return None

    screen_name = item["user"]["screen_name"]

    # Django's caching system will save us here.
    IGNORED_USERS = set(
        TwitterAccount.objects.filter(ignored=True).values_list("username", flat=True)
    )

    # Exclude filtered users
    if screen_name in IGNORED_USERS:
        return None

    # Exlude users with firefox in the handle
    if "firefox" in screen_name.lower():
        return None

    # Exclude problem words
    match = get_word_blacklist_regex().search(text)
    if match:
        return None

    return item
