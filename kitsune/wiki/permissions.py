import logging

from django.conf import settings


log = logging.getLogger('k.wiki')


# Why is this a mixin if it can only be used for the Document model?
# Good question! My only good reason is to keep the permission related
# code organized and contained in one place.
class DocumentPermissionMixin(object):
    """Adds of permission checking methods to the Document model."""

    def allows(self, user, action):
        """Check if the user has the permission on the document."""

        # If this is kicking up a KeyError it's probably because you typoed!
        return getattr(self, '_allows_%s' % action)(user)

    def _allows_create_revision(self, user):
        """Can the user create a revision for the document?"""
        # For now (ever?), creating revisions isn't restricted at all.
        return True

    def _allows_edit(self, user):
        """Can the user edit the document?"""
        # Document editing isn't restricted until it has an approved
        # revision.
        if not self.current_revision:
            return True

        # Locale leaders and reviewers can edit in their locale.
        locale = self.locale
        if _is_leader(locale, user) or _is_reviewer(locale, user):
            return True

        # And finally, fallback to the actual django permission.
        return user.has_perm('wiki.change_document')

    def _allows_delete(self, user):
        """Can the user delete the document?"""
        # Locale leaders can delete documents in their locale.
        locale = self.locale
        if _is_leader(locale, user):
            return True

        # Fallback to the django permission.
        return user.has_perm('wiki.delete_document')

    def _allows_archive(self, user):
        """Can the user archive the document?"""
        # Just use the django permission.
        return user.has_perm('wiki.archive_document')

    def _allows_edit_keywords(self, user):
        """Can the user edit the document's keywords?"""
        # If the document is in the default locale, just use the
        # django permission.
        # Editing keywords isn't restricted in other locales.
        return (self.locale != settings.WIKI_DEFAULT_LANGUAGE or
                user.has_perm('wiki.edit_keywords'))

    def _allows_edit_needs_change(self, user):
        """Can the user edit the needs change fields for the document?"""
        # If the document is in the default locale, just use the
        # django permission.
        # Needs change isn't used for other locales (yet?).
        return (self.locale == settings.WIKI_DEFAULT_LANGUAGE and
                user.has_perm('wiki.edit_needs_change'))

    def _allows_mark_ready_for_l10n(self, user):
        """"Can the user mark the document as ready for localization?"""
        # If the document is localizable and the user has the django
        # permission, then the user can mark as ready for l10n.
        return (self.is_localizable and
                user.has_perm('wiki.mark_ready_for_l10n'))

    def _allows_review_revision(self, user):
        """Can the user review a revision for the document?"""
        # Locale leaders and reviewers can review revisions in their
        # locale.
        locale = self.locale
        if _is_leader(locale, user) or _is_reviewer(locale, user):
            return True

        # Fallback to the django permission.
        return user.has_perm('wiki.review_revision')

    def _allows_delete_revision(self, user):
        """Can the user delete a document's revisions?"""
        # Locale leaders and reviewers can delete revisions in their
        # locale.
        locale = self.locale
        if _is_leader(locale, user) or _is_reviewer(locale, user):
            return True

        # Fallback to the django permission.
        return user.has_perm('wiki.delete_revision')


def _is_leader(locale, user):
    """Checks if the user is a leader for the given locale.

    Returns False if the locale doesn't exist. This will should only happen
    if we forgot to insert a new locale when enabling it or during testing.
    """
    from kitsune.wiki.models import Locale
    try:
        locale_team = Locale.objects.get(locale=locale)
    except Locale.DoesNotExist:
        log.warning('Locale not created for %s' % locale)
        return False

    return user in locale_team.leaders.all()


def _is_reviewer(locale, user):
    """Checks if the user is a reviewer for the given locale.

    Returns False if the locale doesn't exist. This will should only happen
    if we forgot to insert a new locale when enabling it or during testing.
    """
    from kitsune.wiki.models import Locale
    try:
        locale_team = Locale.objects.get(locale=locale)
    except Locale.DoesNotExist:
        log.warning('Locale not created for %s' % locale)
        return False

    return user in locale_team.reviewers.all()
