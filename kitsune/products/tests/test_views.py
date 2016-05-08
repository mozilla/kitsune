# -*- coding: utf-8 -*-
from django.conf import settings

from nose.tools import eq_

from kitsune.products.views import is_localized
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


class HelperTestCase(TestCase):

    def test_is_localized_for_non_existing_article(self):
        """Non existing article cannot be even localized."""
        eq_(False, is_localized('community-hub-news', settings.LANGUAGE_CODE))

    def test_is_localized_for_language(self):
        slug = 'community-hub-news'
        locale = 'cs'

        d = DocumentFactory(slug=slug, locale=settings.LANGUAGE_CODE)
        ApprovedRevisionFactory(document=d)
        d.save()
        eq_(False, is_localized(slug, locale))

        d_locale = DocumentFactory(parent=d, locale=locale)
        ApprovedRevisionFactory(document=d_locale)
        d_locale.save()
        eq_(True, is_localized(slug, locale))
