import logging
from functools import wraps

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

from premailer import transform
from django.test.client import RequestFactory

from kitsune.sumo.utils import uselocale


log = logging.getLogger('k.email')


def send_messages(messages):
    """Sends a a bunch of EmailMessages."""
    if not messages:
        return

    conn = mail.get_connection(fail_silently=True)
    conn.open()

    for msg in messages:
        conn.send_messages([msg])


def safe_translation(f):
    """Call `f` which has first argument `locale`. If `f` raises an
    exception indicative of a bad localization of a string, try again in
    `settings.WIKI_DEFAULT_LANGUAGE`.

    The translation system will be manipulated so that calls to gettext and
    friends will use the appropriate language.

    NB: This means `f` will be called up to two times!
    """
    @wraps(f)
    def wrapper(locale, *args, **kwargs):
        try:
            with uselocale(locale):
                return f(locale, *args, **kwargs)
        except (TypeError, KeyError, ValueError, IndexError):
            # Types of errors, and examples.
            #
            # TypeError: Not enough arguments for string
            #   '%s %s %s' % ('foo', 'bar')
            # KeyError: Bad variable name
            #   '%(Foo)s' % {'foo': 10} or '{Foo}'.format(foo=10')
            # ValueError: Incomplete Format, or bad format string.
            #    '%(foo)a' or '%(foo)' or '{foo'
            # IndexError: Not enough arguments for .format() style string.
            #    '{0} {1}'.format(42)
            log.exception('Bad translation in locale "%s"', locale)

            with uselocale(settings.WIKI_DEFAULT_LANGUAGE):
                return f(settings.WIKI_DEFAULT_LANGUAGE, *args, **kwargs)

    return wrapper


def render_email(template, context):
    """Renders a template in the currently set locale.

    Falls back to WIKI_DEFAULT_LANGUAGE in case of error.
    """

    @safe_translation
    def _render(locale):
        """Render an email in the given locale.

        Because of safe_translation decorator, if this fails,
        the function will be run again in English.
        """
        req = RequestFactory()
        req.META = {}
        req.locale = locale

        return render_to_string(template, context)

    return _render(translation.get_language())


def make_mail(subject,
              text_template,
              html_template,
              context_vars,
              from_email,
              to_email,
              headers=None,
              **extra_kwargs):
    """Return an instance of EmailMultiAlternative with both plaintext and
    html versions."""
    default_headers = {
        'Reply-To': settings.DEFAULT_REPLY_TO_EMAIL,
    }
    if headers is not None:
        default_headers.update(headers)
    headers = default_headers

    mail = EmailMultiAlternatives(subject,
                                  render_email(text_template, context_vars),
                                  from_email,
                                  [to_email],
                                  headers=headers,
                                  **extra_kwargs)

    if html_template:
        html = transform(render_email(html_template, context_vars),
                         'https://' + Site.objects.get_current().domain)
        mail.attach_alternative(html, 'text/html')

    return mail


def emails_with_users_and_watches(
        subject,
        text_template,
        html_template,
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
    :arg text_template: path to text template file
    :arg html_template: path to html template file
    :arg context_vars: a map which becomes the Context passed in to the
        template and the subject string
    :arg from_email: the from email address
    :arg default_local: the local to default to if not user.profile.locale
    :arg extra_kwargs: additional kwargs to pass into EmailMessage constructor

    :returns: generator of EmailMessage objects

    """
    @safe_translation
    def _make_mail(locale, user, watch):
        context_vars['user'] = user
        context_vars['watch'] = watch[0]
        context_vars['watches'] = watch

        mail = make_mail(subject.format(**context_vars), text_template,
                         html_template, context_vars, from_email, user.email,
                         **extra_kwargs)

        return mail

    for u, w in users_and_watches:
        if hasattr(u, 'profile'):
            locale = u.profile.locale
        else:
            locale = default_locale

        yield _make_mail(locale, u, w)
