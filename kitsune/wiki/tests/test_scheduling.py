import json
from datetime import UTC, datetime, timedelta
from itertools import product
from unittest.mock import patch
from zoneinfo import ZoneInfo

from celery.schedules import crontab
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.db import DatabaseError, IntegrityError, transaction
from django.test import RequestFactory, override_settings

from kitsune.celery_beat import PERIODIC_TASKS_ALL
from kitsune.dashboards.readouts import (
    MostVisitedDefaultLanguageReadout,
    MostVisitedTranslationsReadout,
    TemplateReadout,
    UnreviewedReadout,
    kb_overview_rows,
)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory, add_permission
from kitsune.wiki.config import MEDIUM_SIGNIFICANCE
from kitsune.wiki.content_managers import AIContentManager, ManualContentManager
from kitsune.wiki.events import ApproveRevisionInLocaleEvent, ReadyRevisionEvent
from kitsune.wiki.forms import ReviewForm
from kitsune.wiki.models import Document, DraftRevision, Revision, ScheduledRevision
from kitsune.wiki.review import apply_review, release_due_revisions
from kitsune.wiki.tasks import (
    fix_current_revisions,
    release_scheduled_revisions,
    send_weekly_ready_for_review_digest,
)
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DeferredRevisionFactory,
    LocaleFactory,
    RevisionFactory,
    ScheduledRevisionFactory,
    TemplateDocumentFactory,
)


class ScheduledRevisionModelTests(TestCase):
    def test_one_schedule_per_document(self):
        schedule = ScheduledRevisionFactory()

        with (
            self.assertRaisesMessage(IntegrityError, "wiki_scheduledrevision_one_per_document"),
            transaction.atomic(),
        ):
            ScheduledRevisionFactory(revision__document=schedule.document)

    def test_held_revision_never_becomes_current(self):
        older = ApprovedRevisionFactory()
        document = older.document
        current = ApprovedRevisionFactory(document=document)
        held_id = ScheduledRevisionFactory(revision__document=document).revision_id

        current.delete()
        document.refresh_from_db()
        self.assertEqual(document.current_revision, older)

        Document.objects.filter(pk=document.pk).update(current_revision=None)
        fix_current_revisions()
        document.refresh_from_db()
        self.assertEqual(document.current_revision, older)

        Revision.objects.get(pk=held_id).save()
        document.refresh_from_db()
        held = Revision.objects.get(pk=held_id)
        self.assertEqual(document.current_revision, older)
        self.assertFalse(held.is_approved)
        self.assertIsNone(held.reviewed)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, AI_ENABLED_LOCALES=["de"])
class ApplyReviewTests(TestCase):
    def setUp(self):
        self.creator = UserFactory()
        self.reviewer = UserFactory()
        add_permission(self.reviewer, Revision, "review_revision")
        add_permission(self.reviewer, Revision, "mark_ready_for_l10n")
        add_permission(self.reviewer, Document, "edit_needs_change")
        ApproveRevisionInLocaleEvent.notify(UserFactory(), locale="en-US")
        ReadyRevisionEvent.notify(UserFactory())

    def test_apply_review(self):
        for approve, ready in product([True, False], repeat=2):
            with (
                self.subTest(approve=approve, ready=ready),
                patch("kitsune.wiki.tasks.render_document_cascade.delay") as render_cascade,
                patch("kitsune.wiki.tasks.translate.delay") as translate,
            ):
                document = ApprovedRevisionFactory().document
                revision = RevisionFactory(
                    document=document, creator=self.creator, is_ready_for_localization=False
                )
                mail.outbox = []

                apply_review(
                    revision,
                    self.reviewer,
                    approve=approve,
                    comment="Reviewed",
                    significance=MEDIUM_SIGNIFICANCE,
                    ready_for_localization=ready,
                    needs_change=True,
                    needs_change_comment="Needs work",
                )

                revision.refresh_from_db()
                document.refresh_from_db()
                self.assertEqual(
                    {
                        "is_approved": revision.is_approved,
                        "reviewer": revision.reviewer,
                        "is_reviewed": revision.reviewed is not None,
                        "significance": revision.significance,
                        "is_current": document.current_revision == revision,
                        "is_latest_localizable": document.latest_localizable_revision == revision,
                        "needs_change": (document.needs_change, document.needs_change_comment),
                        "cascades": [call.args for call in render_cascade.call_args_list],
                        "translations": sorted(
                            json.loads(call.args[0])["target_locale"]
                            for call in translate.call_args_list
                        ),
                    },
                    {
                        "is_approved": approve,
                        "reviewer": self.reviewer,
                        "is_reviewed": True,
                        "significance": MEDIUM_SIGNIFICANCE,
                        "is_current": approve,
                        "is_latest_localizable": approve and ready,
                        "needs_change": (approve, "Needs work" if approve else ""),
                        "cascades": [(document.id,)],
                        "translations": ["de"] if approve and ready else [],
                    },
                )
                self.assertTrue(
                    any(m.to == [self.creator.email] for m in mail.outbox),
                    "the creator gets the review mail",
                )


class HeldRevisionVisibilityTests(TestCase):
    def test_held_revision_visibility(self):
        current = ApprovedRevisionFactory(document__slug="held-article")
        document = current.document
        creator = UserFactory()
        revisions = {
            "held": ScheduledRevisionFactory(
                revision__document=document, revision__creator=creator
            ).revision,
            "ordinary": RevisionFactory(document=document),
        }
        translation = ApprovedRevisionFactory(
            document__parent=document, document__locale="de", based_on=current
        ).document
        reviewer = UserFactory()
        LocaleFactory(locale=document.locale).reviewers.add(reviewer)
        de_reviewer = UserFactory()
        LocaleFactory(locale="de").reviewers.add(de_reviewer)
        viewers = {
            "anonymous": None,
            "contributor": UserFactory(),
            "creator": creator,
            "reviewer": reviewer,
            "de reviewer": de_reviewer,
            "staff": UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)]),
        }

        def found(url, params=None):
            status_code = self.client.get(url, params).status_code
            self.assertIn(status_code, (200, 404))
            return status_code == 200

        def listed(url, revision, params=None):
            response = self.client.get(url, params)
            self.assertEqual(response.status_code, 200)
            return f'"{revision.get_absolute_url()}"' in response.content.decode()

        pages = {
            "revision": lambda revision: found(revision.get_absolute_url()),
            "compare": lambda revision: found(
                reverse("wiki.compare_revisions", args=[document.slug]),
                {"from": current.id, "to": revision.id},
            ),
            "edit": lambda revision: found(
                reverse("wiki.new_revision_based_on", args=[document.slug, revision.id])
            ),
            "history": lambda revision: listed(
                reverse("wiki.document_revisions", args=[document.slug]), revision
            ),
            "recent revisions": lambda revision: listed(
                reverse("wiki.revisions"), revision, {"fragment": 1, "locale": document.locale}
            ),
            "translate": lambda revision: found(
                reverse(
                    "wiki.new_revision_based_on", args=[translation.slug, revision.id], locale="de"
                )
            ),
        }

        for viewer_name, viewer in viewers.items():
            self.client.logout()
            if viewer:
                self.client.force_login(viewer)
            for (page, shown), (kind, revision) in product(pages.items(), revisions.items()):
                if page in ("edit", "translate") and not viewer:
                    # Anonymous users are sent to log in.
                    continue
                # Translating also checks the held revision against the "de" locale.
                held_viewers = (
                    {"creator", "staff"}
                    if page == "translate"
                    else {"creator", "reviewer", "staff"}
                )
                with self.subTest(viewer=viewer_name, page=page, revision=kind):
                    self.assertEqual(
                        shown(revision), kind == "ordinary" or viewer_name in held_viewers
                    )

    def test_held_revision_hidden_on_an_unpublished_article(self):
        coauthor = UserFactory()
        document = DeferredRevisionFactory(creator=coauthor).document
        held = ScheduledRevisionFactory(
            revision__document=document, revision__content="Held launch content"
        ).revision
        reviewer = UserFactory()
        LocaleFactory(locale=document.locale).reviewers.add(reviewer)
        viewers = {"co-author": coauthor, "creator": held.creator, "reviewer": reviewer}
        pages = {
            "edit": reverse("wiki.edit_document", args=[document.slug]),
            "translate": reverse("wiki.translate", args=[document.slug], locale="de"),
        }
        # Translators start from live content, so no one starts from the held revision.
        shown_to = {"edit": {"creator", "reviewer"}, "translate": set()}

        for (viewer_name, viewer), (page, url) in product(viewers.items(), pages.items()):
            with self.subTest(viewer=viewer_name, page=page):
                self.client.force_login(viewer)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    held.content in response.content.decode(), viewer_name in shown_to[page]
                )

        only_held = ScheduledRevisionFactory().revision
        self.client.force_login(only_held.creator)
        response = self.client.get(
            reverse("wiki.translate", args=[only_held.document.slug], locale="de")
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_be_based_on_a_held_revision(self):
        document = ApprovedRevisionFactory().document
        held = ScheduledRevisionFactory(revision__document=document).revision
        translation = ApprovedRevisionFactory(
            document__parent=document, document__locale="de", based_on=document.current_revision
        ).document
        revision_data = {"content": "Entwurf", "summary": "Zusammenfassung", "based_on": held.id}
        posts = {
            "draft": (
                reverse("wiki.draft_revision", locale="de"),
                {**revision_data, "title": "Titel", "slug": "titel"},
                DraftRevision.objects,
                201,
            ),
            "translation": (
                reverse("wiki.translate", args=[document.slug], locale="de"),
                {**revision_data, "form": "rev"},
                translation.revisions,
                302,
            ),
        }
        viewers = {"contributor": UserFactory(), "creator": held.creator}

        for (post, (url, data, saved, saved_status)), (viewer_name, viewer) in product(
            posts.items(), viewers.items()
        ):
            allowed = viewer_name == "creator"
            with self.subTest(post=post, viewer=viewer_name):
                self.client.force_login(viewer)
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, saved_status if allowed else 400)
                self.assertEqual(saved.filter(creator=viewer).exists(), allowed)

    def test_existing_reference_to_a_revision_held_later(self):
        document = ApprovedRevisionFactory(is_ready_for_localization=True).document
        # No spaces: the diff tables render them as &nbsp;.
        source = RevisionFactory(document=document, content="Embargoed-launch-copy")
        translation = ApprovedRevisionFactory(
            document__parent=document, document__locale="de", based_on=source
        ).document
        submitted = RevisionFactory(document=translation, based_on=source)
        de_reviewer = UserFactory()
        LocaleFactory(locale="de").reviewers.add(de_reviewer)
        self.client.force_login(de_reviewer)
        pages = {
            "review": reverse(
                "wiki.review_revision", args=[translation.slug, submitted.id], locale="de"
            ),
            "translate": reverse("wiki.translate", args=[document.slug], locale="de"),
        }

        # Referenced while ordinary, then held, then opened by someone it is hidden from.
        for held in (False, True):
            if held:
                ScheduledRevisionFactory(revision=source)
            for page, url in pages.items():
                with self.subTest(held=held, page=page):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(source.content in response.content.decode(), not held)

    def test_held_revision_is_not_listed_as_needing_review(self):
        reviewer = UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)])
        LocaleFactory(locale="en-US").reviewers.add(reviewer)
        documents = {}
        for kind in ("ordinary", "held"):
            article = ApprovedRevisionFactory(
                document__title=f"{kind} article", is_ready_for_localization=True
            ).document
            template = ApprovedRevisionFactory(
                document=TemplateDocumentFactory(title=f"Template:{kind} template")
            ).document
            translation = ApprovedRevisionFactory(
                document__title=f"{kind} translation",
                document__parent=article,
                document__locale="de",
                based_on=article.current_revision,
            ).document
            for document in (article, template, translation):
                revision = RevisionFactory(document=document)
                if kind == "held":
                    ScheduledRevisionFactory(revision=revision)
            documents[kind] = {
                "article": article,
                "template": template,
                "translation": translation,
            }

        request = RequestFactory().get("/")
        request.user = reviewer
        request.LANGUAGE_CODE = "en-US"

        def review_needed(readout, locale="en-US"):
            return {
                row["title"]
                for row in readout(request, locale=locale).rows()
                if str(row["status"]) == "Review Needed"
            }

        mail.outbox = []
        send_weekly_ready_for_review_digest()
        digest = "".join(message.body for message in mail.outbox)

        listings = {
            "kb overview": (
                "article",
                {
                    row["title"]
                    for row in kb_overview_rows(user=reviewer)
                    if "revision_comment" in row
                },
            ),
            "most visited": ("article", review_needed(MostVisitedDefaultLanguageReadout)),
            "templates": ("template", review_needed(TemplateReadout)),
            "translations": ("translation", review_needed(MostVisitedTranslationsReadout, "de")),
            "unreviewed": (
                "article",
                {row["title"] for row in UnreviewedReadout(request, locale="en-US").rows()},
            ),
            "digest": (
                "article",
                {
                    doc.title
                    for docs in documents.values()
                    for doc in docs.values()
                    if doc.title in digest
                },
            ),
        }
        for listing, (document_kind, titles) in listings.items():
            with self.subTest(listing=listing):
                self.assertIn(documents["ordinary"][document_kind].title, titles)
                self.assertNotIn(documents["held"][document_kind].title, titles)

        article = documents["held"]["article"]
        held = article.revisions.get(schedule__isnull=False)
        other = RevisionFactory(document=article)
        reviewing = RevisionFactory(document=article)
        self.client.force_login(reviewer)
        content = self.client.get(
            reverse("wiki.review_revision", args=[article.slug, reviewing.id])
        ).content.decode()
        self.assertIn(
            f'"{reverse("wiki.review_revision", args=[article.slug, other.id])}"', content
        )
        self.assertNotIn(
            f'"{reverse("wiki.review_revision", args=[article.slug, held.id])}"', content
        )


NOW = datetime(2026, 10, 1, 12, tzinfo=UTC)
BERLIN = ZoneInfo("Europe/Berlin")


class PublishAtFormTests(TestCase):
    def test_publish_at_validation(self):
        not_on_slot = "Choose a time on the hour or half hour."
        dst_change = (
            "This time happens twice or not at all in your timezone because of a daylight "
            "saving change. Choose another time."
        )
        invalid = "Enter a valid date/time."
        results = {
            "2026-10-02T09:30": datetime(2026, 10, 2, 7, 30, tzinfo=UTC),
            "2026-10-02T09:30:00": datetime(2026, 10, 2, 7, 30, tzinfo=UTC),
            # Ambiguous in the site's US/Pacific, which must not matter.
            "2026-11-01T01:30": datetime(2026, 11, 1, 0, 30, tzinfo=UTC),
            "": None,
            "2026-10-02T09:15": not_on_slot,
            "2026-10-02T09:30:15": not_on_slot,
            "2026-09-30T09:00": "Choose a time in the future.",
            "2026-10-25T02:30": dst_change,
            "2027-03-28T02:30": dst_change,
            "tomorrow at noon": invalid,
            "0001-01-01T00:00": invalid,
        }

        with patch("django.utils.timezone.now", return_value=NOW):
            for publish_at, result in results.items():
                with self.subTest(publish_at=publish_at):
                    form = ReviewForm({"publish_at": publish_at}, timezone=BERLIN)
                    if isinstance(result, str):
                        self.assertEqual(form.errors.get("publish_at"), [result])
                    else:
                        self.assertEqual(form.errors, {})
                        self.assertEqual(form.cleaned_data["publish_at"], result)


class ScheduleReviewTests(TestCase):
    def setUp(self):
        self.reviewer = UserFactory(profile__timezone=BERLIN)
        add_permission(self.reviewer, Revision, "review_revision")
        self.client.force_login(self.reviewer)
        self.document = ApprovedRevisionFactory().document
        self.revision = RevisionFactory(document=self.document)

    def review(self, revision, action="approve", **data):
        mail.outbox = []
        with (
            patch("django.utils.timezone.now", return_value=NOW),
            patch("kitsune.wiki.tasks.render_document_cascade.delay") as render_cascade,
        ):
            response = self.client.post(
                reverse("wiki.review_revision", args=[self.document.slug, revision.id]),
                {action: "1", "comment": "Launch copy", **data},
            )
        self.assertEqual(response.status_code, 302)
        return render_cascade

    def schedules(self):
        return list(ScheduledRevision.objects.values_list("revision", "publish_at"))

    def test_approving_with_a_date_only_schedules(self):
        render_cascade = self.review(
            self.revision,
            publish_at="2026-10-02T09:30",
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
            needs_change=True,
            needs_change_comment="Update after launch",
        )

        self.revision.refresh_from_db()
        self.assertFalse(self.revision.is_approved)
        self.assertIsNone(self.revision.reviewed)
        self.assertEqual(
            ScheduledRevision.objects.values(
                "revision",
                "document",
                "publish_at",
                "reviewer",
                "comment",
                "significance",
                "is_ready_for_localization",
                "needs_change",
                "needs_change_comment",
            ).get(),
            {
                "revision": self.revision.id,
                "document": self.document.id,
                "publish_at": datetime(2026, 10, 2, 7, 30, tzinfo=UTC),
                "reviewer": self.reviewer.id,
                "comment": "Launch copy",
                "significance": MEDIUM_SIGNIFICANCE,
                "is_ready_for_localization": True,
                "needs_change": True,
                "needs_change_comment": "Update after launch",
            },
        )
        self.assertEqual(mail.outbox, [])
        render_cascade.assert_not_called()

    def test_rescheduling_replaces_the_schedule(self):
        self.review(self.revision, publish_at="2026-10-02T09:30")
        self.review(self.revision, publish_at="2026-10-03T18:00")
        self.assertEqual(
            self.schedules(), [(self.revision.id, datetime(2026, 10, 3, 16, tzinfo=UTC))]
        )

        newer = RevisionFactory(document=self.document)
        self.review(newer, publish_at="2026-10-04T08:00")
        self.assertEqual(self.schedules(), [(newer.id, datetime(2026, 10, 4, 6, tzinfo=UTC))])

    def test_approving_now_publishes_and_clears_the_schedule(self):
        ScheduledRevisionFactory(revision=self.revision)
        self.review(self.revision)

        self.revision.refresh_from_db()
        self.assertTrue(self.revision.is_approved)
        self.assertEqual(Document.objects.get(pk=self.document.pk).current_revision, self.revision)
        self.assertEqual(self.schedules(), [])

    def test_rejecting_clears_the_schedule(self):
        ScheduledRevisionFactory(revision=self.revision)
        self.review(self.revision, action="reject", publish_at="2026-10-02T09:30")

        self.revision.refresh_from_db()
        self.assertFalse(self.revision.is_approved)
        self.assertIsNotNone(self.revision.reviewed)
        self.assertEqual(self.schedules(), [])

    def test_approving_a_newer_revision_cancels_the_older_schedule(self):
        ScheduledRevisionFactory(revision=self.revision)
        self.review(RevisionFactory(document=self.document))
        self.assertEqual(self.schedules(), [])

    def test_approving_an_older_revision_keeps_the_newer_schedule(self):
        schedule = ScheduledRevisionFactory(revision__document=self.document)
        self.review(self.revision)
        self.assertEqual(self.schedules(), [(schedule.revision_id, schedule.publish_at)])

    def test_cancel_schedule(self):
        url = reverse("wiki.cancel_revision_schedule", args=[self.document.slug, self.revision.id])
        cases = {
            "reviewer": (self.reviewer, "post", 302),
            "creator": (self.revision.creator, "post", 403),
            "contributor": (UserFactory(), "post", 404),
            "reviewer, GET": (self.reviewer, "get", 405),
        }

        for case, (user, method, status_code) in cases.items():
            with self.subTest(case=case):
                ScheduledRevision.objects.all().delete()
                ScheduledRevisionFactory(revision=self.revision)
                self.client.force_login(user)
                response = getattr(self.client, method)(url)
                self.assertEqual(response.status_code, status_code)
                if status_code == 302:
                    self.assertRedirects(
                        response,
                        reverse("wiki.document_revisions", args=[self.document.slug]),
                        fetch_redirect_response=False,
                    )
                held = Revision.objects.filter(pk=self.revision.pk, schedule__isnull=False)
                self.assertEqual(held.exists(), status_code != 302)
                self.assertTrue(
                    Revision.objects.filter(pk=self.revision.pk, reviewed=None).exists()
                )

    def test_scheduled_label(self):
        ScheduledRevisionFactory(
            revision=self.revision, publish_at=datetime(2026, 10, 2, 7, 30, tzinfo=UTC)
        )
        RevisionFactory(document=self.document)
        creator = self.revision.creator
        creator.profile.timezone = ZoneInfo("Asia/Tokyo")
        creator.profile.save()
        viewers = {
            "reviewer": (self.reviewer, "2026-10-02T09:30:00+02:00"),
            "creator": (creator, "2026-10-02T16:30:00+09:00"),
        }
        pages = {
            "history": reverse("wiki.document_revisions", args=[self.document.slug]),
            "revision": self.revision.get_absolute_url(),
            "review": reverse("wiki.review_revision", args=[self.document.slug, self.revision.id]),
        }
        cancel_url = reverse(
            "wiki.cancel_revision_schedule", args=[self.document.slug, self.revision.id]
        )

        for (viewer_name, (viewer, local_time)), (page, url) in product(
            viewers.items(), pages.items()
        ):
            if page == "review" and viewer_name == "creator":
                # Only reviewers may open the review page.
                continue
            with self.subTest(viewer=viewer_name, page=page):
                self.client.force_login(viewer)
                content = self.client.get(url).content.decode()
                self.assertEqual(content.count(f'Scheduled for <time datetime="{local_time}">'), 1)
                is_reviewer = viewer_name == "reviewer"
                self.assertEqual(f'action="{cancel_url}"' in content, is_reviewer)
                self.assertEqual('form="cancel-schedule"' in content, is_reviewer)
                if page == "review":
                    # Re-reviewing starts from the scheduled time, not an empty "publish now".
                    self.assertIn('name="publish_at" value="2026-10-02T09:30"', content)

    def test_review_page_warns_about_another_revisions_schedule(self):
        newer = RevisionFactory(document=self.document)
        cases = {
            "older revision scheduled": (
                self.revision,
                newer,
                "Approving or scheduling this revision cancels that schedule.",
            ),
            "newer revision scheduled": (newer, self.revision, "and will replace this one."),
        }

        for case, (scheduled, reviewed, consequence) in cases.items():
            ScheduledRevision.objects.all().delete()
            ScheduledRevisionFactory(
                revision=scheduled, publish_at=datetime(2026, 10, 2, 7, 30, tzinfo=UTC)
            )
            for revision, warned in ((reviewed, True), (scheduled, False)):
                with self.subTest(case=case, reviewing=revision.id):
                    content = self.client.get(
                        reverse("wiki.review_revision", args=[self.document.slug, revision.id])
                    ).content.decode()
                    self.assertEqual(
                        f"Revision {scheduled.id} is scheduled to go live on" in content, warned
                    )
                    self.assertEqual(consequence in content, warned)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ReleaseTests(TestCase):
    def setUp(self):
        self.locale = LocaleFactory(locale="en-US")
        self.watcher = UserFactory()
        ApproveRevisionInLocaleEvent.notify(self.watcher, locale="en-US")

    def held(self):
        reviewer = UserFactory()
        self.locale.reviewers.add(reviewer)
        add_permission(reviewer, Revision, "mark_ready_for_l10n")
        add_permission(reviewer, Document, "edit_needs_change")
        return ScheduledRevisionFactory(
            revision__document=ApprovedRevisionFactory().document,
            reviewer=reviewer,
            publish_at=NOW,
            comment="Launch copy",
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True,
            needs_change=True,
            needs_change_comment="Update after launch",
        )

    def review_state(self, revision):
        revision = Revision.objects.get(pk=revision.pk)
        return revision.is_approved, revision.reviewed, revision.reviewer

    def approval_mails(self):
        return [message for message in mail.outbox if message.to == [self.watcher.email]]

    def test_releases_due_revisions_only(self):
        schedule = self.held()
        revision, document = schedule.revision, schedule.document
        before = self.review_state(revision)
        mail.outbox = []

        with patch("django.utils.timezone.now", return_value=NOW - timedelta(seconds=1)):
            self.assertEqual(release_due_revisions(), 0)
        self.assertEqual(self.review_state(revision), before)
        self.assertTrue(ScheduledRevision.objects.filter(pk=schedule.pk).exists())
        self.assertEqual(mail.outbox, [])

        with patch("django.utils.timezone.now", return_value=NOW):
            self.assertEqual(release_due_revisions(), 1)
        revision.refresh_from_db()
        document.refresh_from_db()
        self.assertEqual(
            (
                revision.is_approved,
                revision.reviewer,
                revision.reviewed,
                revision.significance,
                revision.is_ready_for_localization,
                document.current_revision,
                document.needs_change,
                document.needs_change_comment,
            ),
            (
                True,
                schedule.reviewer,
                NOW,
                MEDIUM_SIGNIFICANCE,
                True,
                revision,
                True,
                "Update after launch",
            ),
        )
        self.assertFalse(ScheduledRevision.objects.filter(pk=schedule.pk).exists())
        self.assertEqual(len(self.approval_mails()), 1)
        creator_mails = [m for m in mail.outbox if m.to == [revision.creator.email]]
        self.assertEqual(len(creator_mails), 1)
        self.assertIn(schedule.comment, creator_mails[0].body)

    def test_dropped_schedules(self):
        cases = {
            "already rejected": lambda s: ManualContentManager().reject_revision(
                s.revision, UserFactory(), send_notifications=False
            ),
            "already approved by the AI content manager": lambda s: (
                AIContentManager().publish_revision(s.revision, send_notifications=False)
            ),
            "older than the current revision": lambda s: ApprovedRevisionFactory(
                document=s.document
            ),
            "reviewer lost the permission": lambda s: self.locale.reviewers.remove(s.reviewer),
            "reviewer inactive": lambda s: User.objects.filter(pk=s.reviewer_id).update(
                is_active=False
            ),
        }

        for case, change in cases.items():
            with self.subTest(case=case):
                schedule = self.held()
                change(schedule)
                before = self.review_state(schedule.revision)
                mail.outbox = []

                self.assertEqual(release_due_revisions(NOW), 0)

                self.assertFalse(ScheduledRevision.objects.filter(pk=schedule.pk).exists())
                self.assertEqual(self.review_state(schedule.revision), before)
                self.assertEqual(mail.outbox, [])

    def test_rescheduled_during_a_run_is_not_released(self):
        first, rescheduled = self.held(), self.held()
        later = NOW + timedelta(minutes=30)

        def reschedule_then_apply(*args, **kwargs):
            # A reviewer moves the other schedule after the run listed it as due.
            ScheduledRevision.objects.filter(pk=rescheduled.pk).update(publish_at=later)
            return apply_review(*args, **kwargs)

        with patch("kitsune.wiki.review.apply_review", side_effect=reschedule_then_apply):
            self.assertEqual(release_due_revisions(NOW), 1)

        self.assertTrue(self.review_state(first.revision)[0])
        self.assertEqual(self.review_state(rescheduled.revision), (False, None, None))
        self.assertEqual(ScheduledRevision.objects.get(pk=rescheduled.pk).publish_at, later)

    def test_failed_release_is_retried(self):
        failures = {
            "before the review is applied": patch(
                "kitsune.wiki.review.apply_review", side_effect=DatabaseError
            ),
            # Revision.save() has already stored the approval when it updates the document.
            "while the document is updated": patch.object(
                Document, "save", side_effect=DatabaseError
            ),
        }

        for failure, patcher in failures.items():
            with self.subTest(failure=failure):
                schedule = self.held()

                with patcher, self.assertRaises(DatabaseError):
                    release_due_revisions(NOW)
                self.assertEqual(self.review_state(schedule.revision), (False, None, None))
                self.assertTrue(ScheduledRevision.objects.filter(pk=schedule.pk).exists())

                mail.outbox = []
                self.assertEqual(release_due_revisions(NOW), 1)
                self.assertTrue(self.review_state(schedule.revision)[0])
                self.assertEqual(
                    Document.objects.get(pk=schedule.document_id).current_revision_id,
                    schedule.revision_id,
                )
                self.assertFalse(ScheduledRevision.objects.filter(pk=schedule.pk).exists())
                self.assertEqual(len(self.approval_mails()), 1)

    def test_beat_entry(self):
        entry = PERIODIC_TASKS_ALL["release_scheduled_revisions"]
        self.assertEqual(entry["task"], release_scheduled_revisions.name)
        self.assertEqual(entry["schedule"], crontab(minute="0,30"))

    def test_read_only_mode_skips(self):
        schedule = self.held()

        with patch("django.utils.timezone.now", return_value=NOW):
            with override_settings(READ_ONLY=True):
                release_scheduled_revisions()
            self.assertTrue(ScheduledRevision.objects.filter(pk=schedule.pk).exists())

            release_scheduled_revisions()
        self.assertTrue(self.review_state(schedule.revision)[0])
