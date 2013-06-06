import logging
import re

from django import http
from django.conf import settings

import tweepy

from kitsune.twitter import (
    url, Session, REQUEST_KEY_NAME, REQUEST_SECRET_NAME)


log = logging.getLogger('k')


def validate_token(token):
    return bool(token and (len(token) < 100) and re.search('\w+', token))


class SessionMiddleware(object):

    def process_request(self, request):

        request.twitter = Session.from_request(request)

        # If is_secure is True (should always be true except for local dev),
        # we will be redirected back to https and all cookies set will be
        # secure only.
        is_secure = settings.TWITTER_COOKIE_SECURE

        ssl_url = url(request, {'scheme': 'https' if is_secure else 'http'})
        auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY,
                                   settings.TWITTER_CONSUMER_SECRET,
                                   ssl_url,
                                   secure=True)

        if request.REQUEST.get('twitter_delete_auth'):
            request.twitter = Session()
            return http.HttpResponseRedirect(url(request))

        elif request.twitter.authed:
            auth.set_access_token(request.twitter.key, request.twitter.secret)
            request.twitter.api = tweepy.API(auth)

        else:
            verifier = request.GET.get('oauth_verifier')
            if verifier:
                # We are completing an OAuth login

                request_key = request.COOKIES.get(REQUEST_KEY_NAME)
                request_secret = request.COOKIES.get(REQUEST_SECRET_NAME)

                if (validate_token(request_key) and
                    validate_token(request_secret)):
                    auth.set_request_token(request_key, request_secret)

                    try:
                        auth.get_access_token(verifier)
                    except tweepy.TweepError:
                        log.warning('Tweepy Error with verifier token')
                        pass
                    else:
                        # Override path to drop query string.
                        ssl_url = url(
                            request,
                            {'scheme': 'https' if is_secure else 'http',
                             'path': request.path})
                        response = http.HttpResponseRedirect(ssl_url)

                        Session(
                            auth.access_token.key,
                            auth.access_token.secret).save(request, response)
                        return response
                else:
                    # request tokens didn't validate
                    log.warning("Twitter Oauth request tokens didn't validate")

            elif request.REQUEST.get('twitter_auth_request'):
                # We are requesting Twitter auth

                try:
                    redirect_url = auth.get_authorization_url()
                except tweepy.TweepError:
                    log.warning('Tweepy error while getting authorization url')
                else:
                    response = http.HttpResponseRedirect(redirect_url)
                    response.set_cookie(
                        REQUEST_KEY_NAME,
                        auth.request_token.key,
                        secure=is_secure)
                    response.set_cookie(
                        REQUEST_SECRET_NAME,
                        auth.request_token.secret,
                        secure=is_secure)
                    return response

    def process_response(self, request, response):
        if getattr(request, 'twitter', False):
            if request.REQUEST.get('twitter_delete_auth'):
                request.twitter.delete(request, response)

            if request.twitter.authed and REQUEST_KEY_NAME in request.COOKIES:
                response.delete_cookie(REQUEST_KEY_NAME)
                response.delete_cookie(REQUEST_SECRET_NAME)
                request.twitter.save(request, response)

        return response
