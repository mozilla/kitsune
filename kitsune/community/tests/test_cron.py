from datetime import datetime, timedelta

from unittest import mock
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.management import call_command
from django.test.utils import override_settings
from nose.tools import eq_

from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import TestCase, attrs_eq
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import DocumentFactory, RevisionFactory


class WelcomeEmailsTests(TestCase):
    @mock.patch.object(Site.objects, "get_current")
    def test_answer_welcome_email(self, get_current):
        get_current.return_value.domain = "testserver"

        u1 = UserFactory()
        u2 = UserFactory(profile__first_answer_email_sent=True)
        u3 = UserFactory()

        two_days = datetime.now() - timedelta(hours=48)

        q = QuestionFactory(creator=u1)
        AnswerFactory(question=q, creator=u1, created=two_days)
        AnswerFactory(question=q, creator=u2, created=two_days)
        AnswerFactory(question=q, creator=u3, created=two_days)

        # Clear out the notifications that were sent
        mail.outbox = []
        # Send email(s) for welcome messages
        call_command("send_welcome_emails")

        # There should be an email for u3 only.
        # u1 was the asker, and so did not make a contribution.
        # u2 has already recieved the email

        eq_(len(mail.outbox), 1)
        attrs_eq(mail.outbox[0], to=[u3.email])

        # Links should be locale-neutral
        assert "en-US" not in mail.outbox[0].body

        # Check that no links used the wrong host.
        assert "support.mozilla.org" not in mail.outbox[0].body
        # Check that one link used the right host.
        assert "https://testserver/forums/contributors" in mail.outbox[0].body
        assert (
            "The community forum is at https://testserver/forums/contributors ."
            in mail.outbox[0].body
        )
        # Assumption: links will be done consistently, and so this is enough testing.

        # u3's flag should now be set.
        u3 = User.objects.get(id=u3.id)
        eq_(u3.profile.first_answer_email_sent, True)

    @override_settings(WIKI_DEFAULT_LANGUAGE="en-US")
    @mock.patch.object(Site.objects, "get_current")
    def test_l10n_welcome_email(self, get_current):
        get_current.return_value.domain = "testserver"

        u1 = UserFactory()
        u2 = UserFactory(profile__first_l10n_email_sent=True)

        two_days = datetime.now() - timedelta(hours=48)

        d = DocumentFactory(locale="ru")
        RevisionFactory(document=d, creator=u1, created=two_days)
        RevisionFactory(document=d, creator=u2, created=two_days)

        # Clear out the notifications that were sent
        mail.outbox = []
        # Send email(s) for welcome messages
        call_command("send_welcome_emails")

        # There should be an email for u1 only.
        # u2 has already recieved the email

        eq_(len(mail.outbox), 1)
        attrs_eq(mail.outbox[0], to=[u1.email])

        # Links should be locale-neutral
        assert "en-US" not in mail.outbox[0].body

        # Check that no links used the wrong host.
        assert "support.mozilla.org" not in mail.outbox[0].body
        # Check that one link used the right host.
        assert "https://testserver/kb/locales" in mail.outbox[0].body
        # Assumption: links will be done consistently, and so this is enough testing.

        # u3's flag should now be set.
        u1 = User.objects.get(id=u1.id)
        eq_(u1.profile.first_l10n_email_sent, True)
