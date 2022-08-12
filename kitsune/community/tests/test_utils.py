from datetime import date, datetime, timedelta

from kitsune.community.utils import (
    top_contributors_kb,
    top_contributors_l10n,
    top_contributors_questions,
)
from kitsune.products.tests import ProductFactory
from kitsune.questions.tests import AnswerFactory
from kitsune.search.tests import Elastic7TestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.users.tests import ContributorFactory
from kitsune.wiki.tests import DocumentFactory, RevisionFactory


class TopContributorTests(Elastic7TestCase):
    client_class = LocalizingClient
    search_tests = True

    def test_top_contributors_kb(self):
        d = DocumentFactory(locale="en-US")
        r1 = RevisionFactory(document=d)
        RevisionFactory(document=d, creator=r1.creator)
        RevisionFactory(document=d)
        r4 = RevisionFactory(document=d, created=date.today() - timedelta(days=91))

        # By default, we should only get 2 top contributors back.
        top, _ = top_contributors_kb()
        self.assertEqual(2, len(top))
        assert r4.creator_id not in [u["term"] for u in top]
        self.assertEqual(r1.creator_id, top[0]["term"])

        # If we specify an older start, then we get all 3.
        top, _ = top_contributors_kb(start=date.today() - timedelta(days=92))
        self.assertEqual(3, len(top))

        # If we also specify an older end date, we only get the creator for
        # the older revision.
        top, _ = top_contributors_kb(
            start=date.today() - timedelta(days=92), end=date.today() - timedelta(days=1)
        )
        self.assertEqual(1, len(top))
        self.assertEqual(r4.creator_id, top[0]["term"])

    def test_top_contributors_l10n(self):
        d = DocumentFactory(locale="es")
        es1 = RevisionFactory(document=d)
        RevisionFactory(document=d, creator=es1.creator)
        RevisionFactory(document=d)
        es4 = RevisionFactory(document=d, created=date.today() - timedelta(days=91))

        d = DocumentFactory(locale="de")
        de1 = RevisionFactory(document=d)
        RevisionFactory(document=d, creator=de1.creator)

        d = DocumentFactory(locale="en-US")
        RevisionFactory(document=d)
        RevisionFactory(document=d)

        # By default, we should only get 2 top contributors back for 'es'.
        top, _ = top_contributors_l10n(locale="es")
        self.assertEqual(2, len(top))
        assert es4.creator_id not in [u["term"] for u in top]
        self.assertEqual(es1.creator_id, top[0]["term"])

        # By default, we should only get 1 top contributors back for 'de'.
        top, _ = top_contributors_l10n(locale="de")
        self.assertEqual(1, len(top))
        self.assertEqual(de1.creator_id, top[0]["term"])

        # If no locale is passed, it includes all locales except en-US.
        top, _ = top_contributors_l10n()
        self.assertEqual(3, len(top))

    def test_top_contributors_questions(self):
        firefox = ProductFactory(slug="firefox")
        fxos = ProductFactory(slug="firefox-os")
        a1 = AnswerFactory(question__product=firefox, creator=ContributorFactory())
        AnswerFactory(creator=a1.creator)
        AnswerFactory(question__product=fxos, creator=ContributorFactory())
        a4 = AnswerFactory(
            created=datetime.now() - timedelta(days=91), creator=ContributorFactory()
        )
        AnswerFactory(creator=a1.creator, question__product=fxos)
        AnswerFactory(creator=a4.question.creator, question=a4.question)

        # By default, we should only get 2 top contributors back.
        top, _ = top_contributors_questions()
        self.assertEqual(2, len(top))
        assert a4.creator_id not in [u["term"] for u in top]
        self.assertEqual(str(a1.creator_id), top[0]["term"])

        # Verify, filtering of Firefox questions only.
        top, _ = top_contributors_questions(product=firefox)
        self.assertEqual(1, len(top))
        self.assertEqual(str(a1.creator_id), top[0]["term"])
        top, _ = top_contributors_questions(product=fxos)
        self.assertEqual(2, len(top))
