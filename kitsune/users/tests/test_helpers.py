# -*- coding: utf-8 -*-
import hashlib

from django.contrib.auth.models import AnonymousUser, User

from jinja2 import Markup
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.tests import TestCase
from kitsune.users.helpers import (
    profile_url, profile_avatar, public_email, display_name, user_list)
from kitsune.users.tests import profile, user


class HelperTestCase(TestCase):
    def setUp(self):
        super(HelperTestCase, self).setUp()
        self.u = user(username=u'testuser', save=True)

    def test_profile_url(self):
        eq_(u'/user/%s' % self.u.username, profile_url(self.u))

    def test_profile_avatar_default(self):
        profile(user=self.u)
        email_hash = hashlib.md5(self.u.email.lower()).hexdigest()
        gravatar_url = 'https://secure.gravatar.com/avatar/%s?s=48' % (
            email_hash)
        assert profile_avatar(self.u).startswith(gravatar_url)

    def test_profile_avatar_anonymous(self):
        email_hash = '00000000000000000000000000000000'
        gravatar_url = 'https://secure.gravatar.com/avatar/%s?s=48' % (
            email_hash)
        assert profile_avatar(AnonymousUser()).startswith(gravatar_url)

    def test_profile_avatar(self):
        profile(user=self.u, avatar='images/foo.png')
        email_hash = hashlib.md5(self.u.email.lower()).hexdigest()
        gravatar_url = 'https://secure.gravatar.com/avatar/%s?s=48' % (
            email_hash)
        assert profile_avatar(self.u).startswith(gravatar_url)

    def test_profile_avatar_unicode(self):
        self.u.email = u'rápido@example.com'
        self.u.save()
        profile(user=self.u)
        gravatar_url = 'https://secure.gravatar.com/'
        assert profile_avatar(self.u).startswith(gravatar_url)

    def test_public_email(self):
        eq_(u'<span class="email">'
            u'&#109;&#101;&#64;&#100;&#111;&#109;&#97;&#105;&#110;&#46;&#99;'
            u'&#111;&#109;</span>', public_email('me@domain.com'))
        eq_(u'<span class="email">'
            u'&#110;&#111;&#116;&#46;&#97;&#110;&#46;&#101;&#109;&#97;&#105;'
            u'&#108;</span>', public_email('not.an.email'))

    def test_display_name(self):
        eq_(u'testuser', display_name(self.u))
        profile(user=self.u, name=u'Test User')
        eq_(u'Test User', display_name(self.u))
        eq_(u'', display_name(AnonymousUser()))

    def test_user_list(self):
        user(username='testuser2', save=True)
        user(username='testuser3', save=True)
        users = User.objects.all()
        list = user_list(users)
        assert isinstance(list, Markup)
        fragment = pq(list)
        eq_(len(users), len(fragment('a')))
        a = fragment('a')[1]
        assert a.attrib['href'].endswith(str(users[1].username))
        eq_(users[1].username, a.text)
