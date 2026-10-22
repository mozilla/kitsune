import os
import tempfile
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.utils import timezone
from parameterized import parameterized

from kitsune.products.models import CuratedBlock
from kitsune.products.tests import (
    CuratedBlockFactory,
    CuratedBlockItemFactory,
    ProductFactory,
    TopicFactory,
    make_article,
)
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.wiki.models import Document
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory, RedirectRevisionFactory

Kind = CuratedBlock.Kind
Variant = CuratedBlock.Variant


def make_translation(article, locale="de", **fields):
    translation = DocumentFactory(parent=article, locale=locale, **fields)
    ApprovedRevisionFactory(document=translation, based_on=article.current_revision)
    return translation


def make_solved_question(product, topic, votes=0, **fields):
    question = QuestionFactory(product=product, topic=topic, num_votes_past_week=votes, **fields)
    question.solution = AnswerFactory(question=question)
    question.save()
    return question


def archive(article):
    Document.objects.filter(pk=article.pk).update(is_archived=True)


def drop_from_product(article):
    article.products.clear()


def restrict(article):
    article.restrict_to_groups.add(Group.objects.create(name="restricted"))


def edit_block(block):
    block.message = "Changed"
    block.save()


def add_item(block):
    CuratedBlockItemFactory(block=block, document=make_article(block.product), position=9)


def delete_item(block):
    block.items.get().delete()


def delete_block(block):
    block.delete()


EXCLUDED_QUESTIONS = [
    ("unsolved", lambda product, topic: QuestionFactory(product=product, topic=topic)),
    ("spam", lambda product, topic: make_solved_question(product, topic, is_spam=True)),
    ("archived", lambda product, topic: make_solved_question(product, topic, is_archived=True)),
    ("locked", lambda product, topic: make_solved_question(product, topic, is_locked=True)),
    ("other_locale", lambda product, topic: make_solved_question(product, topic, locale="de")),
    ("other_product", lambda product, topic: make_solved_question(ProductFactory(), topic)),
    (
        "other_topic",
        lambda product, topic: make_solved_question(product, TopicFactory(products=[product])),
    ),
]


class CuratedBlockTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.product = ProductFactory()
        self.topic = TopicFactory(products=[self.product])
        self.subtopic = TopicFactory(parent=self.topic, products=[self.product])

    def block(self, kind, variant, targets=(), topic=None, **fields):
        block = CuratedBlockFactory(
            product=self.product, topic=topic or self.topic, kind=kind, variant=variant, **fields
        )
        field = "question" if kind == Kind.QUESTIONS else "document"
        # Created back to front so the item order has to come from `position`, not from the ids.
        for position, target in reversed(list(enumerate(targets))):
            CuratedBlockItemFactory(block=block, position=position, **{field: target})
        return block

    def page(self, subtopic=None, locale="en-US"):
        return CuratedBlock.objects.for_page(self.product, self.topic, subtopic, locale)

    def automatic_block(self, topic=None):
        return self.block(Kind.QUESTIONS, Variant.AUTOMATIC, topic=topic)


class ForPageTests(CuratedBlockTestCase):
    def test_blocks_come_in_a_fixed_order_with_the_template_shape(self):
        articles = [make_article(self.product) for _ in range(2)]
        questions = [make_solved_question(self.product, self.topic) for _ in range(2)]
        self.block(Kind.QUESTIONS, Variant.MANUAL, targets=questions)
        self.block(Kind.ARTICLES, Variant.FEATURED, targets=articles)
        self.block(Kind.CALLOUT, Variant.IMPORTANT, targets=articles[:1], message="Back up first.")

        callout, cards, forum = self.page()

        self.assertEqual(
            callout,
            {
                "kind": "callout",
                "variant": "important",
                "message": "Back up first.",
                "items": [
                    {
                        "url": articles[0].get_absolute_url(),
                        "title": articles[0].title,
                        "summary": articles[0].current_revision.summary,
                        "english": False,
                        "source_id": articles[0].pk,
                    }
                ],
            },
        )
        self.assertEqual((cards["kind"], cards["variant"]), ("articles", "featured"))
        self.assertEqual([item["title"] for item in cards["items"]], [a.title for a in articles])
        self.assertEqual(forum["kind"], "questions")
        self.assertEqual(
            forum["items"][0],
            {
                "url": f"/en-US/questions/{questions[0].pk}",
                "title": questions[0].title,
                "solved": True,
                "replies": 1,
            },
        )

    def test_subtopic_block_replaces_the_parents_of_the_same_kind(self):
        articles = [make_article(self.product) for _ in range(2)]
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, message="Parent")
        self.block(Kind.ARTICLES, Variant.NUMBERED, targets=articles)
        self.block(Kind.CALLOUT, Variant.IMPORTANT, message="Subtopic", topic=self.subtopic)

        on_subtopic = self.page(self.subtopic)
        on_parent = self.page()

        self.assertEqual(
            [(b["kind"], b["message"]) for b in on_subtopic],
            [("callout", "Subtopic"), ("articles", "")],
        )
        self.assertEqual(
            [(b["kind"], b["message"]) for b in on_parent],
            [("callout", "Parent"), ("articles", "")],
        )

    @parameterized.expand(
        [
            ("past", timedelta(hours=-1), False),
            ("future", timedelta(hours=1), True),
            ("none", None, True),
        ]
    )
    def test_show_until(self, _name, offset, is_shown):
        show_until = timezone.now() + offset if offset else None
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, show_until=show_until)

        self.assertEqual(len(self.page()), int(is_shown))

    def test_expired_subtopic_block_falls_back_to_the_parents(self):
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, message="Parent")
        self.block(
            Kind.CALLOUT,
            Variant.IMPORTANT,
            message="Subtopic",
            topic=self.subtopic,
            show_until=timezone.now() - timedelta(hours=1),
        )

        self.assertEqual([b["message"] for b in self.page(self.subtopic)], ["Parent"])

    def test_blocks_of_other_products_and_topics_are_ignored(self):
        CuratedBlockFactory()
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, topic=TopicFactory(products=[self.product]))

        self.assertEqual(self.page(), [])

    def test_blocks_below_two_items_are_hidden_except_callouts(self):
        gone = make_article(self.product, is_archived=True)
        kept = make_article(self.product)
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, targets=[gone])
        self.block(Kind.ARTICLES, Variant.NUMBERED, targets=[kept, gone])
        self.block(
            Kind.QUESTIONS,
            Variant.MANUAL,
            targets=[
                make_solved_question(self.product, self.topic),
                make_solved_question(self.product, self.topic, is_spam=True),
            ],
        )

        (callout,) = self.page()

        self.assertEqual((callout["kind"], callout["items"]), ("callout", []))

    def test_subtopic_block_hidden_by_the_threshold_falls_back_to_the_parents(self):
        parent_questions = [
            make_solved_question(self.product, self.topic, locale="de") for _ in range(2)
        ]
        english_questions = [make_solved_question(self.product, self.subtopic) for _ in range(2)]
        self.block(Kind.QUESTIONS, Variant.MANUAL, targets=parent_questions)
        self.block(Kind.QUESTIONS, Variant.MANUAL, targets=english_questions, topic=self.subtopic)

        (german,) = self.page(self.subtopic, locale="de")
        (english,) = self.page(self.subtopic)

        self.assertEqual(
            [item["title"] for item in german["items"]], [q.title for q in parent_questions]
        )
        self.assertEqual(
            [item["title"] for item in english["items"]], [q.title for q in english_questions]
        )


class ArticleResolutionTests(CuratedBlockTestCase):
    @parameterized.expand(
        [
            ("translated", make_translation, True),
            ("untranslated", lambda article: None, False),
            (
                "no_current_revision",
                lambda article: DocumentFactory(parent=article, locale="de"),
                False,
            ),
            (
                "redirect",
                lambda article: (
                    RedirectRevisionFactory(
                        document__parent=article, document__locale="de"
                    ).document
                ),
                False,
            ),
        ]
    )
    def test_articles_resolve_to_the_readers_locale(self, _name, translate, is_translated):
        article = make_article(self.product)
        translation = translate(article)
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, targets=[article])

        (callout,) = self.page(locale="de")

        if is_translated:
            expected = {
                "url": translation.get_absolute_url(),
                "title": translation.title,
                "summary": translation.current_revision.summary,
                "english": False,
                "source_id": article.pk,
            }
        else:
            expected = {
                "url": f"/de/kb/{article.slug}",
                "title": article.title,
                "summary": article.current_revision.summary,
                "english": True,
                "source_id": article.pk,
            }
        self.assertEqual(callout["items"], [expected])

    @parameterized.expand(
        [
            ("archived", archive),
            ("removed_from_product", drop_from_product),
            ("restricted", restrict),
            (
                "not_english",
                lambda article: Document.objects.filter(pk=article.pk).update(locale="de"),
            ),
        ]
    )
    def test_articles_that_are_no_longer_eligible_are_dropped(self, _name, make_ineligible):
        kept = make_article(self.product)
        dropped = make_article(self.product)
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, targets=[dropped, kept])
        make_ineligible(dropped)

        (callout,) = self.page()

        self.assertEqual([item["title"] for item in callout["items"]], [kept.title])


class QuestionResolutionTests(CuratedBlockTestCase):
    def test_manual_questions_show_in_their_own_locale(self):
        questions = [
            make_solved_question(self.product, self.topic, locale="de"),
            QuestionFactory(product=self.product, topic=self.topic, locale="de"),
        ]
        self.block(Kind.QUESTIONS, Variant.MANUAL, targets=questions)

        (block,) = self.page(locale="de")

        self.assertEqual(
            [(item["url"], item["solved"]) for item in block["items"]],
            [
                (f"/de/questions/{questions[0].pk}", True),
                (f"/de/questions/{questions[1].pk}", False),
            ],
        )

    @parameterized.expand(
        [
            ("other_locale", {"locale": "de"}),
            ("spam", {"is_spam": True}),
            ("archived", {"is_archived": True}),
        ]
    )
    def test_manual_questions_that_no_longer_qualify_are_dropped(self, _name, fields):
        kept = [make_solved_question(self.product, self.topic) for _ in range(2)]
        dropped = make_solved_question(self.product, self.topic, **fields)
        self.block(Kind.QUESTIONS, Variant.MANUAL, targets=[dropped, *kept])

        (block,) = self.page()

        self.assertEqual([item["title"] for item in block["items"]], [q.title for q in kept])


class AutomaticQuestionTests(CuratedBlockTestCase):
    def titles(self, blocks):
        (block,) = blocks
        return [item["title"] for item in block["items"]]

    def test_top_four_are_ranked_by_votes_with_newest_first_on_ties(self):
        questions = [
            make_solved_question(self.product, self.topic, votes=votes)
            for votes in (3, 9, 9, 1, 7, 5)
        ]
        self.automatic_block()

        expected = [questions[i].title for i in (2, 1, 4, 5)]
        self.assertEqual(self.titles(self.page()), expected)

    @parameterized.expand(EXCLUDED_QUESTIONS)
    def test_questions_that_do_not_qualify_are_excluded(self, _name, make_excluded):
        kept = [make_solved_question(self.product, self.topic, votes=votes) for votes in (2, 1)]
        make_excluded(self.product, self.topic)
        self.automatic_block()

        self.assertEqual(self.titles(self.page()), [q.title for q in kept])

    def test_fewer_than_two_questions_hide_the_block(self):
        make_solved_question(self.product, self.topic)
        self.automatic_block()

        self.assertEqual(self.page(), [])

    def test_a_parent_block_includes_subtopic_questions_on_every_tab(self):
        in_topic = make_solved_question(self.product, self.topic, votes=1)
        in_subtopic = make_solved_question(self.product, self.subtopic, votes=2)
        self.automatic_block()

        expected = [in_subtopic.title, in_topic.title]
        self.assertEqual(self.titles(self.page()), expected)
        self.assertEqual(self.titles(self.page(self.subtopic)), expected)

    def test_a_subtopic_block_only_has_its_own_questions(self):
        make_solved_question(self.product, self.topic)
        own = [make_solved_question(self.product, self.subtopic) for _ in range(2)]
        self.automatic_block(topic=self.subtopic)

        self.assertEqual(self.titles(self.page(self.subtopic)), [q.title for q in reversed(own)])
        self.assertEqual(self.page(), [])


class CachingTests(CuratedBlockTestCase):
    def test_second_render_is_served_from_the_cache(self):
        articles = [make_article(self.product) for _ in range(2)]
        for _ in range(2):
            make_solved_question(self.product, self.topic, locale="de")
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, targets=articles[:1])
        self.block(Kind.ARTICLES, Variant.NUMBERED, targets=articles)
        self.automatic_block()
        first = self.page(self.subtopic, locale="de")

        with self.assertNumQueries(0):
            second = self.page(self.subtopic, locale="de")

        self.assertEqual(first, second)
        self.assertEqual([len(block["items"]) for block in second], [1, 2, 2])

    def test_show_until_is_checked_after_the_cache_read(self):
        show_until = timezone.now() + timedelta(hours=1)
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, show_until=show_until)
        self.assertEqual(len(self.page()), 1)

        with (
            mock.patch("django.utils.timezone.now", return_value=show_until + timedelta(hours=1)),
            self.assertNumQueries(0),
        ):
            self.assertEqual(self.page(), [])

    @parameterized.expand(
        [
            ("block_saved", edit_block),
            ("item_added", add_item),
            ("item_deleted", delete_item),
            ("block_deleted", delete_block),
        ]
    )
    def test_saving_or_deleting_a_block_or_its_items_clears_its_cache(self, _name, change):
        block = self.block(
            Kind.CALLOUT, Variant.GOOD_TO_KNOW, targets=[make_article(self.product)]
        )
        pages = [(None, "en-US"), (self.subtopic, "de")]
        before = [self.page(*page) for page in pages]
        elsewhere = CuratedBlockFactory()
        elsewhere_args = (elsewhere.product, elsewhere.topic, None, "en-US")
        elsewhere_page = CuratedBlock.objects.for_page(*elsewhere_args)

        with self.captureOnCommitCallbacks(execute=True):
            change(block)

        for page, old in zip(pages, before, strict=True):
            self.assertNotEqual(self.page(*page), old)
        with self.assertNumQueries(0):
            self.assertEqual(CuratedBlock.objects.for_page(*elsewhere_args), elsewhere_page)

    def test_cache_is_not_cleared_before_the_transaction_commits(self):
        block = self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, message="Old")
        self.page()

        block.message = "New"
        block.save()

        self.assertEqual(self.page()[0]["message"], "Old")

    def test_automatic_picks_are_not_cleared_by_block_changes(self):
        questions = [make_solved_question(self.product, self.topic, votes=1) for _ in range(2)]
        block = self.automatic_block()
        self.page()
        make_solved_question(self.product, self.topic, votes=9)

        with self.captureOnCommitCallbacks(execute=True):
            block.save()

        self.assertEqual(
            [item["title"] for item in self.page()[0]["items"]], [q.title for q in questions][::-1]
        )


class DbLocalizeTests(CuratedBlockTestCase):
    def test_callout_messages_are_exported_for_translation(self):
        self.block(Kind.CALLOUT, Variant.GOOD_TO_KNOW, message="Restart Firefox first.")

        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "db_strings.py")
            call_command("extract_db", "--output-file", path)
            with open(path, encoding="utf-8") as exported:
                content = exported.read()

        self.assertIn(
            'pgettext("DB: products.CuratedBlock.message", """Restart Firefox first.""")', content
        )
