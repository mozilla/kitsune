import logging

from django.conf import settings
from django.utils.datastructures import SortedDict

from statsd import statsd
from tower import ugettext_lazy as _lazy
from zendesk import Zendesk, ZendeskError


log = logging.getLogger('k.questions.marketplace')


MARKETPLACE_CATEGORIES = SortedDict([
    ('payments', _lazy('Payments')),
    ('applications', _lazy('Applications')),
    ('account', _lazy('Account')),
])


class ZendeskSettingsError(ZendeskError):
    """Exception for missing settings."""


def get_zendesk():
    """Instantiate and return a Zendesk client"""
    # Verify required Zendesk settings
    zendesk_url = settings.ZENDESK_URL
    zendesk_email = settings.ZENDESK_USER_EMAIL
    zendesk_password = settings.ZENDESK_USER_PASSWORD
    if not zendesk_url or not zendesk_email or not zendesk_password:
        log.error('Zendesk settings error: please set ZENDESK_URL, '
                  'ZENDESK_USER_EMAIL and ZENDESK_USER_PASSWORD.')
        statsd.incr('questions.zendesk.settingserror')
        raise ZendeskSettingsError('Missing Zendesk settings.')

    return Zendesk(
        zendesk_url, zendesk_email, zendesk_password, api_version=2)


def submit_ticket(email, category, subject, body, tags):
    """Submit a marketplace ticket to Zendesk.

    :arg email: user's email address
    :arg category: issue's category
    :arg subject: issue's subject
    :arg body: issue's description
    """
    # Create the Zendesk connection client.
    zendesk = get_zendesk()

    # Create the ticket
    new_ticket = {
        'ticket': {
            'requester_email': email,
            'subject': settings.ZENDESK_SUBJECT_PREFIX + subject,
            'description': body,
            'set_tags': category,
            'tags': tags,
        }
    }
    try:
        ticket_url = zendesk.create_ticket(data=new_ticket)
        statsd.incr('questions.zendesk.success')
    except ZendeskError as e:
        log.error('Zendesk error: %s' % e.msg)
        statsd.incr('questions.zendesk.error')
        raise

    return ticket_url
