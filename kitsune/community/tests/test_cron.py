from datetime import datetime, timedelta

from django.core import mail
from django.contrib.auth.models import User
from django.test.utils import override_settings

from nose.tools import eq_

from kitsune.community import cron
from kitsune.questions.tests import answer, question
from kitsune.sumo.tests import attrs_eq, TestCase
from kitsune.users.tests import profile
from kitsune.wiki.tests import document, revision


class WelcomeEmailsTests(TestCase):

    def test_answer_welcome_email(self):
        u1 = profile().user
        u2 = profile(first_answer_email_sent=True).user
        u3 = profile().user

        two_days = datetime.now() - timedelta(hours=48)

        q = question(creator=u1, save=True)
        answer(question=q, creator=u1, created=two_days, save=True)
        answer(question=q, creator=u2, created=two_days, save=True)
        answer(question=q, creator=u3, created=two_days, save=True)

        # Clear out the notifications that were sent
        mail.outbox = []
        # Send email(s) for welcome messages
        cron.send_welcome_emails()

        # There should be an email for u3 only.
        # u1 was the asker, and so did not make a contribution.
        # u2 has already recieved the email

        eq_(len(mail.outbox), 1)
        attrs_eq(mail.outbox[0], to=[u3.email])

        # u3's flag should now be set.
        u3 = User.objects.get(id=u3.id)
        eq_(u3.profile.first_answer_email_sent, True)

    @override_settings(WIKI_DEFAULT_LANGUAGE='en-US')
    def test_l10n_welcome_email(self):
        u1 = profile().user
        u2 = profile(first_l10n_email_sent=True).user

        two_days = datetime.now() - timedelta(hours=48)

        d = document(locale='ru', save=True)
        revision(document=d, creator=u1, created=two_days, save=True)
        revision(document=d, creator=u2, created=two_days, save=True)

        # Clear out the notifications that were sent
        mail.outbox = []
        # Send email(s) for welcome messages
        cron.send_welcome_emails()

        # There should be an email for u1 only.
        # u2 has already recieved the email

        eq_(len(mail.outbox), 1)
        attrs_eq(mail.outbox[0], to=[u1.email])

        # u3's flag should now be set.
        u1 = User.objects.get(id=u1.id)
        eq_(u1.profile.first_l10n_email_sent, True)
