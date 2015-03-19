from datetime import datetime, date, timedelta

from django.contrib.auth.models import User

from nose.tools import eq_

from kitsune.community.utils import (
    top_contributors_kb, top_contributors_l10n, top_contributors_aoa,
    top_contributors_questions)
from kitsune.customercare.tests import reply
from kitsune.products.tests import product
from kitsune.questions.tests import answer
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.users.tests import user, profile
from kitsune.wiki.tests import document, revision


class TopContributorTests(ElasticTestCase):
    client_class = LocalizingClient

    def test_top_contributors_kb(self):
        d = document(locale='en-US', save=True)
        r1 = revision(document=d, save=True)
        revision(document=d, creator=r1.creator, save=True)
        revision(document=d, save=True)
        r4 = revision(document=d, created=date.today()-timedelta(days=91),
                      save=True)

        for u in User.objects.all():
            profile(user=u)

        self.refresh()

        # By default, we should only get 2 top contributors back.
        top, _ = top_contributors_kb()
        eq_(2, len(top))
        assert r4.creator_id not in [u['term'] for u in top]
        eq_(r1.creator_id, top[0]['term'])

        # If we specify an older start, then we get all 3.
        top, _ = top_contributors_kb(start=date.today() - timedelta(days=92))
        eq_(3, len(top))

        # If we also specify an older end date, we only get the creator for
        # the older revision.
        top, _ = top_contributors_kb(
            start=date.today() - timedelta(days=92),
            end=date.today() - timedelta(days=1))
        eq_(1, len(top))
        eq_(r4.creator_id, top[0]['term'])

    def test_top_contributors_l10n(self):
        d = document(locale='es', save=True)
        es1 = revision(document=d, save=True)
        es1 = revision(document=d, creator=es1.creator, save=True)
        revision(document=d, save=True)
        es4 = revision(document=d, created=date.today() - timedelta(days=91),
                       save=True)

        d = document(locale='de', save=True)
        de1 = revision(document=d, save=True)
        revision(document=d, creator=de1.creator, save=True)

        d = document(locale='en-US', save=True)
        revision(document=d, save=True)
        revision(document=d, save=True)

        for u in User.objects.all():
            profile(user=u)

        self.refresh()

        # By default, we should only get 2 top contributors back for 'es'.
        top, _ = top_contributors_l10n(locale='es')
        eq_(2, len(top))
        assert es4.creator_id not in [u['term'] for u in top]
        eq_(es1.creator_id, top[0]['term'])

        # By default, we should only get 1 top contributors back for 'de'.
        top, _ = top_contributors_l10n(locale='de')
        eq_(1, len(top))
        eq_(de1.creator_id, top[0]['term'])

        # If no locale is passed, it includes all locales except en-US.
        top, _ = top_contributors_l10n()
        eq_(3, len(top))

    def test_top_contributors_aoa(self):
        r1 = reply(user=user(save=True), save=True)
        reply(user=r1.user, save=True)
        reply(user=user(save=True), save=True)
        r4 = reply(user=user(save=True),
                   created=date.today() - timedelta(days=91),
                   save=True)

        for u in User.objects.all():
            profile(user=u)

        self.refresh()

        # By default, we should only get 2 top contributors back.
        top, _ = top_contributors_aoa()
        eq_(2, len(top))
        assert r4.user_id not in [u['term'] for u in top]
        eq_(r1.user_id, top[0]['term'])

    def test_top_contributors_questions(self):
        firefox = product(slug='firefox', save=True)
        fxos = product(slug='firefox-os', save=True)
        a1 = answer(save=True)
        a1.question.product = firefox
        a1.question.save()
        answer(creator=a1.creator, save=True)
        a3 = answer(save=True)
        a3.question.product = fxos
        a3.question.save()
        a4 = answer(created=datetime.now()-timedelta(days=91),
                    save=True)
        a5 = answer(creator=a1.creator, save=True)
        a5.question.product = fxos
        a5.question.save()
        answer(creator=a4.question.creator, question=a4.question, save=True)

        for u in User.objects.all():
            profile(user=u)

        self.refresh()

        # By default, we should only get 2 top contributors back.
        top, _ = top_contributors_questions()
        eq_(2, len(top))
        assert a4.creator_id not in [u['term'] for u in top]
        eq_(a1.creator_id, top[0]['term'])

        # Verify, filtering of Firefox questions only.
        top, _ = top_contributors_questions(product=firefox.slug)
        eq_(1, len(top))
        eq_(a1.creator_id, top[0]['term'])
        top, _ = top_contributors_questions(product=fxos.slug)
        eq_(2, len(top))
