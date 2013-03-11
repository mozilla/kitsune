from contextlib import contextmanager

from django.conf import settings
from django.core import mail
from django.core.mail import EmailMessage
from django.utils import translation

import jingo
import tower
from test_utils import RequestFactory


def send_messages(messages):
    """Sends a a bunch of EmailMessages."""
    conn = mail.get_connection(fail_silently=True)
    conn.open()

    for msg in messages:
        conn.send_messages([msg])


@contextmanager
def uselocale(locale):
    """Context manager for setting locale and returning
    to previous locale.

    This is useful for when doing translations for things run by
    celery workers or out of the HTTP request handling path.

    >>> with uselocale('xx'):
    ...     subj = _('Subject of my email')
    ...     msg = render_email(email_template, email_kwargs)
    ...     mail.send_mail(subj, msg, ...)
    ...

    In Kitsune, you can get the right locale from Profile.locale and
    also request.LANGUAGE_CODE.

    If Kitsune is handling an HTTP request already, you don't have to
    run uselocale---the locale will already be set correctly.

    """
    currlocale = translation.get_language()
    tower.activate(locale)
    yield
    tower.activate(currlocale)


def render_email(template, context):
    """Renders a template in the currently set locale."""
    req = RequestFactory()
    req.META = {}
    req.locale = translation.get_language()

    return jingo.render_to_string(req, template, context)


def emails_with_users_and_watches(subject,
                                  template_path,
                                  context_vars,
                                  users_and_watches,
                                  from_email=settings.TIDINGS_FROM_ADDRESS,
                                  default_locale=settings.WIKI_DEFAULT_LANGUAGE,
                                  **extra_kwargs):
    """Return iterable of EmailMessages with user and watch values substituted.

    A convenience function for generating emails by repeatedly
    rendering a Django template with the given ``context_vars`` plus a
    ``user`` and ``watches`` key for each pair in
    ``users_and_watches``

    .. Note::

       This is a locale-aware re-write of the same function in django-tidings.
       It's kind of goofy--I ain't gonna lie.

    :arg subject: lazy gettext subject string
    :arg template_path: path to template file
    :arg context_vars: a map which becomes the Context passed in to the template
        and the subject string
    :arg from_email: the from email address
    :arg default_local: the local to default to if not user.profile.locale
    :arg extra_kwargs: additional kwargs to pass into EmailMessage constructor

    :returns: generator of EmailMessage objects

    """
    for u, w in users_and_watches:
        if hasattr(u, 'profile'):
            locale = u.profile.locale
        else:
            locale = default_locale

        with uselocale(locale):
            context_vars['user'] = u
            context_vars['watch'] = w[0]
            context_vars['watches'] = w

            yield EmailMessage(subject.format(**context_vars),
                               render_email(template_path, context_vars),
                               from_email,
                               [u.email],
                               **extra_kwargs)
