# -*- coding: utf-8 -*-
#
# This tries to fix bug 1357563 in a best effort way. It may find a proper page
# to redirect users to but if it fails it will raise a 404.
#
# Flow:
#
# 1. Checks if the response is 404 and it's from a Lithium URL (/t5/*)
# 2. Checks cache, redirects if successful
# 3. Checks popular Lithium pages from LithiumRedirectionMiddleware.extra_pages,
#    redirects if successful
# 4. Checks Lithium localized product_pages from
#    LithiumRedirectionMiddleware.product_pages, redirects if successful
# In all cases we append ?cache=no in the redirect to bust the cache
# All redirects are 302s
#
#

import hashlib
import re

from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.translation import pgettext
from django.utils import translation

from kitsune.products.models import Product, Topic
from kitsune.sumo.views import handle404

# build a list of topics translated for reverse lookup
TOPICS = {}
for topic in set(Topic.objects.values_list('title', flat=True)):
    for lang in settings.SUMO_LANGUAGES:
        with translation.override(lang):
            trans_text = pgettext('DB: products.Topic.title', topic)
        TOPICS[trans_text] = topic

PRODUCTS = {}
for product in set(Product.objects.values_list('title', flat=True)):
    for lang in settings.SUMO_LANGUAGES:
        with translation.override(lang):
            trans_text = pgettext('DB: products.Product.title', product)
        PRODUCTS[trans_text] = product


class LithiumRedirectionMiddleware():
    meta_regex = re.compile('<meta content="(.*?)" property="(.*?)"/>')
    product_pages = {
        u'Mozilla-Hilfe-Deutsch': '/de/?cache=no',
        u'Soporte-de-Mozilla-Español': '/es/?cache=no',
        u'Magyar': '/hu/?cache=no',
        u'Pomoc-Mozilli-polski': '/pl/?cache=no',
        u'Podpora-Mozilly-slovenčina': '/sk/?cache=no',
        u'Поддержка-Mozilla-Русский': '/ru/?cache=no',
        u'Podpora-Mozilly-Čeština': '/cs/?cache=no',
        u'Mozilla-Support-Ελληνικά': '/el/?cache=no',
        u'Mozilla-tuki-suomi': '/fi/?cache=no',
        u'Dukungan-Mozilla-Bahasa': '/hi-IN/?cache=no',
        u'Suporte-Mozilla-Português-do': '/pt-br/?cache=no',
        u'Mozilla-Destek-Türkçe': '/tr/?cache=no',
        u'Підтримка-Mozilla-Українська': '/uk/?cache=no',
        u'Mozilla-Support-Dansk': '/da/?cache=no',
        u'Mozilla-Support-English': '/en/?cache=no',
        u'Assistance-de-Mozilla-Français': '/fr/?cache=no',
        u'Supporto-Mozilla-Italiano': '/it/?cache=no',
        u'Mozilla-Support-Nederlands': '/nl/?cache=no',
        u'Apoio-da-Mozilla-Português': '/pt/?cache=no',
        u'Mozilla-Support-Svenska': '/sv/?cache=no',
        'Mozilla-\xe3\x82\xb5\xe3\x83\x9d\xe3\x83\xbc\xe3\x83\x88-\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e': '/ja/?cache=no',  # noqa
        'Mozilla-\xe6\x8a\x80\xe8\xa1\x93\xe6\x94\xaf\xe6\x8f\xb4-\xe6\xad\xa3\xe9\xab\x94\xe4\xb8\xad\xe6\x96\x87-\xe7\xb9\x81\xe9\xab\x94': '/zh-TW/?cache=no',  # noqa
        'Mozilla-\xeb\x8f\x84\xec\x9b\x80\xeb\xa7\x90-\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4': '/ko/?cache=no',  # noqa
        'Mozilla-\xe6\x8a\x80\xe6\x9c\xaf\xe6\x94\xaf\xe6\x8c\x81-\xe4\xb8\xad\xe6\x96\x87-\xe7\xae\x80\xe4\xbd\x93': '/zh-CN/?cache=no',  # noqa
        '\xd8\xaf\xd8\xb9\xd9\x85-\xd9\x81\xd9\x8e\xd9\x8a\xd9\x8e\xd8\xb1\xd9\x81\xd9\x8f\xd9\x83\xd8\xb3-\xd8\xb9\xd8\xb1\xd8\xa8\xd9\x8a': '/ar/?cache=no',  # noqa
    }

    extra_pages = {
        '/t5/How-To/Cookies/ta-p/16348': '/kb/cookies-information-websites-store-on-your-computer?cache=no',  # noqa
        '/t5/Fix-slowness-crashing-error/What-does-quot-Your-connection-is-not-secure-quot-mean/ta-p/30354': '/kb/what-does-your-connection-is-not-secure-mean?cache=no',  # noqa
        '/t5/Firefox-for-Android/ct-p/Firefox-Android': '/products/mobile?cache=no',
        '/t5/Manage-preferences-and-add-ons/Disable-or-remove-Add-ons/ta-p/1000': '/kb/disable-or-remove-add-ons?cache=no',  # noqa
    }

    def process_response(self, request, response):
        if (response.status_code != 404):
            return response

        urlparts = request.path_info.split('/')
        try:
            if not urlparts[1].startswith('t5'):
                return response
        except KeyError:
            return response

        # Oh boy, Lithium URL. Let's see if we can turn things around.

        # Cache first
        cache_key = hashlib.sha1(request.path_info.encode('utf-8')).hexdigest()
        cached_redirect = cache.get(cache_key)
        if cached_redirect:
            return HttpResponseRedirect(cached_redirect)

        if request.path_info in self.extra_pages:
            return HttpResponseRedirect(self.extra_pages[request.path_info])

        if urlparts[2] in self.product_pages:
            return HttpResponseRedirect(self.product_pages[urlparts[2]])

        # everything failed, kittens die, it's a 404
        return handle404(request)
