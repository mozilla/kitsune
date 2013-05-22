import threading

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.core.urlresolvers import reverse as django_reverse
from django.utils.translation.trans_real import parse_accept_lang_header

# Thread-local storage for URL prefixes. Access with (get|set)_url_prefix.
_locals = threading.local()

def set_url_prefixer(prefixer):
    """Set the Prefixer for the current thread."""
    _locals.prefixer = prefixer


def get_url_prefixer():
    """Get the Prefixer for the current thread, or None."""
    return getattr(_locals, 'prefixer', None)


def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None,
            force_locale=False, locale=None):
    """Wraps Django's reverse to prepend the correct locale.

    force_locale -- Ordinarily, if get_url_prefixer() returns None, we return
        an unlocalized URL, which will be localized via redirect when visited.
        Set force_locale to True to force the insertion of a default locale
        when there is no set prefixer. If you are writing a test and simply
        wish to avoid LocaleURLMiddleware's initial 301 when passing in an
        unprefixed URL, it is probably easier to substitute LocalizingClient
        for any uses of django.test.client.Client and forgo this kwarg.

    locale -- By default, reverse prepends the current locale (if set) or
        the default locale if force_locale == True. To override this behavior
        and have it prepend a different locale, pass in the locale parameter
        with the desired locale. When passing a locale, the force_locale is
        not used and is implicitly True.

    """
    if locale:
        prefixer = Prefixer(locale=locale)
    else:
        prefixer = get_url_prefixer()
        if not prefixer and force_locale:
            prefixer = Prefixer()

    if prefixer:
        prefix = prefix or '/'
    url = django_reverse(viewname, urlconf, args, kwargs, prefix)
    if prefixer:
        return prefixer.fix(url)
    else:
        return url


def find_supported(test):
    return [settings.LANGUAGE_URL_MAP[x] for
            x in settings.LANGUAGE_URL_MAP if
            x.split('-', 1)[0] == test.lower().split('-', 1)[0]]


def get_non_supported(lang):
    """Find known non-supported locales with fallbacks."""
    lang = lang.lower()
    langs = dict((k.lower(), v) for k, v in
                 settings.NON_SUPPORTED_LOCALES.items())
    if lang in langs:
        if langs[lang] is None:
            return settings.LANGUAGE_CODE
        return langs[lang]
    return None


def get_best_language(accept_lang):
    """Given an Accept-Language header, return the best-matching language."""

    LUM = settings.LANGUAGE_URL_MAP
    NSL = settings.NON_SUPPORTED_LOCALES
    LC = settings.LANGUAGE_CODE
    langs = dict(LUM)
    # Add in non-supported first to allow overriding prefix behavior.
    langs.update((k.lower(), v if v else LC) for k, v in NSL.items() if
                 k.lower() not in langs)
    langs.update((k.split('-')[0], v) for k, v in LUM.items() if
                 k.split('-')[0] not in langs)
    ranked = parse_accept_lang_header(accept_lang)
    for lang, _ in ranked:
        lang = lang.lower()
        if lang in langs:
            return langs[lang]
        pre = lang.split('-')[0]
        if pre in langs:
            return langs[pre]
    # Couldn't find any acceptable locale.
    return False


def split_path(path):
    """
    Split the requested path into (locale, path).

    locale will be empty if it isn't found.
    """
    path = path.lstrip('/')

    # Use partition instead of split since it always returns 3 parts
    first, _, rest = path.partition('/')

    lang = first.lower()
    if lang in settings.LANGUAGE_URL_MAP:
        return settings.LANGUAGE_URL_MAP[lang], rest
    elif get_non_supported(lang) is not None:
        return get_non_supported(lang), rest
    else:
        supported = find_supported(first)
        if supported:
            return supported[0], rest
        else:
            return '', path


class Prefixer(object):
    def __init__(self, request=None, locale=None):
        """If request is omitted, fall back to a default locale."""
        # to avoid circular imports
        from users.models import Profile

        self.request = request or WSGIRequest({'REQUEST_METHOD': 'bogus',
                                               'wsgi.input': None})
        self.locale, self.shortened_path = split_path(self.request.path_info)

        # Need to make sure 'user' exists for request. Test
        # test_deprecated_redirect (sumo.tests.test_views.RedirectTests)
        # does not have user in request.
        # We also need to check to see if locale is already given in the url,
        # as that serves as an override.
        if not self.locale and request and hasattr(request, 'user'):
            if request.user.is_anonymous():
                language = request.session.get(settings.LANGUAGE_COOKIE_NAME)
                if language:
                    self.locale = language
            else:
                try:
                    profile = request.user.get_profile()
                except Profile.DoesNotExist:
                    pass
                else:
                    self.locale = profile.locale

        if locale:
            self.locale = locale

    def get_language(self):
        """
        Return a locale code we support on the site using the
        user's Accept-Language header to determine which is best. This
        mostly follows the RFCs but read bug 439568 for details.
        """
        if 'lang' in self.request.GET:
            lang = self.request.GET['lang'].lower()
            if lang in settings.LANGUAGE_URL_MAP:
                return settings.LANGUAGE_URL_MAP[lang]

        if self.request.META.get('HTTP_ACCEPT_LANGUAGE'):
            best = get_best_language(
                self.request.META['HTTP_ACCEPT_LANGUAGE'])
            if best:
                return best

        return settings.LANGUAGE_CODE

    def fix(self, path):
        path = path.lstrip('/')
        url_parts = [self.request.META['SCRIPT_NAME']]

        first_part = path.partition('/')[0]
        if (first_part not in settings.SUPPORTED_NONLOCALES and
            first_part not in settings.LANGUAGE_URL_MAP):
            locale = self.locale if self.locale else self.get_language()
            url_parts.append(locale)

        url_parts.append(path)

        return '/'.join(url_parts)
