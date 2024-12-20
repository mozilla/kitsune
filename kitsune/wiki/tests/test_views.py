# -*- coding: utf-8 -*-

import json
from unittest import mock

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import Client
from pyquery import PyQuery as pq

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.sumo.tests import SkipTest, TestCase, template_used
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory, add_permission
from kitsune.wiki.config import CATEGORIES, TEMPLATE_TITLE_PREFIX, TEMPLATES_CATEGORY
from kitsune.wiki.models import (
    Document,
    DraftRevision,
    HelpfulVote,
    HelpfulVoteMetadata,
    Locale,
    Revision,
)
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    DraftRevisionFactory,
    RedirectRevisionFactory,
    RevisionFactory,
    TemplateDocumentFactory,
    TranslatedRevisionFactory,
    new_document_data,
)
from kitsune.wiki.views import _document_lock_check, _document_lock_clear, _document_lock_steal


class DocumentVisibilityTests(TestCase):
    """Document view visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_approved_content_and_anonymous_user(self):
        """Documents with approved content can be seen by anyone."""
        rev = ApprovedRevisionFactory()
        response = self.client.get(rev.document.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_visibility_when_no_approved_content_and_anonymous_user(self):
        """
        Documents without approved content should effectively not exist for
        anonymous users.
        """
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(rev.document.get_absolute_url())
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(rev.document.get_absolute_url())
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(rev.document.get_absolute_url())
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(rev.document.get_absolute_url())
        self.assertEqual(response.status_code, 200)


class RevisionVisibilityTests(TestCase):
    """Revision visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_approved_content_and_anonymous_user(self):
        """Documents with approved content can be seen by anyone."""
        rev = ApprovedRevisionFactory()
        response = self.client.get(reverse("wiki.revision", args=[rev.document.slug, rev.id]))
        self.assertEqual(response.status_code, 200)

    def test_visibility_when_no_approved_content_and_anonymous_user(self):
        """
        Documents without approved content should effectively not exist for
        anonymous users.
        """
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(reverse("wiki.revision", args=[rev.document.slug, rev.id]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.get(reverse("wiki.revision", args=[rev.document.slug, rev.id]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(
                    reverse("wiki.revision", args=[rev.document.slug, rev.id])
                )
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(reverse("wiki.revision", args=[rev.document.slug, rev.id]))
        self.assertEqual(response.status_code, 200)


class StealLockVisibilityTests(TestCase):
    """Steal-lock visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.post(reverse("wiki.steal_lock", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.post(reverse("wiki.steal_lock", args=[rev.document.slug]))
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.post(reverse("wiki.steal_lock", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 200)


class EditDocumentVisibilityTests(TestCase):
    """Edit-document visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.get(
            reverse("wiki.edit_document_metadata", args=[rev.document.slug])
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(
                    reverse("wiki.edit_document_metadata", args=[rev.document.slug])
                )
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(
            reverse("wiki.edit_document_metadata", args=[rev.document.slug])
        )
        self.assertEqual(response.status_code, 200)


class PreviewRevisionVisibilityTests(TestCase):
    """Preview visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.post(
            reverse("wiki.preview"),
            data=dict(slug=rev.document.slug, locale=rev.document.locale),
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.post(
                    reverse("wiki.preview"),
                    data=dict(slug=rev.document.slug, locale=rev.document.locale),
                )
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.post(
            reverse("wiki.preview"),
            data=dict(slug=rev.document.slug, locale=rev.document.locale),
        )
        self.assertEqual(response.status_code, 200)


class DocumentRevisionsVisibilityTests(TestCase):
    """Document revisions visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_approved_content_and_anonymous_user(self):
        """Documents with approved content can be seen by anyone."""
        rev = ApprovedRevisionFactory()
        response = self.client.get(reverse("wiki.document_revisions", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 200)

    def test_visibility_when_no_approved_content_and_anonymous_user(self):
        """
        Documents without approved content should effectively not exist for
        anonymous users.
        """
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(reverse("wiki.document_revisions", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.get(reverse("wiki.document_revisions", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(
                    reverse("wiki.document_revisions", args=[rev.document.slug])
                )
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(reverse("wiki.document_revisions", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 200)


class CompareRevisionsVisibilityTests(TestCase):
    """Compare revisions visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_approved_content_and_anonymous_user(self):
        """Documents with approved content can be seen by anyone."""
        rev = ApprovedRevisionFactory()
        new_rev = RevisionFactory(document=rev.document)
        url = reverse("wiki.compare_revisions", args=[rev.document.slug])
        response = self.client.get(f"{url}?from={rev.id}&to={new_rev.id}")
        self.assertEqual(response.status_code, 200)

    def test_visibility_when_no_approved_content_and_anonymous_user(self):
        """
        Documents without approved content should effectively not exist for
        anonymous users.
        """
        rev = RevisionFactory(is_approved=False)
        new_rev = RevisionFactory(document=rev.document)
        url = reverse("wiki.compare_revisions", args=[rev.document.slug])
        response = self.client.get(f"{url}?from={rev.id}&to={new_rev.id}")
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        rev = RevisionFactory(is_approved=False)
        new_rev = RevisionFactory(document=rev.document)
        url = reverse("wiki.compare_revisions", args=[rev.document.slug])
        response = self.client.get(f"{url}?from={rev.id}&to={new_rev.id}")
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                new_rev = RevisionFactory(document=rev.document)
                url = reverse("wiki.compare_revisions", args=[rev.document.slug])
                response = self.client.get(f"{url}?from={rev.id}&to={new_rev.id}")
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        self.client.login(username=creator.username, password="testpass")
        rev = RevisionFactory(is_approved=False, creator=creator)
        new_rev = RevisionFactory(document=rev.document)
        url = reverse("wiki.compare_revisions", args=[rev.document.slug])
        response = self.client.get(f"{url}?from={rev.id}&to={new_rev.id}")
        self.assertEqual(response.status_code, 200)


class SelectLocaleVisibilityTests(TestCase):
    """Select locale visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(reverse("wiki.select_locale", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(reverse("wiki.select_locale", args=[rev.document.slug]))
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(reverse("wiki.select_locale", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 200)


class TranslateVisibilityTests(TestCase):
    """Translate visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        rev = RevisionFactory(is_approved=False)
        en_doc = rev.document
        trans_doc = RevisionFactory(
            is_approved=False, document__parent=en_doc, document__locale="es"
        ).document
        response = self.client.get(
            reverse("wiki.translate", locale=trans_doc.locale, args=[en_doc.slug])
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                en_doc = rev.document
                trans_doc = RevisionFactory(
                    is_approved=False, document__parent=en_doc, document__locale="es"
                ).document
                response = self.client.get(
                    reverse("wiki.translate", locale=trans_doc.locale, args=[en_doc.slug])
                )
                expected_status = (
                    200 if perm in ("superuser", "review_revision", "delete_document") else 403
                )
                self.assertEqual(response.status_code, expected_status)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        en_doc = rev.document
        trans_doc = RevisionFactory(
            is_approved=False, document__parent=en_doc, document__locale="es"
        ).document
        response = self.client.get(
            reverse("wiki.translate", locale=trans_doc.locale, args=[en_doc.slug])
        )
        self.assertEqual(response.status_code, 403)


class WatchDocumentVisibilityTests(TestCase):
    """Watch document visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.post(reverse("wiki.document_watch", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.post(
                    reverse("wiki.document_watch", args=[rev.document.slug])
                )
                self.assertEqual(response.status_code, 302)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.post(reverse("wiki.document_watch", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 302)


class UnwatchDocumentVisibilityTests(TestCase):
    """Unwatch document visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.post(reverse("wiki.document_unwatch", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.post(
                    reverse("wiki.document_unwatch", args=[rev.document.slug])
                )
                self.assertEqual(response.status_code, 302)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.post(reverse("wiki.document_unwatch", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 302)


class GetHelpfulVotesAsyncVisibilityTests(TestCase):
    """Get helpful votes async visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_approved_content_and_anonymous_user(self):
        """Documents with approved content can be seen by anyone."""
        rev = ApprovedRevisionFactory()
        response = self.client.get(
            reverse("wiki.get_helpful_votes_async", args=[rev.document.slug])
        )
        self.assertEqual(response.status_code, 200)

    def test_visibility_when_no_approved_content_and_anonymous_user(self):
        """
        Documents without approved content should effectively not exist for
        anonymous users.
        """
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(
            reverse("wiki.get_helpful_votes_async", args=[rev.document.slug])
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.get(
            reverse("wiki.get_helpful_votes_async", args=[rev.document.slug])
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(
                    reverse("wiki.get_helpful_votes_async", args=[rev.document.slug])
                )
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(
            reverse("wiki.get_helpful_votes_async", args=[rev.document.slug])
        )
        self.assertEqual(response.status_code, 200)


class AddContributorVisibilityTests(TestCase):
    """Add contributor visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        rev = RevisionFactory(is_approved=False)
        contributors = UserFactory.create_batch(2)
        data = dict(users=",".join(u.username for u in contributors))
        response = self.client.post(
            reverse("wiki.add_contributor", args=[rev.document.slug]), data=data
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                contributors = UserFactory.create_batch(2)
                data = dict(users=",".join(u.username for u in contributors))
                response = self.client.post(
                    reverse("wiki.add_contributor", args=[rev.document.slug]), data=data
                )
                self.assertEqual(response.status_code, 302)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        self.client.login(username=creator.username, password="testpass")
        rev = RevisionFactory(is_approved=False, creator=creator)
        contributors = UserFactory.create_batch(2)
        data = dict(users=",".join(u.username for u in contributors))
        response = self.client.post(
            reverse("wiki.add_contributor", args=[rev.document.slug]), data=data
        )
        self.assertEqual(response.status_code, 302)


class RemoveContributorVisibilityTests(TestCase):
    """Remove contributor visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        rev = RevisionFactory(is_approved=False)
        contributor = UserFactory()
        response = self.client.get(
            reverse("wiki.remove_contributor", args=[rev.document.slug, contributor.id])
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                contributor = UserFactory()
                response = self.client.get(
                    reverse("wiki.remove_contributor", args=[rev.document.slug, contributor.id])
                )
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        self.client.login(username=creator.username, password="testpass")
        contributor = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        response = self.client.get(
            reverse("wiki.remove_contributor", args=[rev.document.slug, contributor.id])
        )
        self.assertEqual(response.status_code, 200)


class ShowTranslationsVisibilityTests(TestCase):
    """Show translations visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_approved_content_and_anonymous_user(self):
        """Documents with approved content can be seen by anyone."""
        rev = ApprovedRevisionFactory()
        response = self.client.get(reverse("wiki.show_translations", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 200)

    def test_visibility_when_no_approved_content_and_anonymous_user(self):
        """
        Documents without approved content should effectively not exist for
        anonymous users.
        """
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(reverse("wiki.show_translations", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(reverse("wiki.show_translations", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(
                    reverse("wiki.show_translations", args=[rev.document.slug])
                )
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(reverse("wiki.show_translations", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 200)


class WhatLinksHereVisibilityTests(TestCase):
    """What-links-here visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_approved_content_and_anonymous_user(self):
        """Documents with approved content can be seen by anyone."""
        rev = ApprovedRevisionFactory()
        response = self.client.get(reverse("wiki.what_links_here", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 200)

    def test_visibility_when_no_approved_content_and_anonymous_user(self):
        """
        Documents without approved content should effectively not exist for
        anonymous users.
        """
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(reverse("wiki.what_links_here", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        rev = RevisionFactory(is_approved=False)
        response = self.client.get(reverse("wiki.what_links_here", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(
                    reverse("wiki.what_links_here", args=[rev.document.slug])
                )
                self.assertEqual(response.status_code, 200)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(reverse("wiki.what_links_here", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 200)


class DeleteDocumentVisibilityTests(TestCase):
    """Delete document visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.get(reverse("wiki.document_delete", args=[rev.document.slug]))
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(
                    reverse("wiki.document_delete", args=[rev.document.slug])
                )
                expected_status = (
                    200 if perm in ("superuser", "delete_document", "en-US__leaders") else 403
                )
                self.assertEqual(response.status_code, expected_status)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(reverse("wiki.document_delete", args=[rev.document.slug]))
        self.assertEqual(response.status_code, 403)


class MarkReadyForL10nVisibilityTests(TestCase):
    """Mark ready for l10n visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.post(
            reverse("wiki.mark_ready_for_l10n_revision", args=[rev.document.slug, rev.id])
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.post(
                    reverse("wiki.mark_ready_for_l10n_revision", args=[rev.document.slug, rev.id])
                )
                self.assertEqual(response.status_code, 400 if perm == "superuser" else 403)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.post(
            reverse("wiki.mark_ready_for_l10n_revision", args=[rev.document.slug, rev.id])
        )
        self.assertEqual(response.status_code, 403)


class DeleteRevisionVisibilityTests(TestCase):
    """Delete revision visibility tests."""

    def setUp(self):
        ProductFactory()

    def test_visibility_when_no_approved_content_and_authenticated_user_without_permission(
        self,
    ):
        """
        Documents without approved content should effectively not exist for
        authenticated users without the proper permission.
        """
        rev = RevisionFactory(is_approved=False)
        user = UserFactory()
        # The document is in the "en-US" locale, so this permission won't provide access.
        locale_team, _ = Locale.objects.get_or_create(locale="de")
        locale_team.reviewers.add(user)
        self.client.login(username=user.username, password="testpass")
        response = self.client.get(
            reverse("wiki.delete_revision", args=[rev.document.slug, rev.id])
        )
        self.assertEqual(404, response.status_code)

    def test_visibility_when_no_approved_content_and_authenticated_user_with_permission(self):
        """
        Documents without approved content can be seen by authenticated users with one of
        several special permissions.
        """
        # Each of these permissions will provide access.
        for perm in (
            "superuser",
            "review_revision",
            "delete_document",
            "en-US__leaders",
            "en-US__reviewers",
        ):
            with self.subTest(perm):
                user = UserFactory(is_superuser=(perm == "superuser"))
                if perm == "review_revision":
                    add_permission(user, Revision, "review_revision")
                elif perm == "delete_document":
                    add_permission(user, Document, "delete_document")
                elif "__" in perm:
                    locale, role = perm.split("__")
                    locale_team, _ = Locale.objects.get_or_create(locale=locale)
                    getattr(locale_team, role).add(user)
                self.client.login(username=user.username, password="testpass")
                rev = RevisionFactory(is_approved=False)
                response = self.client.get(
                    reverse("wiki.delete_revision", args=[rev.document.slug, rev.id])
                )
                expected_status = (
                    200 if perm in ("superuser", "en-US__leaders", "en-US__reviewers") else 403
                )
                self.assertEqual(response.status_code, expected_status)
                self.client.logout()

    def test_visibility_when_no_approved_content_and_creator(self):
        """
        Documents without approved content can be seen by their creator.
        """
        creator = UserFactory()
        rev = RevisionFactory(is_approved=False, creator=creator)
        self.client.login(username=creator.username, password="testpass")
        response = self.client.get(
            reverse("wiki.delete_revision", args=[rev.document.slug, rev.id])
        )
        self.assertEqual(response.status_code, 403)


class RedirectTests(TestCase):
    """Tests for the REDIRECT wiki directive"""

    def setUp(self):
        super(RedirectTests, self).setUp()
        ProductFactory()

    def test_redirect_suppression(self):
        """The document view shouldn't redirect when passed redirect=no."""
        rev = RedirectRevisionFactory()
        redirect = rev.document
        response = self.client.get(redirect.get_absolute_url() + "?redirect=no", follow=True)
        self.assertContains(response, "REDIRECT ")


class LocaleRedirectTests(TestCase):
    """Tests for fallbacks to en-US and such for slug lookups."""

    # Some of these may fail or be invalid if your WIKI_DEFAULT_LANGUAGE is de.

    def setUp(self):
        super(LocaleRedirectTests, self).setUp()
        ProductFactory()
        en = settings.WIKI_DEFAULT_LANGUAGE
        self.en_doc = ApprovedRevisionFactory(
            document__locale=en, document__slug="english-slug"
        ).document
        self.de_doc = ApprovedRevisionFactory(
            document__locale="de", document__parent=self.en_doc
        ).document

    def test_fallback_to_translation(self):
        """If a slug isn't found in the requested locale but is in the default
        locale and if there is a translation of that default-locale document to
        the requested locale, the translation should be served."""
        response = self.client.get(
            reverse("wiki.document", args=[self.en_doc.slug], locale="de"), follow=True
        )
        self.assertRedirects(response, self.de_doc.get_absolute_url())

    def test_fallback_with_query_params(self):
        """The query parameters should be passed along to the redirect."""
        url = reverse("wiki.document", args=[self.en_doc.slug], locale="de")
        response = self.client.get(url + "?x=y&x=z", follow=True)
        self.assertRedirects(response, self.de_doc.get_absolute_url() + "?x=y&x=z")


class JsonViewTests(TestCase):
    def setUp(self):
        super(JsonViewTests, self).setUp()

        d = DocumentFactory(title="an article title", slug="article-title")
        RevisionFactory(document=d, is_approved=True)

    def test_json_view_by_title(self):
        """Verify checking for an article by title."""
        url = reverse("wiki.json")
        resp = self.client.get(url, {"title": "an article title"})
        self.assertEqual(200, resp.status_code)
        data = json.loads(resp.content)
        self.assertEqual("article-title", data["slug"])

    def test_json_view_by_slug(self):
        """Verify checking for an article by slug."""
        url = reverse("wiki.json")
        resp = self.client.get(url, {"slug": "article-title"})
        self.assertEqual(200, resp.status_code)
        data = json.loads(resp.content)
        self.assertEqual("an article title", data["title"])

    def test_json_view_404(self):
        """Searching for something that doesn't exist should 404."""
        url = reverse("wiki.json")
        resp = self.client.get(url, {"title": "an article title ok."})
        self.assertEqual(404, resp.status_code)


class WhatLinksWhereTests(TestCase):
    def test_what_links_here(self):
        group = GroupFactory()
        user = UserFactory(groups=[group])
        d1 = ApprovedRevisionFactory(content="", document__title="D1").document
        ApprovedRevisionFactory(content="[[D1]]", document__title="D2")
        ApprovedRevisionFactory(
            content="[[D1]]",
            document__title="D3",
            document__restrict_to_groups=[group],
        )

        url = reverse("wiki.what_links_here", args=[d1.slug])
        resp = self.client.get(url, follow=True)
        self.assertEqual(200, resp.status_code)
        assert b"D2" in resp.content
        assert b"D3" not in resp.content

        self.client.login(username=user.username, password="testpass")
        resp = self.client.get(url, follow=True)
        self.client.logout()
        self.assertEqual(200, resp.status_code)
        assert b"D2" in resp.content
        assert b"D3" in resp.content

    def test_what_links_here_locale_filtering(self):
        d1 = DocumentFactory(title="D1", locale="de")
        ApprovedRevisionFactory(document=d1, content="")
        d2 = DocumentFactory(title="D2", locale="fr")
        ApprovedRevisionFactory(document=d2, content="[[D1]]")

        url = reverse("wiki.what_links_here", args=[d1.slug], locale="de")
        resp = self.client.get(url, follow=True)
        self.assertEqual(200, resp.status_code)
        assert b"Auf D1 verweisen keine anderen Dokumente." in resp.content

    def test_what_links_here_with_locale_fallback(self):
        d1 = ApprovedRevisionFactory(content="", document__title="D1").document
        d2 = ApprovedRevisionFactory(content="[[D1]]", document__title="D2").document
        ApprovedRevisionFactory(
            content="",
            document__title="DAS-1",
            document__locale="de",
            document__parent=d1,
        ).document
        ApprovedRevisionFactory(
            content="[[DAS-1]]",
            document__title="DAS-2",
            document__locale="de",
            document__parent=d2,
        ).document

        url = reverse("wiki.what_links_here", args=[d1.slug], locale="de")
        resp = self.client.get(url, follow=True)
        self.assertEqual(200, resp.status_code)
        assert b"DAS-2" in resp.content


class DocumentEditingTests(TestCase):
    """Tests for the document-editing view"""

    def setUp(self):
        super(DocumentEditingTests, self).setUp()
        self.u = UserFactory()
        # The "delete_document" permission is one of the ways to allow
        # a user to "see" documents that have no approved content.
        add_permission(self.u, Document, "delete_document")
        add_permission(self.u, Document, "change_document")
        self.client.login(username=self.u.username, password="testpass")

    def test_retitling(self):
        """When the title of an article is edited, a redirect is made."""
        # Not testing slug changes separately; the model tests cover those plus
        # slug+title changes. If title changes work in the view, the rest
        # should also.
        new_title = "Some New Title"
        r = ApprovedRevisionFactory()
        d = r.document
        old_title = d.title
        data = new_document_data()
        data.update({"title": new_title, "slug": d.slug, "form": "doc"})
        self.client.post(reverse("wiki.edit_document_metadata", args=[d.slug]), data)
        self.assertEqual(new_title, Document.objects.get(id=d.id).title)
        assert Document.objects.get(title=old_title).redirect_url()

    def test_retitling_accent(self):
        d = DocumentFactory(title="Umlaut test")
        RevisionFactory(document=d, is_approved=True)
        new_title = "Ümlaut test"
        data = new_document_data()
        data.update({"title": new_title, "slug": d.slug, "form": "doc"})
        self.client.post(reverse("wiki.edit_document_metadata", args=[d.slug]), data)
        self.assertEqual(new_title, Document.objects.get(id=d.id).title)

    def test_retitling_template(self):
        d = TemplateDocumentFactory()
        RevisionFactory(document=d)

        old_title = d.title
        new_title = "Not a template"

        # First try and change the title without also changing the category. It should fail.
        data = new_document_data()
        data.update({"title": new_title, "category": d.category, "slug": d.slug, "form": "doc"})
        url = reverse("wiki.edit_document_metadata", args=[d.slug])
        res = self.client.post(url, data, follow=True)
        self.assertEqual(Document.objects.get(id=d.id).title, old_title)
        # This message gets HTML encoded.
        assert (
            b"Documents in the Template category must have titles that start with "
            b"&#34;Template:&#34;." in res.content
        )

        # Now try and change the title while also changing the category.
        data["category"] = CATEGORIES[0][0]
        url = reverse("wiki.edit_document_metadata", args=[d.slug])
        self.client.post(url, data, follow=True)
        self.assertEqual(Document.objects.get(id=d.id).title, new_title)

    def test_removing_template_category(self):
        d = TemplateDocumentFactory()
        RevisionFactory(document=d)
        self.assertEqual(d.category, TEMPLATES_CATEGORY)
        assert d.title.startswith(TEMPLATE_TITLE_PREFIX)

        # First try and change the category without also changing the title. It should fail.
        data = new_document_data()
        data.update(
            {"title": d.title, "category": CATEGORIES[0][0], "slug": d.slug, "form": "doc"}
        )
        url = reverse("wiki.edit_document_metadata", args=[d.slug])
        res = self.client.post(url, data, follow=True)
        self.assertEqual(Document.objects.get(id=d.id).category, TEMPLATES_CATEGORY)
        # This message gets HTML encoded.
        assert (
            b"Documents with titles that start with &#34;Template:&#34; must be in the "
            b"templates category." in res.content
        )

        # Now try and change the title while also changing the category.
        data["title"] = "not a template"
        url = reverse("wiki.edit_document_metadata", args=[d.slug])
        self.client.post(url, data)
        self.assertEqual(Document.objects.get(id=d.id).category, CATEGORIES[0][0])

    def test_changing_products(self):
        """Changing products works as expected."""
        r = ApprovedRevisionFactory()
        d = r.document
        prod_desktop = ProductFactory(title="desktop")
        prod_mobile = ProductFactory(title="mobile")
        topic = TopicFactory(products=[prod_desktop, prod_mobile])

        data = new_document_data()
        data.update(
            {
                "products": [prod_desktop.id, prod_mobile.id],
                "topics": [topic.id],
                "title": d.title,
                "slug": d.slug,
                "form": "doc",
            }
        )
        self.client.post(reverse("wiki.edit_document_metadata", args=[d.slug]), data)

        self.assertEqual(
            sorted(Document.objects.get(id=d.id).products.values_list("id", flat=True)),
            sorted([prod.id for prod in [prod_desktop, prod_mobile]]),
        )

        data.update({"products": [prod_desktop.id], "form": "doc"})
        self.client.post(reverse("wiki.edit_document_metadata", args=[data["slug"]]), data)
        self.assertEqual(
            sorted(Document.objects.get(id=d.id).products.values_list("id", flat=True)),
            sorted([prod.id for prod in [prod_desktop]]),
        )

    @mock.patch.object(Site.objects, "get_current")
    def test_new_document_slugs(self, get_current):
        """Slugs cannot contain /. but can be urlencoded"""
        get_current.return_value.domain = "testserver"
        data = new_document_data()
        error = "The slug provided is not valid."

        data["slug"] = "inva/lid"
        response = self.client.post(reverse("wiki.new_document"), data)
        self.assertContains(response, error)

        data["slug"] = "no-question-marks?"
        response = self.client.post(reverse("wiki.new_document"), data)
        self.assertContains(response, error)

        data["slug"] = "no+plus"
        response = self.client.post(reverse("wiki.new_document"), data)
        self.assertContains(response, error)

        data["slug"] = "%2Atesttest"
        response = self.client.post(reverse("wiki.new_document"), data)
        self.assertContains(response, error)

        data["slug"] = "%20testtest"
        response = self.client.post(reverse("wiki.new_document"), data)
        self.assertContains(response, error)

        data["slug"] = "valid"
        response = self.client.post(reverse("wiki.new_document"), data)
        self.assertRedirects(
            response, reverse("wiki.document_revisions", args=[data["slug"]], locale="en-US")
        )

    def test_translate_with_parent_slug_while_trans_article_available(self):
        doc = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        r = RevisionFactory(document=doc)
        trans_doc = DocumentFactory(parent=doc, locale="bn", slug="bn_slug")
        RevisionFactory(document=trans_doc, based_on=r)
        url = reverse("wiki.edit_document", args=[doc.slug], locale=trans_doc.locale)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check translate article template is being used
        assert template_used(response, "wiki/translate.html")
        content = pq(response.content)
        self.assertEqual(content("#id_title").val(), trans_doc.title)
        self.assertEqual(content("#id_slug").val(), trans_doc.slug)

    def test_translate_with_parent_slug_while_trans_article_not_available(self):
        doc = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        RevisionFactory(document=doc)
        url = reverse("wiki.edit_document", args=[doc.slug], locale="bn")
        response = self.client.get(url)
        # Check redirect is happening
        self.assertEqual(response.status_code, 302)
        # get the redirected url
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        # Check translate article template is being used
        assert template_used(response, "wiki/translate.html")
        content = pq(response.content)
        # While first translation, the slug and title field is always blank.
        # So the value field should be None
        self.assertEqual(content("#id_title").val(), "")
        self.assertEqual(content("#id_slug").val(), "")

    def test_while_there_is_no_parent_slug(self):
        doc = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        invalid_slug = doc.slug + "invalid_slug"
        url = reverse("wiki.edit_document", args=[invalid_slug], locale="bn")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_localized_based_on(self):
        """Editing a localized article 'based on' an older revision of the
        localization is OK."""
        en_r = RevisionFactory()
        fr_d = DocumentFactory(parent=en_r.document, locale="fr")
        RevisionFactory(document=fr_d, based_on=en_r, is_approved=True)
        fr_r = RevisionFactory(document=fr_d, based_on=en_r, keywords="oui", summary="lipsum")
        url = reverse(
            "wiki.new_revision_based_on",
            locale="fr",
            args=(
                fr_d.slug,
                fr_r.pk,
            ),
        )
        response = self.client.get(url)
        doc = pq(response.content)
        input = doc("#id_based_on")[0]
        self.assertEqual(int(input.value), en_r.pk)
        self.assertEqual(doc("#id_keywords")[0].attrib["value"], "oui")
        self.assertEqual(doc("#id_summary").text(), "\nlipsum")

    def test_needs_change(self):
        """Test setting and unsetting the needs change flag"""
        # Create a new document and edit it, setting needs_change.
        comment = "Please update for Firefix.next"
        doc = RevisionFactory().document
        data = new_document_data()
        data.update({"needs_change": True, "needs_change_comment": comment, "form": "doc"})

        # Verify that needs_change can't be set if the user doesn't have
        # the permission.
        self.client.post(reverse("wiki.edit_document", args=[doc.slug]), data)
        doc = Document.objects.get(pk=doc.pk)
        assert not doc.needs_change
        assert not doc.needs_change_comment

        # Give the user permission, now it should work.
        add_permission(self.u, Document, "edit_needs_change")
        self.client.post(reverse("wiki.edit_document_metadata", args=[doc.slug]), data)
        doc = Document.objects.get(pk=doc.pk)
        assert doc.needs_change
        self.assertEqual(comment, doc.needs_change_comment)

        # Clear out needs_change.
        data.update({"needs_change": False, "needs_change_comment": comment})
        self.client.post(reverse("wiki.edit_document_metadata", args=[doc.slug]), data)
        doc = Document.objects.get(pk=doc.pk)
        assert not doc.needs_change
        self.assertEqual("", doc.needs_change_comment)

    def test_draft_revision_view(self):
        """Test Draft Revision saving is working propoerly"""
        rev = ApprovedRevisionFactory()
        url = reverse("wiki.draft_revision", locale="bn")
        data = {
            "content": "Test Content bla bla bla",
            "keyword": "something",
            "summary": "some summary",
            "title": "test title",
            "slug": "test-slug",
            "based_on": rev.id,
        }
        resp = self.client.post(url, data)
        self.assertEqual(201, resp.status_code)
        obj = DraftRevision.objects.get(creator=self.u, document=rev.document, locale="bn")
        self.assertEqual(obj.content, data["content"])
        self.assertEqual(obj.based_on, rev)

    def test_draft_revision_many_times(self):
        """Test only one draft revision for a single translation and user"""
        rev = ApprovedRevisionFactory()
        url = reverse("wiki.draft_revision", locale="bn")
        data = {
            "content": "Test Content bla bla bla",
            "keyword": "something",
            "summary": "some summary",
            "title": "test title",
            "slug": "test-slug",
            "based_on": rev.id,
        }
        # post 10 post request for draft
        for i in range(10):
            resp = self.client.post(url, data)
            self.assertEqual(201, resp.status_code)

        obj = DraftRevision.objects.filter(creator=self.u, document=rev.document, locale="bn")
        # There should be only one draft revision
        self.assertEqual(1, obj.count())

    def test_draft_revision_restore_in_translation_page(self):
        """Check Draft Revision is restored when a user click on the Restore Button"""
        # Create a draft revision
        draft = DraftRevisionFactory(creator=self.u)
        doc = draft.document
        # Now send a get request to the page for restoring the draft
        trans_url = reverse("wiki.translate", locale=draft.locale, args=[doc.slug])
        draft_request = {"restore": "Restore"}
        restore_draft_resp = self.client.post(trans_url, draft_request)
        self.assertEqual(200, restore_draft_resp.status_code)
        # Check if the title of the translate page contains the title of draft revision
        trans_page = pq(restore_draft_resp.content)
        self.assertEqual("\n" + draft.content, trans_page("#id_content").text())

    def test_discard_draft_revision(self):
        """Check Draft Revision is discarded

        If a user clicks on Discard button in the translation page, the draft revision
        should be deleted"""
        draft = DraftRevisionFactory(creator=self.u)
        doc = draft.document
        # Send a request to translate article page to discard the draft
        trans_url = reverse("wiki.translate", locale=draft.locale, args=[doc.slug])
        draft_request = {"discard": "Discard"}
        restore_draft_resp = self.client.post(trans_url, draft_request)
        self.assertEqual(302, restore_draft_resp.status_code)
        # Check if the draft revision is in database
        draft = DraftRevision.objects.filter(id=draft.id)
        self.assertEqual(False, draft.exists())

    def test_draft_revision_discarded_when_submitting_revision(self):
        """Check draft revision is discarded when submitting a revision

        A user can have only one Draft revision for each translated document. The draft revision
        should be deleted automatically when the user submit any revision in the document."""
        draft = DraftRevisionFactory(creator=self.u)
        doc = draft.document
        locale = draft.locale
        trans_url = reverse("wiki.translate", locale=locale, args=[doc.slug])
        data = {
            "title": "Un Test Articulo",
            "slug": "un-test-articulo",
            "keywords": "keyUno, keyDos, keyTres",
            "summary": "lipsumo",
            "content": "loremo ipsumo doloro sito ameto",
            "form": "both",
        }
        self.client.post(trans_url, data)
        draft_revision = DraftRevision.objects.filter(id=draft.id)
        self.assertEqual(False, draft_revision.exists())


class AddRemoveContributorTests(TestCase):
    def setUp(self):
        super(AddRemoveContributorTests, self).setUp()
        self.user = UserFactory()
        self.contributor = UserFactory()
        # The "delete_document" permission is one of the ways to allow
        # a user to "see" documents that have no approved content.
        add_permission(self.user, Document, "delete_document")
        add_permission(self.user, Document, "change_document")
        self.client.login(username=self.user.username, password="testpass")
        self.revision = RevisionFactory()
        self.document = self.revision.document

    def test_add_contributor(self):
        url = reverse("wiki.add_contributor", locale="en-US", args=[self.document.slug])
        r = self.client.get(url)
        self.assertEqual(405, r.status_code)
        r = self.client.post(url, {"users": self.contributor.username})
        self.assertEqual(302, r.status_code)
        assert self.contributor in self.document.contributors.all()

    def test_remove_contributor(self):
        self.document.contributors.add(self.contributor)
        url = reverse(
            "wiki.remove_contributor",
            locale="en-US",
            args=[self.document.slug, self.contributor.id],
        )
        r = self.client.get(url)
        self.assertEqual(200, r.status_code)
        r = self.client.post(url)
        self.assertEqual(302, r.status_code)
        assert self.contributor not in self.document.contributors.all()


class VoteTests(TestCase):
    def test_helpful_vote_bad_id(self):
        """Throw helpful_vote a bad ID, and see if it crashes."""
        response = self.client.post(
            reverse("wiki.document_vote", args=["hi"]), {"revision_id": "x"}
        )
        self.assertEqual(404, response.status_code)

    def test_helpful_vote_no_id(self):
        """Throw helpful_vote a POST without an ID and see if it 400s."""
        response = self.client.post(reverse("wiki.document_vote", args=["hi"]), {})
        self.assertEqual(400, response.status_code)

    def test_vote_on_template(self):
        """
        Throw helpful_vote a document that is a template and see if it 400s.
        """
        d = TemplateDocumentFactory()
        r = ApprovedRevisionFactory(document=d)
        response = self.client.post(
            reverse("wiki.document_vote", args=["hi"]), {"revision_id": r.id}
        )
        self.assertEqual(400, response.status_code)

    def test_source(self):
        """Test that the source metadata field works."""
        rev = ApprovedRevisionFactory()
        url = reverse("wiki.document_vote", kwargs={"document_slug": rev.document.slug})
        self.client.post(
            url,
            {
                "revision_id": rev.id,
                "helpful": True,
                "source": "test",
            },
        )

        self.assertEqual(HelpfulVoteMetadata.objects.filter(key="source").count(), 1)

    def test_rate_limiting(self):
        """Verify only 10 votes are counted in a day."""
        for i in range(13):
            rev = ApprovedRevisionFactory()
            url = reverse("wiki.document_vote", kwargs={"document_slug": rev.document.slug})
            self.client.post(url, {"revision_id": rev.id, "helpful": True})

        self.assertEqual(10, HelpfulVote.objects.count())


class TestDocumentLocking(TestCase):
    def setUp(self):
        super(TestDocumentLocking, self).setUp()
        try:
            self.redis = redis_client("default")
            self.redis.flushdb()
        except RedisError:
            raise SkipTest

    def _test_lock_helpers(self, doc):
        u1 = UserFactory()
        u2 = UserFactory()

        # No one has the document locked yet.
        self.assertEqual(_document_lock_check(doc.id), None)
        # u1 should be able to lock the doc
        self.assertEqual(_document_lock_steal(doc.id, u1.username), True)
        self.assertEqual(_document_lock_check(doc.id), u1.username)
        # u2 should be able to steal the lock
        self.assertEqual(_document_lock_steal(doc.id, u2.username), True)
        self.assertEqual(_document_lock_check(doc.id), u2.username)
        # u1 can't release the lock, because u2 stole it
        self.assertEqual(_document_lock_clear(doc.id, u1.username), False)
        self.assertEqual(_document_lock_check(doc.id), u2.username)
        # u2 can release the lock
        self.assertEqual(_document_lock_clear(doc.id, u2.username), True)
        self.assertEqual(_document_lock_check(doc.id), None)

    def test_lock_helpers_doc(self):
        doc = DocumentFactory()
        self._test_lock_helpers(doc)

    def test_lock_helpers_translation(self):
        doc_en = DocumentFactory()
        doc_de = DocumentFactory(parent=doc_en, locale="de")
        self._test_lock_helpers(doc_de)

    def _lock_workflow(self, doc, edit_url):
        """This is a big end to end feature test of document locking.

        This tests that when a user starts editing a page, it gets locked,
        users can steal locks, and that when a user submits the edit page, the
        lock is cleared.
        """

        def _login(user):
            self.client.login(username=user.username, password="testpass")

        def assert_is_locked(r):
            self.assertContains(r, 'id="unlock-button"')

        def assert_not_locked(r):
            self.assertNotContains(r, 'id="unlock-button"')

        u1 = UserFactory(password="testpass")
        u2 = UserFactory(password="testpass")

        # With u1, edit the document. No lock should be found.
        _login(u1)
        r = self.client.get(edit_url)
        # Now load it again, the page should not show as being locked
        # (since u1 has the lock)
        r = self.client.get(edit_url)
        assert_not_locked(r)

        # With u2, edit the document. It should be locked.
        _login(u2)
        r = self.client.get(edit_url)
        assert_is_locked(r)
        # Simulate stealing the lock by clicking the button.
        _document_lock_steal(doc.id, u2.username)
        r = self.client.get(edit_url)
        assert_not_locked(r)

        # Now u1 should see the page as locked.
        _login(u1)
        r = self.client.get(edit_url)
        assert_is_locked(r)

        # Now u2 submits the page, clearing the held lock.
        _login(u2)
        r = self.client.post(edit_url)

        data = new_document_data()
        # We're using "rev" for the form because all users have the
        # "create_revision" permission needed for "rev", but the "edit"
        # permission needed for "doc" has to be explicitly granted when
        # the translated document and its parent document have approved
        # content.
        data.update({"title": doc.title, "slug": doc.slug, "form": "rev"})
        self.client.post(edit_url, data)

        # And u1 should not see a lock warning.
        _login(u1)
        r = self.client.get(edit_url)
        assert_not_locked(r)

    def test_doc_lock_workflow(self):
        """End to end test of locking on an english document."""
        rev = ApprovedRevisionFactory()
        doc = rev.document
        url = reverse("wiki.edit_document", args=[doc.slug], locale="en-US")
        self._lock_workflow(doc, url)

    def test_trans_lock_workflow(self):
        """End to end test of locking on a translated document."""
        trans_doc = TranslatedRevisionFactory().document
        edit_url = reverse("wiki.edit_document", locale=trans_doc.locale, args=[trans_doc.slug])
        self._lock_workflow(trans_doc, edit_url)


class FallbackSystem(TestCase):
    """Check that fallback locales on article level are working correctly."""

    def setUp(self):
        super(FallbackSystem, self).setUp()
        ProductFactory()

    def create_documents(self, locale):
        """Create a document in English and a translated document for the locale"""
        en = settings.WIKI_DEFAULT_LANGUAGE
        en_content = "This article is in English"
        trans_content = "This article is translated into %slocale" % locale
        # Create an English article and a translation for the locale
        en_doc = DocumentFactory(locale=en)
        ApprovedRevisionFactory(
            document=en_doc, content=en_content, is_ready_for_localization=True
        )
        trans_doc = DocumentFactory(parent=en_doc, locale=locale)
        # Create a new revision of the localized document
        trans_rev = ApprovedRevisionFactory(document=trans_doc, content=trans_content)
        # Make the created revision the current one for the localized document
        trans_doc.current_revision = trans_rev
        trans_doc.save()
        # Return both the English version and the localized version of the document
        return en_doc, trans_doc

    def get_data_from_translated_document(self, header, create_doc_locale, req_doc_locale):
        """Create documents and get provided locale document data"""
        # Create a client with provided ACCEPT_LANGUAGE header information
        client = Client(HTTP_ACCEPT_LANGUAGE=header)
        # Create an English and a localized version of the document, based on create_doc_locale
        en_doc, trans_doc = self.create_documents(create_doc_locale)
        # Get the data of the requested locale version of the document
        url = reverse("wiki.document", args=[en_doc.slug], locale=req_doc_locale)
        response = client.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        doc = pq(response.content)
        doc_content = doc("#doc-content").text()
        return doc_content

    def test_header_locales_in_translated_list(self):
        """
        Test that the article is showing in the header locale

        Test cases when the document is not localized to locale requested by the user,
        but is localized to a locale mentioned in the ACCEPT_LANGUAGE header
        """
        # Define a client with es, fr, ja as locale choices in the ACCEPT_LANGUAGE header
        header = "es,fr;q=0.7,ja;q=0.3,"
        # Create a document localized into fr
        # Attempt to resolve to the es version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(
            header=header, create_doc_locale="fr", req_doc_locale="es"
        )
        # Show the fr version of the document based on existing client header,
        # as it is not localized into es
        en_content = "This article is in English"
        trans_content = "This article is translated into fr"
        assert en_content not in doc_content
        assert trans_content in doc_content

    def test_header_locales_not_in_translated_list(self):
        """
        Test that the article is showing in the header locale, with the following conditions:

        * the article is not localized into the user-requested locale
        * the article is not localized to any of the locales listed in the ACCEPT_LANGUAGE header
        * there is a fallback locale defined for one of the locales listed in the the
          ACCEPT LANGUAGE header
           ** it is set in kitsune/settings.py

        Test that the fallback locale is used
        """

        # Define a client with de, an, ja as locale choices in the ACCEPT_LANGUAGE header
        header = "de,an;q=0.7,ja;q=0.3,"
        # Create a document localized into es
        # Attempt to resolve to the de version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(
            header=header, create_doc_locale="es", req_doc_locale="de"
        )
        # Show the es version of the document based on the fallback locale for an set in
        # kitsune/settings.py, as it is not localized into de and there is no available
        # locale based on the client header
        en_content = "This article is in English"
        trans_content = "This article is translated into es"
        assert en_content not in doc_content
        assert trans_content in doc_content

    def test_en_in_accept_language_header(self):
        """If the first fallback locale does not exist and the second fallback locale is en-US,
        the second fallback locale should not be used"""
        # Define a client with fr, en-US, de as locale choices in the ACCEPT_LANGUAGE header
        header = "fr,en-US;q=0.7,de;q=0.3,"
        # Create a document localized into de
        # Attempt to resolve to the es version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(
            header=header, create_doc_locale="de", req_doc_locale="es"
        )
        # Show the en-US version of the document based on existing client header,
        # as it is not localized into fr and de is behind en-US in header
        en_content = "This article is in English"
        trans_content = "This article is translated into de"
        assert en_content in doc_content
        assert trans_content not in doc_content

    def test_custom_locale_mapping(self):
        """
        Test that the article is showing according to defined locale fallback options
        (more than one), with the following conditions:

        * the article is not localized into the user-requested locale
        * the article is not localized into any of the locales listed in the ACCEPT_LANGUAGE header
        * None of the ACCEPT_LANGUAGE header locales has a defined fallback locale
        * the user-requested locale has more than one fallback locale defined and
          the requested article is localized into one of the defined fallback locales
            ** the fallback locale is set in kitsune/settings.py

        Test that the article is shown in the defined fallback locale
        """

        # Create a document localized into es. Attempt to resolve to the ca version
        # of the document without defining locale options for the client

        # of the document. While we the client have no language choices.
        doc_content = self.get_data_from_translated_document(
            header=None, create_doc_locale="es", req_doc_locale="ca"
        )
        # Show the es locale version of the document based on the fallback locale,
        # as it is not localized into ca locale and there is no available locale
        # from the ACCEPT_LANGUAGE header
        en_content = "This article is in English"
        trans_content = "This article is translated into es"
        assert en_content not in doc_content
        assert trans_content in doc_content

    def test_custom_locale_mapping_for_header_locale(self):
        """
        Test that defined locale fallbacks are used as header locales,
        with the following conditions:

        * the article is not localized into the user-requested locale
        * the article is not localized to any of the locales listed in the ACCEPT_LANGUAGE header
        * the header locales do not have a defined fallback locale OR the article is not localized
          into any of those defined fallback locales
        * the user-requested locale has a defined fallback locale, but the article is
          not localized into it
        * one of the locales listed in the ACCEPT_LANGUAGE headers has a defined fallback locale
          and the article is localized into that fallback locale

        Test that the defined fallback locale is used
        """

        # The user-requested locale has a defined custom wiki fallback locale,
        # but the article is not localized into that fallback locale

        # Define a client with ca, wo, ja as locale choices in the ACCEPT_LANGUAGE header
        header = "ca,wo;q=0.7,ja;q=0.3,"
        # Create a document localized into fr
        # Attempt to resolve to the ca version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(
            header=header, create_doc_locale="fr", req_doc_locale="ca"
        )
        # Show the pt-BR version of the document based on existing custom wiki locale mapping
        # for pt-PT, as it is not localized into ca
        en_content = "This article is in English"
        trans_content = "This article is translated into fr"
        assert en_content not in doc_content
        assert trans_content in doc_content

        # If the user-requested locale does not have a custom wiki fallback locale
        # Define a client with ca, wo, ja as locale choices in the ACCEPT_LANGUAGE header
        header = "ar,wo;q=0.7,ja;q=0.3,"
        # Create a document localized into fr
        # Attempt to resolve to the ar version of the document with the client defined before
        doc_content = self.get_data_from_translated_document(
            header=header, create_doc_locale="fr", req_doc_locale="ar"
        )
        # Show the article in wo based on the custom wiki fallback locale mapping for wo,
        # as it is localized neither into any of the locales listed in the
        # ACCEPT_LANGUAGE header, nor into ar
        en_content = "This article is in English"
        trans_content = "This article is translated into fr"
        assert en_content not in doc_content
        assert trans_content in doc_content

    def test_non_normalized_case_in_accept_language_header(self):
        """
        We should be able to handle the Accept-Language values no matter their case.
        """
        en_content = "This article is in English"

        with self.subTest("wiki fallback"):
            doc_content = self.get_data_from_translated_document(
                header="fy-nl,fr;q=0.8,en-us;q=0.7", create_doc_locale="nl", req_doc_locale="fr"
            )
            self.assertNotIn(en_content, doc_content)
            self.assertIn("This article is translated into nl", doc_content)

        with self.subTest("global override"):
            doc_content = self.get_data_from_translated_document(
                header="sv-se,fr;q=0.8,en-us;q=0.7", create_doc_locale="sv", req_doc_locale="fr"
            )
            self.assertNotIn(en_content, doc_content)
            self.assertIn("This article is translated into sv", doc_content)

        with self.subTest("supported language"):
            doc_content = self.get_data_from_translated_document(
                header="pt-br,fr;q=0.8,en-us;q=0.7", create_doc_locale="pt-BR", req_doc_locale="fr"
            )
            self.assertNotIn(en_content, doc_content)
            self.assertIn("This article is translated into pt-BR", doc_content)

    def test_skip_of_document_cache_when_fallback_uses_accept_language(self):
        en_doc, es_doc = self.create_documents("es")
        url = reverse("wiki.document", args=[en_doc.slug], locale="fr")

        # First, request the document in French via the English slug. Since a
        # French translation doesn't exist, the Accept-Language header is used
        # to determine that the Spanish translation can be returned instead.
        # This shouldn't be cached, because the response depends on the user's
        # Accept-Language header.
        headers = {"accept-language": "fr;q=0.8,es;q=0.7"}
        response = self.client.get(url, headers=headers)
        self.assertEqual(200, response.status_code)
        self.assertIn("vary", response)
        self.assertIn("accept-language", response["vary"])
        doc = pq(response.content)
        self.assertEqual(doc("html").attr("lang"), "fr")
        self.assertEqual(doc("html").attr("data-ga-article-locale"), "es")
        self.assertIn("This article is translated into es", doc("#doc-content").text())

        # If another user makes the same request, the French content via the
        # English slug, but this user will only accept English content as a
        # fallback, then let's make sure the previous request wasn't cached,
        # because if it was cached, the Spanish content would be returned.
        headers = {"accept-language": "fr;q=0.8,en-us;q=0.7"}
        response = self.client.get(url, headers=headers)
        self.assertEqual(200, response.status_code)
        self.assertIn("vary", response)
        self.assertIn("accept-language", response["vary"])
        doc = pq(response.content)
        doc_content = doc("#doc-content").text()
        self.assertEqual(doc("html").attr("lang"), "fr")
        self.assertEqual(doc("html").attr("data-ga-article-locale"), "en-US")
        self.assertIn("This article is in English", doc_content)

    def test_vary_header_when_fallback_uses_accept_language(self):
        en_doc, es_doc = self.create_documents("es")
        url = reverse("wiki.document", args=[en_doc.slug], locale="fr")

        with self.subTest("default in accept-language"):
            headers = {"accept-language": "fr;q=0.8,en-us;q=0.7"}
            response = self.client.get(url, headers=headers)
            self.assertEqual(200, response.status_code)
            self.assertIn("vary", response)
            self.assertIn("accept-language", response["vary"])
            doc = pq(response.content)
            self.assertEqual(doc("html").attr("lang"), "fr")
            self.assertEqual(doc("html").attr("data-ga-article-locale"), "en-US")
            self.assertIn("This article is in English", doc("#doc-content").text())

        with self.subTest("another translation in accept-language"):
            headers = {"accept-language": "fr;q=0.8,es;q=0.7"}
            response = self.client.get(url, headers=headers)
            self.assertEqual(200, response.status_code)
            self.assertIn("vary", response)
            self.assertIn("accept-language", response["vary"])
            doc = pq(response.content)
            self.assertEqual(doc("html").attr("lang"), "fr")
            self.assertEqual(doc("html").attr("data-ga-article-locale"), "es")
            self.assertIn("This article is translated into es", doc("#doc-content").text())

        with self.subTest("hard-coded fallback in accept-language"):
            headers = {"accept-language": "fr;q=0.8,ca;q=0.7"}
            response = self.client.get(url, headers=headers)
            self.assertEqual(200, response.status_code)
            self.assertIn("vary", response)
            self.assertIn("accept-language", response["vary"])
            doc = pq(response.content)
            self.assertEqual(doc("html").attr("lang"), "fr")
            self.assertEqual(doc("html").attr("data-ga-article-locale"), "es")
            self.assertIn("This article is translated into es", doc("#doc-content").text())

        with self.subTest("no fallback found"):
            headers = {"accept-language": "fr;q=0.8"}
            response = self.client.get(url, headers=headers)
            self.assertEqual(200, response.status_code)
            self.assertIn("vary", response)
            self.assertIn("accept-language", response["vary"])
            doc = pq(response.content)
            self.assertEqual(doc("html").attr("lang"), "fr")
            self.assertEqual(doc("html").attr("data-ga-article-locale"), "en-US")
            self.assertIn("This article is in English", doc("#doc-content").text())

    def test_vary_header_when_fallback_does_not_use_accept_language(self):
        en_doc, es_doc = self.create_documents("es")
        url = reverse("wiki.document", args=[en_doc.slug], locale="ca")
        headers = {"accept-language": "en-us;q=0.8"}
        response = self.client.get(url, headers=headers)
        self.assertEqual(200, response.status_code)
        self.assertIn("vary", response)
        self.assertNotIn("accept-language", response["vary"])
        doc = pq(response.content)
        self.assertEqual(doc("html").attr("lang"), "ca")
        self.assertEqual(doc("html").attr("data-ga-article-locale"), "es")
        self.assertIn("This article is translated into es", doc("#doc-content").text())


class PocketArticleTests(TestCase):
    """Pocket article redirect tests."""

    def setUp(self):
        ProductFactory()

    def test_pocket_redirect_to_kb_for_document_that_exists(self):
        """Are we redirecting to our article page?"""
        doc = DocumentFactory(title="an article title", slug="article-title")
        RevisionFactory(document=doc, is_approved=True)
        pocket_style_url = f"/kb/pocket/1111-{doc.slug}"
        response = self.client.get(pocket_style_url, follow=True)
        redirect_chain = response.redirect_chain
        self.assertEqual(len(redirect_chain), 2)
        self.assertEqual(redirect_chain[0], (f"/en-US/kb/pocket/1111-{doc.slug}", 302))
        self.assertEqual(redirect_chain[1], ("/en-US/kb/article-title", 302))

    def test_pocket_redirect_when_kb_article_doesnt_exist(self):
        """No match found, we should be sent to /products/pocket"""
        pocket_style_url = "/kb/pocket/1111-wont-match"
        response = self.client.get(pocket_style_url, follow=True)
        redirect_chain = response.redirect_chain
        self.assertEqual(len(redirect_chain), 2)
        self.assertEqual(redirect_chain[0], (f"/en-US{pocket_style_url}", 302))
        self.assertEqual(redirect_chain[1], ("/en-US/products/pocket", 301))
