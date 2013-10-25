import hashlib

from django.conf import settings
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
        self.u = User.objects.create(pk=500000, username=u'testuser')

    def test_profile_url(self):
        eq_(u'/user/%d' % self.u.id, profile_url(self.u))

    def test_profile_avatar_default(self):
        profile(user=self.u)
        email_hash = hashlib.md5(self.u.email.lower()).hexdigest()
        gravatar_url = '//www.gravatar.com/avatar/%s?s=48&d=%s' % (
            email_hash, settings.STATIC_URL + settings.DEFAULT_AVATAR)
        eq_(gravatar_url, profile_avatar(self.u))

    def test_profile_avatar_anonymous(self):
        email_hash = '00000000000000000000000000000000'
        gravatar_url = '//www.gravatar.com/avatar/%s?s=48&d=%s' % (
            email_hash, settings.STATIC_URL + settings.DEFAULT_AVATAR)
        eq_(gravatar_url, profile_avatar(AnonymousUser()))

    def test_profile_avatar(self):
        profile(user=self.u, avatar='images/foo.png')
        email_hash = hashlib.md5(self.u.email.lower()).hexdigest()
        gravatar_url = '//www.gravatar.com/avatar/%s?s=48&d=%s' % (
            email_hash, settings.MEDIA_URL + 'images/foo.png')
        eq_(gravatar_url, profile_avatar(self.u))

    def test_public_email(self):
        eq_(u'<span class="email">'
             '&#109;&#101;&#64;&#100;&#111;&#109;&#97;&#105;&#110;&#46;&#99;'
             '&#111;&#109;</span>', public_email('me@domain.com'))
        eq_(u'<span class="email">'
             '&#110;&#111;&#116;&#46;&#97;&#110;&#46;&#101;&#109;&#97;&#105;'
             '&#108;</span>', public_email('not.an.email'))

    def test_display_name(self):
        eq_(u'testuser', display_name(self.u))
        p = profile(user=self.u, name=u'Test User')
        eq_(u'Test User', display_name(self.u))

    def test_user_list(self):
        User.objects.create(pk=300000, username='testuser2')
        User.objects.create(pk=400000, username='testuser3')
        users = User.objects.all()
        list = user_list(users)
        assert isinstance(list, Markup)
        fragment = pq(list)
        eq_(3, len(fragment('a')))
        a = fragment('a')[1]
        assert a.attrib['href'].endswith('400000')
        eq_('testuser3', a.text)
