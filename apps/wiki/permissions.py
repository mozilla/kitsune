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
        locale = self.locale

        if action == 'create_revision':
            # For now (ever?), creating revisions isn't restricted at all.
            return True

        if action == 'edit':
            # Document editing isn't restricted until it has an approved
            # revision.
            if not self.current_revision:
                return True

            # Locale leaders and reviewers can edit in their locale.
            if _is_leader(locale, user) or _is_reviewer(locale, user):
                return True

            # And finally, fallback to the actual django permission.
            return user.has_perm('wiki.change_document')

        if action == 'delete':
            # Locale leaders can delete documents in their locale.
            if _is_leader(locale, user):
                return True

            # Fallback to the django permission.
            return user.has_perm('wiki.delete_document')

        if action == 'archive':
            # Just use the django permission.
            return user.has_perm('wiki.archive_document')

        if action == 'edit_keywords':
            # If the document is in the default locale, just use the
            # django permission.
            # Editing keywords isn't restricted in other locales.
            return (self.locale != settings.WIKI_DEFAULT_LANGUAGE or
                    user.has_perm('wiki.edit_keywords'))

        if action == 'edit_needs_change':
            # If the document is in the default locale, just use the
            # django permission.
            # Needs change isn't used for other locales (yet?).
            return (self.locale == settings.WIKI_DEFAULT_LANGUAGE and
                    user.has_perm('wiki.edit_needs_change'))

        if action == 'mark_ready_for_l10n':
            # If the document is localizable and the user has the django
            # permission, then the user can mark as ready for l10n.
            return (self.is_localizable and
                    user.has_perm('wiki.mark_ready_for_l10n'))

        if action == 'review_revision':
            # Locale leaders and reviewers can review revisions in their
            # locale.
            if _is_leader(locale, user) or _is_reviewer(locale, user):
                return True

            # Fallback to the django permission.
            return user.has_perm('wiki.review_revision')

        if action == 'delete_revision':
            # Locale leaders and reviewers can delete revisions in their
            # locale.
            if _is_leader(locale, user) or _is_reviewer(locale, user):
                return True

            # Fallback to the django permission.
            return user.has_perm('wiki.delete_revision')

        return False


def _is_leader(locale, user):
    """Checks if the user is a leader for the given locale.

    Returns False if the locale doesn't exist. This will should only happen
    if we forgot to insert a new locale when enabling it or during testing.
    """
    from wiki.models import Locale
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
    from wiki.models import Locale
    try:
        locale_team = Locale.objects.get(locale=locale)
    except Locale.DoesNotExist:
        log.warning('Locale not created for %s' % locale)
        return False

    return user in locale_team.reviewers.all()
