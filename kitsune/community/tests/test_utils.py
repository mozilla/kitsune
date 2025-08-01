from datetime import date, datetime, timedelta

from kitsune.community.utils import (
    deleted_contribution_metrics_by_contributor,
    num_deleted_contributions,
    top_contributors_kb,
    top_contributors_l10n,
    top_contributors_questions,
)
from kitsune.products.tests import ProductFactory
from kitsune.questions.models import Answer
from kitsune.questions.tests import AnswerFactory
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import ContributorFactory
from kitsune.wiki.models import Document, Revision
from kitsune.wiki.tests import RevisionFactory


class TopContributorTests(ElasticTestCase):
    search_tests = True

    def test_top_contributors_kb(self):
        mobile = ProductFactory(slug="ios")
        firefox = ProductFactory(slug="firefox")

        r1 = RevisionFactory(document__products=[mobile, firefox])
        RevisionFactory(creator=r1.creator, document__products=[mobile])
        r3 = RevisionFactory(document__products=[mobile])
        r4 = RevisionFactory(
            created=date.today() - timedelta(days=91), document__products=[firefox]
        )
        r5 = RevisionFactory(creator=r1.creator, document__products=[firefox])
        r6 = RevisionFactory(creator=r3.creator, document__products=[mobile])
        r7 = RevisionFactory(document__products=[mobile])

        # Let's delete some revisions to ensure we're properly including deleted contributions.
        r5.delete()
        r6.delete()
        r7.delete()

        # Using the defaults, we should only get 3 top contributors back.
        top, total = top_contributors_kb()
        self.assertEqual(total, 3)
        self.assertEqual(3, len(top))
        self.assertEqual(top[0]["term"], r1.creator_id)
        self.assertEqual(top[0]["count"], 3)
        self.assertEqual(top[1]["term"], r3.creator_id)
        self.assertEqual(top[1]["count"], 2)
        self.assertEqual(top[2]["term"], r7.creator_id)
        self.assertEqual(top[2]["count"], 1)

        # Filter by start and the firefox product.
        top, total = top_contributors_kb(start=date.today() - timedelta(days=92), product=firefox)
        self.assertEqual(total, 2)
        self.assertEqual(2, len(top))
        self.assertEqual(top[0]["term"], r1.creator_id)
        self.assertEqual(top[0]["count"], 2)
        self.assertEqual(top[1]["term"], r4.creator_id)
        self.assertEqual(top[1]["count"], 1)

        # Filter by the mobile product.
        top, total = top_contributors_kb(product=mobile)
        self.assertEqual(total, 3)
        self.assertEqual(3, len(top))
        self.assertEqual(top[0]["term"], r1.creator_id)
        self.assertEqual(top[0]["count"], 2)
        self.assertEqual(top[1]["term"], r3.creator_id)
        self.assertEqual(top[1]["count"], 2)
        self.assertEqual(top[2]["term"], r7.creator_id)
        self.assertEqual(top[2]["count"], 1)

        # If we specify an older start, then we get all 4.
        top, total = top_contributors_kb(start=date.today() - timedelta(days=92))
        self.assertEqual(total, 4)
        self.assertEqual(4, len(top))
        self.assertEqual(top[0]["term"], r1.creator_id)
        self.assertEqual(top[0]["count"], 3)
        self.assertEqual(top[1]["term"], r3.creator_id)
        self.assertEqual(top[1]["count"], 2)
        self.assertEqual(top[2]["term"], r4.creator_id)
        self.assertEqual(top[2]["count"], 1)
        self.assertEqual(top[3]["term"], r7.creator_id)
        self.assertEqual(top[3]["count"], 1)

        # If we also specify an older end date, we only get the creator for
        # the older revision.
        top, total = top_contributors_kb(
            start=date.today() - timedelta(days=92), end=date.today() - timedelta(days=1)
        )
        self.assertEqual(total, 1)
        self.assertEqual(1, len(top))
        self.assertEqual(top[0]["term"], r4.creator_id)
        self.assertEqual(top[0]["count"], 1)

    def test_top_contributors_l10n(self):
        es1 = RevisionFactory(document__locale="es")
        RevisionFactory(document__locale="es", creator=es1.creator)
        es3 = RevisionFactory(document__locale="es")
        es4 = RevisionFactory(document__locale="es", created=date.today() - timedelta(days=91))
        es5 = RevisionFactory(document__locale="es", creator=es3.creator)

        de1 = RevisionFactory(document__locale="de")
        RevisionFactory(document__locale="de", creator=de1.creator)
        de3 = RevisionFactory(document__locale="de", creator=de1.creator)
        de4 = RevisionFactory(document__locale="de", creator=de1.creator)

        RevisionFactory(document__locale="en-US")
        RevisionFactory(document__locale="en-US")

        # Let's delete some revisions to ensure we're properly including deleted contributions.
        es3.delete()
        es4.delete()
        es5.delete()
        de3.delete()
        de4.delete()

        # By default, we should only get 2 top contributors back for 'es'.
        top, total = top_contributors_l10n(locale="es")
        self.assertEqual(total, 2)
        self.assertEqual(2, len(top))
        self.assertEqual(top[0]["term"], es1.creator_id)
        self.assertEqual(top[0]["count"], 2)
        self.assertEqual(top[1]["term"], es3.creator_id)
        self.assertEqual(top[1]["count"], 2)

        # By default, we should only get 1 top contributors back for 'de'.
        top, total = top_contributors_l10n(locale="de")
        self.assertEqual(total, 1)
        self.assertEqual(1, len(top))
        self.assertEqual(top[0]["term"], de1.creator_id)
        self.assertEqual(top[0]["count"], 4)

        # If no locale is passed, it includes all locales except en-US.
        top, total = top_contributors_l10n()
        self.assertEqual(total, 3)
        self.assertEqual(3, len(top))
        self.assertEqual(top[0]["term"], de1.creator_id)
        self.assertEqual(top[0]["count"], 4)
        self.assertEqual(top[1]["term"], es1.creator_id)
        self.assertEqual(top[1]["count"], 2)
        self.assertEqual(top[2]["term"], es3.creator_id)
        self.assertEqual(top[2]["count"], 2)

    def test_top_contributors_questions(self):
        firefox = ProductFactory(slug="firefox")
        fxos = ProductFactory(slug="firefox-os")

        a1 = AnswerFactory(
            creator=ContributorFactory(),
            created=datetime.now() - timedelta(days=3),
            question__product=firefox,
        )
        a2 = AnswerFactory(
            creator=a1.creator,
            created=datetime.now() - timedelta(days=2),
            question__product=firefox,
        )
        a3 = AnswerFactory(
            creator=ContributorFactory(),
            question__product=fxos,
        )
        a4 = AnswerFactory(
            creator=ContributorFactory(),
            created=datetime.now() - timedelta(days=91),
            question__product=firefox,
        )
        a5 = AnswerFactory(
            creator=a1.creator,
            created=datetime.now() - timedelta(days=1),
            question__product=fxos,
        )
        a6 = AnswerFactory(
            creator=a4.creator,
            created=datetime.now() - timedelta(days=30),
            question=a4.question,
        )

        # Let's delete some answers to ensure we're properly including deleted contributions.
        a2.delete()
        a5.delete()
        a6.delete()

        # By default, we should get 3 top contributors back.
        top, total = top_contributors_questions()
        self.assertEqual(total, 3)
        self.assertEqual(3, len(top))
        self.assertEqual(top[0]["term"], str(a1.creator_id))
        self.assertEqual(top[0]["count"], 3)
        self.assertEqual(top[0]["user"]["days_since_last_activity"], 1)
        self.assertEqual(top[1]["term"], str(a3.creator_id))
        self.assertEqual(top[1]["count"], 1)
        self.assertEqual(top[1]["user"]["days_since_last_activity"], 0)
        self.assertEqual(top[2]["term"], str(a4.creator_id))
        self.assertEqual(top[2]["count"], 1)
        self.assertEqual(top[2]["user"]["days_since_last_activity"], 30)

        # Verify filtering by product.
        top, total = top_contributors_questions(product=firefox)
        self.assertEqual(total, 2)
        self.assertEqual(2, len(top))
        self.assertEqual(top[0]["term"], str(a1.creator_id))
        self.assertEqual(top[0]["count"], 2)
        self.assertEqual(top[0]["user"]["days_since_last_activity"], 2)
        self.assertEqual(top[1]["term"], str(a4.creator_id))
        self.assertEqual(top[1]["count"], 1)
        self.assertEqual(top[1]["user"]["days_since_last_activity"], 30)

        top, total = top_contributors_questions(product=fxos)
        self.assertEqual(total, 2)
        self.assertEqual(2, len(top))
        self.assertEqual(top[0]["term"], str(a1.creator_id))
        self.assertEqual(top[0]["count"], 1)
        self.assertEqual(top[0]["user"]["days_since_last_activity"], 1)
        self.assertEqual(top[1]["term"], str(a3.creator_id))
        self.assertEqual(top[1]["count"], 1)
        self.assertEqual(top[1]["user"]["days_since_last_activity"], 0)


class DeletedContributionsTests(TestCase):
    def setUp(self):
        self.sumo_bot = Profile.get_sumo_bot()

    def test_for_answers(self):
        mobile = ProductFactory(slug="ios")
        firefox = ProductFactory(slug="firefox")

        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        three_days_ago = now - timedelta(days=3)
        four_days_ago = now - timedelta(days=4)
        five_days_ago = now - timedelta(days=5)

        a1 = AnswerFactory(
            question__product=firefox, created=one_day_ago, creator=ContributorFactory()
        )
        q1 = a1.question
        AnswerFactory(question=q1, created=two_days_ago)
        AnswerFactory(
            question=q1, is_spam=True, created=two_days_ago, creator=ContributorFactory()
        )
        q1.solution = AnswerFactory(question=q1, creator=a1.creator, created=three_days_ago)
        q1.save()
        AnswerFactory(question=q1, creator=self.sumo_bot, created=four_days_ago)
        AnswerFactory(question=q1, created=four_days_ago)

        a2 = AnswerFactory(
            question__product=mobile,
            question__locale="de",
            created=one_day_ago,
            creator=ContributorFactory(),
        )
        q2 = a2.question
        AnswerFactory(question=q2, created=two_days_ago)
        a3 = AnswerFactory(question=q2, created=two_days_ago, creator=ContributorFactory())
        AnswerFactory(
            question=q2, is_spam=True, created=three_days_ago, creator=ContributorFactory()
        )
        AnswerFactory(question=q2, creator=self.sumo_bot, created=four_days_ago)
        AnswerFactory(question=q2, creator=a2.creator, created=four_days_ago)
        AnswerFactory(question=q2, created=four_days_ago)
        q2.solution = AnswerFactory(question=q2, creator=a2.creator, created=five_days_ago)
        q2.save()

        q1.delete()
        q2.delete()

        self.assertEqual(num_deleted_contributions(Answer), 10)
        self.assertEqual(num_deleted_contributions(Answer, contributor=a1.creator), 2)
        self.assertEqual(num_deleted_contributions(Answer, contributor=a2.creator), 3)
        self.assertEqual(num_deleted_contributions(Answer, contributor=a3.creator), 1)
        self.assertEqual(
            num_deleted_contributions(Answer, contributor=a1.creator, products__in=[firefox]), 2
        )
        self.assertEqual(
            num_deleted_contributions(Answer, contributor=a2.creator, products__in=[firefox]), 0
        )
        self.assertEqual(
            num_deleted_contributions(Answer, contributor=a3.creator, products__in=[firefox]), 0
        )
        self.assertEqual(num_deleted_contributions(Answer, metadata__is_solution=True), 2)
        self.assertEqual(num_deleted_contributions(Answer, locale="de"), 6)
        self.assertEqual(num_deleted_contributions(Answer, exclude_locale="en-US"), 6)

        result = deleted_contribution_metrics_by_contributor(
            Answer, limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [
                (a2.creator.id, (3, one_day_ago)),
                (a1.creator.id, (2, one_day_ago)),
                (a3.creator.id, (1, two_days_ago)),
            ],
        )

        result = deleted_contribution_metrics_by_contributor(
            Answer, max_results=2, limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [(a2.creator.id, (3, one_day_ago)), (a1.creator.id, (2, one_day_ago))],
        )

        result = deleted_contribution_metrics_by_contributor(
            Answer, products=[mobile], limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [(a2.creator.id, (3, one_day_ago)), (a3.creator.id, (1, two_days_ago))],
        )

        result = deleted_contribution_metrics_by_contributor(
            Answer, products=[firefox], limit_to_contributor_groups=True
        )
        self.assertEqual(list(result.items()), [(a1.creator.id, (2, one_day_ago))])

        result = deleted_contribution_metrics_by_contributor(
            Answer, products=[firefox, mobile], limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [
                (a2.creator.id, (3, one_day_ago)),
                (a1.creator.id, (2, one_day_ago)),
                (a3.creator.id, (1, two_days_ago)),
            ],
        )

        result = deleted_contribution_metrics_by_contributor(
            Answer, locale="de", products=[firefox, mobile], limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [(a2.creator.id, (3, one_day_ago)), (a3.creator.id, (1, two_days_ago))],
        )
        result = deleted_contribution_metrics_by_contributor(
            Answer, locale="en-US", limit_to_contributor_groups=True
        )
        self.assertEqual(list(result.items()), [(a1.creator.id, (2, one_day_ago))])

        result = deleted_contribution_metrics_by_contributor(
            Answer, locale="de", limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [(a2.creator.id, (3, one_day_ago)), (a3.creator.id, (1, two_days_ago))],
        )

        result = deleted_contribution_metrics_by_contributor(
            Answer, start=three_days_ago, limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [
                (a1.creator.id, (2, one_day_ago)),
                (a2.creator.id, (1, one_day_ago)),
                (a3.creator.id, (1, two_days_ago)),
            ],
        )

        result = deleted_contribution_metrics_by_contributor(
            Answer, end=three_days_ago, limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [(a2.creator.id, (2, four_days_ago)), (a1.creator.id, (1, three_days_ago))],
        )

        result = deleted_contribution_metrics_by_contributor(
            Answer, start=three_days_ago, end=two_days_ago, limit_to_contributor_groups=True
        )
        self.assertEqual(
            list(result.items()),
            [(a1.creator.id, (1, three_days_ago)), (a3.creator.id, (1, two_days_ago))],
        )

        # Ensure cascade delete when contributor deleted.
        a1.creator.delete()
        a2.creator.delete()
        a3.creator.delete()
        self.assertFalse(
            deleted_contribution_metrics_by_contributor(Answer, limit_to_contributor_groups=True)
        )

    def test_for_revisions(self):
        rev1 = RevisionFactory(is_approved=True)
        rev2 = RevisionFactory(creator=self.sumo_bot)
        rev3 = RevisionFactory(creator=rev1.creator)
        rev4 = RevisionFactory(
            document__parent=rev1.document, document__locale="de", based_on=rev1
        )
        rev5 = RevisionFactory(
            document__parent=rev3.document, document__locale="it", is_approved=True, based_on=rev3
        )

        # Revs 4 and 5 are deleted via cascade on based_on.
        Revision.objects.filter(id__in=[rev1.id, rev2.id, rev3.id]).delete()

        self.assertEqual(num_deleted_contributions(Revision), 4)
        self.assertEqual(num_deleted_contributions(Revision, locale="de"), 1)
        self.assertEqual(num_deleted_contributions(Revision, locale="it"), 1)
        self.assertEqual(num_deleted_contributions(Revision, exclude_locale="en-US"), 2)
        self.assertEqual(num_deleted_contributions(Revision, contributor=rev1.creator), 2)
        self.assertEqual(num_deleted_contributions(Document, contributor=rev1.creator), 1)
        self.assertEqual(num_deleted_contributions(Document, locale="en-US"), 1)
        self.assertEqual(num_deleted_contributions(Document, locale="it"), 1)
        self.assertEqual(num_deleted_contributions(Document, exclude_locale="en-US"), 1)

        result = deleted_contribution_metrics_by_contributor(Revision)
        self.assertEqual(
            list(result.items()),
            [
                (rev1.creator.id, (2, rev3.created)),
                (rev4.creator.id, (1, rev4.created)),
                (rev5.creator.id, (1, rev5.created)),
            ],
        )

        result = deleted_contribution_metrics_by_contributor(Revision, metadata__is_approved=True)
        self.assertEqual(
            list(result.items()),
            [(rev1.creator.id, (1, rev1.created)), (rev5.creator.id, (1, rev5.created))],
        )

        # Ensure cascade delete when contributor deleted.
        rev1.creator.delete()
        rev4.creator.delete()
        rev5.creator.delete()
        self.assertFalse(deleted_contribution_metrics_by_contributor(Revision))

    def test_for_documents(self):
        rev1 = RevisionFactory(is_approved=True)
        doc = rev1.document
        RevisionFactory(document=doc, creator=self.sumo_bot, is_approved=True)
        rev3 = RevisionFactory(document=doc, creator=rev1.creator, is_approved=True)
        rev4 = RevisionFactory(document=doc, is_approved=True)
        rev5 = RevisionFactory(document=doc, is_approved=True)

        doc.delete()

        self.assertEqual(num_deleted_contributions(Document), 3)
        self.assertEqual(num_deleted_contributions(Document, contributor=rev1.creator), 1)
        self.assertEqual(num_deleted_contributions(Document, locale="en-US"), 3)
        self.assertEqual(num_deleted_contributions(Document, exclude_locale="en-US"), 0)

        result = deleted_contribution_metrics_by_contributor(Document)
        self.assertEqual(
            list(result.items()),
            [
                (rev1.creator.id, (1, rev3.created)),
                (rev4.creator.id, (1, rev4.created)),
                (rev5.creator.id, (1, rev5.created)),
            ],
        )

        result = deleted_contribution_metrics_by_contributor(Document, metadata__title=doc.title)
        self.assertEqual(
            list(result.items()),
            [
                (rev1.creator.id, (1, rev3.created)),
                (rev4.creator.id, (1, rev4.created)),
                (rev5.creator.id, (1, rev5.created)),
            ],
        )

        # Ensure cascade delete when contributor deleted.
        rev1.creator.delete()
        rev4.creator.delete()
        rev5.creator.delete()
        self.assertFalse(deleted_contribution_metrics_by_contributor(Document))
