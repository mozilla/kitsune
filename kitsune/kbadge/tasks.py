from django.conf import settings

from celery.task import task
from tower import ugettext as _

from kitsune.sumo import email_utils


@task
def send_award_notification(award):
    """Sends the award notification email

    :arg award: the django-badger Award instance

    """
    @email_utils.safe_translation
    def _make_mail(locale, context, email):
        mail = email_utils.make_mail(
            subject=_('You have been awarded a badge!'),  # TODO: make this suck less
            text_template='kbadge/email/award_notification.ltxt',
            html_template='kbadge/email/award_notification.html',
            context_vars=context,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=email)

        return mail

    msg = _make_mail(
        locale=award.user.profile.locale,
        context={
            'badge_title': award.badge.title,  # TODO: l10nize this!
            'badge_description': award.badge.description,  # TODO: l10nize this!
            'badge_image': award.badge.image,  # TODO: this is an unbaked image!
            'award_description': award.description,
            'award_awardee': award.user,
            'award_awarder': award.creator,
            'award_url': award.get_absolute_url(),
        },
        email=award.user.email
    )

    # FIXME: this sends emails to the person who was awarded the
    # badge. Should we also send an email to the person who awarded
    # the badge? Currently, I think we shouldn't.

    email_utils.send_messages([msg])
