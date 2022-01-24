# -*- coding: utf-8 -*-
import hashlib

from django.contrib.auth.models import AnonymousUser, User
from jinja2 import Markup
from pyquery import PyQuery as pq

from kitsune.sumo.tests import TestCase
from kitsune.users.templatetags.jinja_helpers import (
    display_name,
    profile_avatar,
    profile_url,
    public_email,
    user_list,
)
from kitsune.users.tests import UserFactory


class HelperTestCase(TestCase):
    def setUp(self):
        super(HelperTestCase, self).setUp()
        self.u = UserFactory()

    def test_profile_url(self):
        self.assertEqual("/user/%s" % self.u.username, profile_url(self.u))

    def test_profile_avatar_default(self):
        email_hash = hashlib.md5(self.u.email.lower().encode()).hexdigest()
        gravatar_url = "https://secure.gravatar.com/avatar/%s?s=200" % (email_hash)
        assert profile_avatar(self.u).startswith(gravatar_url)

    def test_profile_avatar_anonymous(self):
        email_hash = "00000000000000000000000000000000"
        gravatar_url = "https://secure.gravatar.com/avatar/%s?s=200" % (email_hash)
        assert profile_avatar(AnonymousUser()).startswith(gravatar_url)

    def test_profile_avatar(self):
        self.u.profile.avatar = "images/foo.png"
        self.u.profile.save()
        email_hash = hashlib.md5(self.u.email.lower().encode()).hexdigest()
        gravatar_url = "https://secure.gravatar.com/avatar/%s?s=200" % (email_hash)
        assert profile_avatar(self.u).startswith(gravatar_url)

    def test_profile_avatar_unicode(self):
        self.u.email = "rápido@example.com"
        self.u.save()
        gravatar_url = "https://secure.gravatar.com/"
        assert profile_avatar(self.u).startswith(gravatar_url)

    def test_public_email(self):
        self.assertEqual(
            '<span class="email">'
            "&#109;&#101;&#64;&#100;&#111;&#109;&#97;&#105;&#110;&#46;&#99;"
            "&#111;&#109;</span>",
            public_email("me@domain.com"),
        )
        self.assertEqual(
            '<span class="email">'
            "&#110;&#111;&#116;&#46;&#97;&#110;&#46;&#101;&#109;&#97;&#105;"
            "&#108;</span>",
            public_email("not.an.email"),
        )

    def test_display_name(self):
        self.assertEqual(self.u.profile.name, display_name(self.u))
        self.u.profile.name = "Test User"
        self.u.profile.save()
        self.assertEqual("Test User", display_name(self.u))

    def test_display_name_anonymous(self):
        self.assertEqual("", display_name(AnonymousUser()))

    def test_user_list(self):
        UserFactory(username="testuser2")
        UserFactory(username="testuser3")
        users = User.objects.all()
        list = user_list(users)
        assert isinstance(list, Markup)
        fragment = pq(list)
        self.assertEqual(len(users), len(fragment("a")))
        a = fragment("a")[1]
        assert a.attrib["href"].endswith(str(users[1].username))
        self.assertEqual(display_name(users[1]), a.text)
