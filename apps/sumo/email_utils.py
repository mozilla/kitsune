from contextlib import contextmanager

from django.utils import translation

import jingo
import tower
from test_utils import RequestFactory


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
    also request.LANGUAGE.

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
