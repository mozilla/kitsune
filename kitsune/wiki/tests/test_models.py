# coding: utf-8

import urlparse
from datetime import datetime

from nose.tools import eq_
from taggit.models import TaggedItem

from django.core.exceptions import ValidationError

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo import ProgrammingError
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import (
    REDIRECT_SLUG, REDIRECT_TITLE, REDIRECT_HTML, MAJOR_SIGNIFICANCE, CATEGORIES,
    TYPO_SIGNIFICANCE, REDIRECT_CONTENT, TEMPLATES_CATEGORY, TEMPLATE_TITLE_PREFIX)
from kitsune.wiki.models import Document
from kitsune.wiki.parser import wiki_to_html
from kitsune.wiki.tests import (
    RevisionFactory, ApprovedRevisionFactory, TranslatedRevisionFactory, DocumentFactory,
    TemplateDocumentFactory, RedirectRevisionFactory)


def _objects_eq(manager, list_):
    """Assert that the objects contained by `manager` are those in `list_`."""
    eq_(set(manager.all()), set(list_))


class DocumentTests(TestCase):
    """Tests for the Document model"""

    def test_document_is_template(self):
        """is_template stays in sync with the title"""
        d = DocumentFactory(title='test')

        assert not d.is_template

        d.title = TEMPLATE_TITLE_PREFIX + 'test'
        d.category = TEMPLATES_CATEGORY
        d.save()

        assert d.is_template

        d.title = 'Back to document'
        d.category = CATEGORIES[0][0]
        d.save()

        assert not d.is_template

    def test_delete_tagged_document(self):
        """Make sure deleting a tagged doc deletes its tag relationships."""
        # TODO: Move to wherever the tests for TaggableMixin are.
        # This works because Django's delete() sees the `tags` many-to-many
        # field (actually a manager) and follows the reference.
        d = DocumentFactory(tags=['grape'])
        eq_(1, TaggedItem.objects.count())

        d.delete()
        eq_(0, TaggedItem.objects.count())

    def test_category_inheritance(self):
        """A document's categories must always be those of its parent."""
        some_category = CATEGORIES[1][0]
        other_category = CATEGORIES[2][0]

        # Notice if somebody ever changes the default on the category field,
        # which would invalidate our test:
        assert some_category != DocumentFactory().category

        parent = DocumentFactory(category=some_category)
        child = DocumentFactory(parent=parent, locale='de')

        # Make sure child sees stuff set on parent:
        eq_(some_category, child.category)

        # Child'd category should revert to parent's on save:
        child.category = other_category
        child.save()
        eq_(some_category, child.category)

        # Changing the parent category should change the child's:
        parent.category = other_category

        parent.save()
        eq_(other_category,
            parent.translations.get(locale=child.locale).category)

    def _test_remembering_setter_unsaved(self, field):
        """A remembering setter shouldn't kick in until the doc is saved."""
        old_field = 'old_' + field
        d = DocumentFactory.build()
        setattr(d, field, 'Foo')
        assert not hasattr(d, old_field), "Doc shouldn't have %s until it's saved." % old_field

    def test_slug_setter_unsaved(self):
        self._test_remembering_setter_unsaved('slug')

    def test_title_setter_unsaved(self):
        self._test_remembering_setter_unsaved('title')

    def _test_remembering_setter(self, field):
        old_field = 'old_' + field
        d = DocumentFactory()
        old = getattr(d, field)

        # Changing the field makes old_field spring into life:
        setattr(d, field, 'Foo')
        eq_(old, getattr(d, old_field))

        # Changing it back makes old_field disappear:
        setattr(d, field, old)
        assert not hasattr(d, old_field)

        # Change it again once:
        setattr(d, field, 'Foo')

        # And twice:
        setattr(d, field, 'Bar')

        # And old_field should remain as it was, since it hasn't been saved
        # between the two changes:
        eq_(old, getattr(d, old_field))

    def test_slug_setter(self):
        """Make sure changing a slug remembers its old value."""
        self._test_remembering_setter('slug')

    def test_title_setter(self):
        """Make sure changing a title remembers its old value."""
        self._test_remembering_setter('title')

    def test_redirect_prefix(self):
        """Test accuracy of the prefix that helps us recognize redirects."""
        assert wiki_to_html(REDIRECT_CONTENT % 'foo').startswith(REDIRECT_HTML)

    def test_only_localizable_allowed_children(self):
        """You can't have children for a non-localizable document."""
        # Make English rev:
        en_doc = DocumentFactory(is_localizable=False)

        # Make Deutsch translation:
        de_doc = DocumentFactory.build(parent=en_doc, locale='de')
        self.assertRaises(ValidationError, de_doc.save)

    def test_cannot_make_non_localizable_if_children(self):
        """You can't make a document non-localizable if it has children."""
        # Make English rev:
        en_doc = DocumentFactory(is_localizable=True)

        # Make Deutsch translation:
        DocumentFactory(parent=en_doc, locale='de')
        en_doc.is_localizable = False
        self.assertRaises(ValidationError, en_doc.save)

    def test_non_english_implies_nonlocalizable(self):
        d = DocumentFactory(is_localizable=True, locale='de')
        assert not d.is_localizable

    def test_validate_category_on_save(self):
        """Make sure invalid categories can't be saved.

        Invalid categories cause errors when viewing documents.

        """
        d = DocumentFactory.build(category=9999)
        self.assertRaises(ValidationError, d.save)

    def test_new_doc_does_not_update_categories(self):
        """Make sure that creating a new document doesn't change the
        category of all the other documents."""
        d1 = DocumentFactory(category=20)
        assert d1.pk
        d2 = DocumentFactory.build(category=30)
        assert not d2.pk
        d2._clean_category()
        d1prime = Document.objects.get(pk=d1.pk)
        eq_(20, d1prime.category)

    def test_majorly_outdated(self):
        """Test the is_majorly_outdated method."""
        trans = TranslatedRevisionFactory(is_approved=True)
        trans_doc = trans.document

        # Make sure a doc returns False if it has no parent:
        assert not trans_doc.parent.is_majorly_outdated()

        assert not trans_doc.is_majorly_outdated()

        # Add a parent revision of MAJOR significance:
        r = RevisionFactory(document=trans_doc.parent, significance=MAJOR_SIGNIFICANCE)
        assert not trans_doc.is_majorly_outdated()

        # Approve it:
        r.is_approved = True
        r.is_ready_for_localization = True
        r.save()

        assert trans_doc.is_majorly_outdated()

    def test_majorly_outdated_with_unapproved_parents(self):
        """Migrations might introduce translated revisions without based_on
        set. Tolerate these.

        If based_on of a translation's current_revision is None, the
        translation should be considered out of date iff any
        major-significance, approved revision to the English article exists.

        """
        # Create a parent doc with only an unapproved revision...
        parent_rev = RevisionFactory()
        # ...and a translation with a revision based on nothing.
        trans = DocumentFactory(parent=parent_rev.document, locale='de')
        trans_rev = RevisionFactory(document=trans, is_approved=True)

        assert trans_rev.based_on is None, \
            ('based_on defaulted to something non-None, which this test '
             "wasn't expecting.")

        assert not trans.is_majorly_outdated(), \
            ('A translation was considered majorly out of date even though '
             'the English document has never had an approved revision of '
             'major significance.')

        ApprovedRevisionFactory(
            document=parent_rev.document,
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True)

        assert trans.is_majorly_outdated(), \
            ('A translation was not considered majorly outdated when its '
             "current revision's based_on value was None.")

    def test_redirect_document_non_redirect(self):
        """Assert redirect_document on non-redirects returns None."""
        eq_(None, DocumentFactory().redirect_document())

    def test_redirect_document_external_redirect(self):
        """Assert redirects to external pages return None."""
        rev = ApprovedRevisionFactory(content='REDIRECT [http://example.com')
        eq_(rev.document.redirect_document(), None)

    def test_redirect_document_nonexistent(self):
        """Assert redirects to non-existent pages return None."""
        rev = ApprovedRevisionFactory(content='REDIRECT [[kersmoo]]')
        eq_(None, rev.document.redirect_document())

    def test_redirect_nondefault_locales(self):
        title1 = 'title1'
        title2 = 'title2'

        redirect_to = ApprovedRevisionFactory(
            document__title=title1,
            document__locale='es',
            document=DocumentFactory(title=title1, locale='es'))

        redirector = RedirectRevisionFactory(
            target=redirect_to.document,
            document__title=title2,
            document__locale='es',
            is_approved=True)

        eq_(redirect_to.document.get_absolute_url(),
            redirector.document.redirect_url())

    def test_get_topics(self):
        """Test the get_topics() method."""
        en_us = DocumentFactory(topics=TopicFactory.create_batch(2))
        eq_(2, len(en_us.get_topics()))

        # Localized document inherits parent's topics.
        DocumentFactory(parent=en_us)
        eq_(2, len(en_us.get_topics()))

    def test_get_products(self):
        """Test the get_products() method."""
        en_us = DocumentFactory(products=ProductFactory.create_batch(2))

        eq_(2, len(en_us.get_products()))

        # Localized document inherits parent's topics.
        DocumentFactory(parent=en_us)
        eq_(2, len(en_us.get_products()))

    def test_template_title_and_category_to_template(self):
        d = DocumentFactory()

        # First, try and change just the title. It should fail.
        d.title = TEMPLATE_TITLE_PREFIX + d.title
        self.assertRaises(ValidationError, d.save)

        # Next, try and change just the category. It should also fail.
        d = Document.objects.get(id=d.id)  # reset
        d.category = TEMPLATES_CATEGORY
        self.assertRaises(ValidationError, d.save)

        # Finally, try and change both title and category. It should work.
        d = Document.objects.get(id=d.id)  # reset
        d.title = TEMPLATE_TITLE_PREFIX + d.title
        d.category = TEMPLATES_CATEGORY
        d.save()

    def test_template_title_and_category_from_template(self):
        d = TemplateDocumentFactory()

        # First, try and change just the title. It should fail.
        d.title = 'Not A Template'
        self.assertRaises(ValidationError, d.save)

        # Next, try and change just the category. It should also fail.
        d = Document.objects.get(id=d.id)  # reset
        d.category = CATEGORIES[0][0]
        self.assertRaises(ValidationError, d.save)

        # Finally, try and change both title and category. It should work.
        d = Document.objects.get(id=d.id)  # reset
        d.title = 'Not A Template'
        d.category = CATEGORIES[0][0]
        d.save()

    def test_template_title_and_category_localized(self):
        # Because localized articles are required to match templates with their
        # parents, this deserves extra testing.

        d_en = DocumentFactory()
        d_fr = DocumentFactory(parent=d_en, locale='fr')

        # Just changing the title isn't enough
        d_fr.title = TEMPLATE_TITLE_PREFIX + d_fr.title
        self.assertRaises(ValidationError, d_fr.save)

        # Trying to change the category won't work, since `d_en` will force the
        # old category.
        d_fr = Document.objects.get(id=d_fr.id)  # reset
        d_fr.title = TEMPLATE_TITLE_PREFIX + d_fr.title
        d_fr.category = TEMPLATES_CATEGORY
        self.assertRaises(ValidationError, d_fr.save)

        # Change the parent
        d_en.title = TEMPLATE_TITLE_PREFIX + d_en.title
        d_en.category = TEMPLATES_CATEGORY
        d_en.save()

        # Now the French article can be changed too.
        d_fr = Document.objects.get(id=d_fr.id)  # reset
        d_fr.title = TEMPLATE_TITLE_PREFIX + d_fr.title
        d_fr.category = TEMPLATES_CATEGORY
        d_fr.save()

    # It may seem like there is a missing case here. That is because
    # there is. There is no test for changing the title and the
    # category of a translated document at once. This action would be
    # valid for a non-translated document. Translated documents have an
    # additional constraint that the category of a translated document
    # must match the category of the parent.
    #
    # Additionally, the UI does not provide a user any way to do this.
    # The only way this could happen is by direct changes to the
    # database.
    #
    # Due to these reasons, I've left the case of renaming and
    # recategorizing a template undefined in the tests. If this becomes
    # something we do in the future, we should revisit this and define
    # the behavior in a test.


class FromUrlTests(TestCase):
    """Tests for Document.from_url()"""

    def test_redirect_to_translated_document(self):
        from_url = Document.from_url

        d_en = DocumentFactory(locale='en-US', title=u'How to delete Google Chrome?')
        d_tr = DocumentFactory(locale='tr', title=u'Google Chrome\'u nasıl silerim?', parent=d_en)
        # The /tr/kb/how-to-delete-google-chrome URL for Turkish locale
        # should be redirected to /tr/kb/google-chromeu-nasl-silerim
        # if there is a Turkish translation of the document.
        tr_translate_url = reverse('wiki.document', locale='tr', args=[d_en.slug])
        self.assertEqual(d_en.translated_to('tr'), from_url(tr_translate_url))
        self.assertEqual(d_tr, from_url(tr_translate_url))
        self.assertEqual(d_en, from_url(d_en.get_absolute_url()))

    def test_id_only(self):
        from_url = Document.from_url

        d = DocumentFactory(locale='en-US', title=u'How to delete Google Chrome?')
        doc = from_url(d.get_absolute_url(), id_only=True)
        self.assertEqual(d.title, doc.title)
        self.assertEqual(d.locale, doc.locale)

    def test_document_translate_fallback(self):
        d_en = DocumentFactory(locale='en-US', title=u'How to delete Google Chrome?')
        invalid_translate = reverse('wiki.document', locale='tr', args=[d_en.slug])
        self.assertEqual(d_en, Document.from_url(invalid_translate))

    def test_check_host(self):
        from_url = Document.from_url
        d_en = DocumentFactory(locale='en-US', title=u'How to delete Google Chrome?')
        sumo_host = 'https://support.mozilla.org'
        invalid_url = urlparse.urljoin(sumo_host, d_en.get_absolute_url())
        self.assertIsNone(from_url(invalid_url))
        self.assertEqual(d_en, from_url(invalid_url, check_host=False))


class LocalizableOrLatestRevisionTests(TestCase):
    """Tests for Document.localizable_or_latest_revision"""

    def test_none(self):
        """If there are no revisions, return None."""
        d = DocumentFactory()
        eq_(None, d.localizable_or_latest_revision())

    def test_only_rejected(self):
        """If there are only rejected revisions, return None."""
        rejected = RevisionFactory(is_approved=False, reviewed=datetime.now())
        eq_(None, rejected.document.localizable_or_latest_revision())

    def test_multiple_ready(self):
        """When multiple ready revisions exist, return the most recent."""
        r1 = ApprovedRevisionFactory(is_approved=True, is_ready_for_localization=True)
        r2 = ApprovedRevisionFactory(document=r1.document, is_ready_for_localization=True)
        eq_(r2, r2.document.localizable_or_latest_revision())

    def test_ready_over_recent(self):
        """Favor a ready revision over a more recent unready one."""
        ready = ApprovedRevisionFactory(is_approved=True, is_ready_for_localization=True)
        ApprovedRevisionFactory(document=ready.document, is_ready_for_localization=False)
        eq_(ready, ready.document.localizable_or_latest_revision())

    def test_approved_over_unreviewed(self):
        """Favor an approved revision over a more recent unreviewed one."""
        approved = ApprovedRevisionFactory(is_ready_for_localization=False)
        RevisionFactory(
            document=approved.document,
            is_ready_for_localization=False,
            is_approved=False,
            reviewed=None)
        eq_(approved, approved.document.localizable_or_latest_revision())

    def test_latest_unreviewed_if_none_ready(self):
        """Return the latest unreviewed revision when no ready one exists."""
        unreviewed = RevisionFactory(is_approved=False, reviewed=None)
        eq_(unreviewed, unreviewed.document.localizable_or_latest_revision())

    def test_latest_rejected_if_none_unreviewed(self):
        """Return the latest rejected revision when no ready or unreviewed ones
        exist, if include_rejected=True."""
        rejected = RevisionFactory(is_approved=False, reviewed=datetime.now())
        eq_(rejected, rejected.document.localizable_or_latest_revision(include_rejected=True))

    def test_non_localizable(self):
        """When document isn't localizable, ignore is_ready_for_l10n."""
        r1 = ApprovedRevisionFactory(is_ready_for_localization=True)
        r2 = ApprovedRevisionFactory(document=r1.document, is_ready_for_localization=False)
        r1.document.is_localizable = False
        r1.document.save()
        eq_(r2, r2.document.localizable_or_latest_revision())


class RedirectCreationTests(TestCase):
    """Tests for automatic creation of redirects when slug or title changes"""

    def setUp(self):
        self.r = ApprovedRevisionFactory()
        self.d = self.r.document
        self.old_title = self.d.title
        self.old_slug = self.d.slug

    def test_change_slug(self):
        """Test proper redirect creation on slug change."""
        self.d.slug = 'new-slug'
        self.d.share_link = 'https://example.com/redirect'
        self.d.save()
        redirect = Document.objects.get(slug=self.old_slug)
        eq_(REDIRECT_CONTENT % self.d.title, redirect.current_revision.content)
        eq_(REDIRECT_TITLE % dict(old=self.d.title, number=1), redirect.title)

        # Verify the share_link got cleared out.
        doc = Document.objects.get(slug=self.d.slug)
        eq_('', doc.share_link)

    def test_change_title(self):
        """Test proper redirect creation on title change."""
        self.d.title = 'New Title'
        self.d.save()
        redirect = Document.objects.get(title=self.old_title)
        eq_(REDIRECT_CONTENT % self.d.title, redirect.current_revision.content)
        eq_(REDIRECT_SLUG % dict(old=self.d.slug, number=1), redirect.slug)

    def test_change_slug_and_title(self):
        """Assert only one redirect is made when both slug and title change."""
        self.d.title = 'New Title'
        self.d.slug = 'new-slug'
        self.d.save()
        eq_(REDIRECT_CONTENT % self.d.title,
            Document.objects.get(
                slug=self.old_slug,
                title=self.old_title).current_revision.content)

    def test_no_redirect_on_unsaved_change(self):
        """No redirect should be made when an unsaved doc's title or slug is
        changed."""
        d = DocumentFactory(title='Gerbil')
        d.title = 'Weasel'
        d.save()
        # There should be no redirect from Gerbil -> Weasel:
        assert not Document.objects.filter(title='Gerbil').exists()

    def _test_collision_avoidance(self, attr, other_attr, template):
        """When creating redirects, dodge existing docs' titles and slugs."""
        # Create a doc called something like Whatever Redirect 1:
        kwargs = {
            other_attr: template % {
                'old': getattr(self.d, other_attr),
                'number': 1
            }
        }
        DocumentFactory(locale=self.d.locale, **kwargs)

        # Trigger creation of a redirect of a new title or slug:
        setattr(self.d, attr, 'new')
        self.d.save()

        # It should be called something like Whatever Redirect 2:
        redirect = Document.objects.get(**{attr: getattr(self,
                                                         'old_' + attr)})
        eq_(template % dict(old=getattr(self.d, other_attr),
                            number=2), getattr(redirect, other_attr))

    def test_slug_collision_avoidance(self):
        """Dodge existing slugs when making redirects due to title changes."""
        self._test_collision_avoidance('slug', 'title', REDIRECT_TITLE)

    def test_title_collision_avoidance(self):
        """Dodge existing titles when making redirects due to slug changes."""
        self._test_collision_avoidance('title', 'slug', REDIRECT_SLUG)

    def test_redirects_unlocalizable(self):
        """Auto-created redirects should be marked unlocalizable."""
        self.d.slug = 'new-slug'
        self.d.save()
        redirect = Document.objects.get(slug=self.old_slug)
        eq_(False, redirect.is_localizable)


class RevisionTests(TestCase):
    """Tests for the Revision model"""

    def test_approved_revision_updates_html(self):
        """Creating an approved revision updates document.html"""
        d = ApprovedRevisionFactory(content='Replace document html').document

        assert 'Replace document html' in d.html, '"Replace document html" not in %s' % d.html

        # Creating another approved revision replaces it again
        ApprovedRevisionFactory(document=d, content='Replace html again')

        assert 'Replace html again' in d.html, \
               '"Replace html again" not in %s' % d.html

    def test_unapproved_revision_not_updates_html(self):
        """Creating an unapproved revision does not update document.html"""
        d = ApprovedRevisionFactory(content='Here to stay').document
        assert 'Here to stay' in d.html, '"Here to stay" not in %s' % d.html

        # Creating another approved revision keeps initial content
        RevisionFactory(document=d, content='Fail to replace html')
        assert 'Here to stay' in d.html, '"Here to stay" not in %s' % d.html

    def test_revision_unicode(self):
        """Revision containing unicode characters is saved successfully."""
        str = u' \r\nFirefox informa\xe7\xf5es \u30d8\u30eb'
        r = ApprovedRevisionFactory(content=str)
        eq_(str, r.content)

    def test_save_bad_based_on(self):
        """Saving a Revision with a bad based_on value raises an error."""
        r1 = RevisionFactory()
        # Revision of some other unrelated Document
        r2 = RevisionFactory.build(based_on=r1)
        self.assertRaises(ProgrammingError, r2.save)

    def test_correct_based_on_to_none(self):
        """Assure Revision.clean() changes a bad based_on value to None when
        there is no current_revision of the English document."""
        r1 = RevisionFactory()
        # Revision of some other unrelated Document
        r2 = RevisionFactory.build(based_on=r1)
        self.assertRaises(ValidationError, r2.clean)
        eq_(None, r2.based_on)

    def test_correct_based_on_to_current_revision(self):
        """Assure Revision.clean() changes a bad based_on value to the English
        doc's current_revision when there is one."""
        # Make English rev:
        en_rev = ApprovedRevisionFactory()

        # Make Deutsch translation:
        de_doc = DocumentFactory(parent=en_rev.document, locale='de')
        de_rev = RevisionFactory(document=de_doc)

        # Set based_on to some random, unrelated Document's rev:
        de_rev.based_on = RevisionFactory()

        # Try to recover:
        self.assertRaises(ValidationError, de_rev.clean)

        eq_(en_rev.document.current_revision, de_rev.based_on)

    def test_correct_ready_for_localization_if_unapproved(self):
        """Revision.clean() must clear is_ready_for_l10n if not is_approved."""
        r = RevisionFactory.build(is_approved=False, is_ready_for_localization=True)
        r.clean()
        assert not r.is_ready_for_localization

    def test_correct_ready_for_localization_if_insignificant(self):
        """Revision.clean() must clear is_ready_for_l10n if the rev is of
        typo-level significance."""
        r = ApprovedRevisionFactory(
            is_ready_for_localization=True,
            significance=TYPO_SIGNIFICANCE)
        r.clean()
        assert not r.is_ready_for_localization

    def test_ready_for_l10n_updates_doc(self):
        """Approving and marking ready a rev should update the doc's ref."""
        # Ready a rev in a new doc:
        ready_1 = ApprovedRevisionFactory(is_ready_for_localization=True)
        eq_(ready_1, ready_1.document.latest_localizable_revision)

        # Add an unready revision that we can ready later:
        unready = RevisionFactory(
            document=ready_1.document,
            is_approved=False,
            is_ready_for_localization=False)

        # Ready a rev in a doc that already has a ready revision:
        ready_2 = ApprovedRevisionFactory(
            document=ready_1.document,
            is_ready_for_localization=True)
        eq_(ready_2, ready_2.document.latest_localizable_revision)

        # Ready the older rev. It should not become the latest_localizable.
        unready.is_ready_for_localization = True
        unready.is_approved = True
        unready.save()
        eq_(ready_2, ready_2.document.latest_localizable_revision)

    def test_delete(self):
        """Make sure deleting the latest localizable revision doesn't delete
        the document but instead sets its latest localizable revision to the
        previous one.

        Making sure current_revision does the same is covered in the
        test_delete_current_revision template test.

        """
        r1 = ApprovedRevisionFactory(is_ready_for_localization=True)
        d = r1.document
        r2 = ApprovedRevisionFactory(document=d, is_ready_for_localization=True)

        # Deleting r2 should make the latest fall back to r1:
        r2.delete()
        eq_(r1, Document.objects.get(pk=d.pk).latest_localizable_revision)

        # And deleting r1 should fall back to None:
        r1.delete()
        eq_(None, Document.objects.get(pk=d.pk).latest_localizable_revision)

    def test_delete_rendering(self):
        """Make sure the cached HTML updates when deleting the current rev."""
        unapproved = RevisionFactory(is_approved=False)
        d = unapproved.document
        approved = ApprovedRevisionFactory(document=d, content='booyah')
        assert 'booyah' in d.content_parsed

        # Delete the current rev. Since there are no other approved revs, the
        # document's HTML should fall back to "".
        approved.delete()
        eq_('', d.content_parsed)

        # Now delete the final revision. It still shouldn't crash.
        unapproved.delete()
        eq_('', d.content_parsed)

    def test_previous(self):
        r1 = RevisionFactory(is_approved=True)
        d = r1.document
        r2 = RevisionFactory(document=d, is_approved=True)

        eq_(r1.previous, None)
        eq_(r2.previous.id, r1.id)
