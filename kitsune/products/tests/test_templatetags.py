# -*- coding: utf-8 -*-
from django.conf import settings

from nose.tools import eq_

from kitsune.products.templatetags.jinja_helpers import is_localized
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


class HelperTestCase(TestCase):

    def test_is_localized_for_non_existing_article(self):
        """Non existing article cannot be even localized."""
        eq_(False, is_localized('community-hub-news', settings.LANGUAGE_CODE))

    def test_is_localized_for_default_language(self):
        """Articles should be assumed localized for default language."""
        d = DocumentFactory(slug='community-hub-news', locale=settings.LANGUAGE_CODE)
        ApprovedRevisionFactory(document=d)
        d.save()
        eq_(True, is_localized('community-hub-news', settings.LANGUAGE_CODE))

    def test_is_localized_for_non_default_language(self):
        d = DocumentFactory(slug='community-hub-news', locale=settings.LANGUAGE_CODE)
        ApprovedRevisionFactory(document=d)
        d.save()
        eq_(False, is_localized('community-hub-news', 'xx'))

        d_xx = DocumentFactory(parent=d, locale='xx')
        ApprovedRevisionFactory(document=d_xx)
        d_xx.save()
        eq_(True, is_localized('community-hub-news', 'xx'))
