import json
from string import ascii_letters

from tower import ugettext_lazy as _lazy

from kitsune.wiki.config import (
    OPERATING_SYSTEMS, GROUPED_OPERATING_SYSTEMS, FIREFOX_VERSIONS,
    GROUPED_FIREFOX_VERSIONS, MOBILE_OPERATING_SYSTEMS,
    DESKTOP_OPERATING_SYSTEMS, MOBILE_FIREFOX_VERSIONS,
    DESKTOP_FIREFOX_VERSIONS)


def _split_browser_slug(slug):
    """Given something like fx35, split it into an alphabetic prefix and a
    suffix, returning a 2-tuple like ('fx', '35')."""
    right = slug.lstrip(ascii_letters)
    left_len = len(slug) - len(right)
    return slug[:left_len], slug[left_len:]


# TODO: This is a mess but should be taken care of in bug 768244.
ALL_OS_JSON = json.dumps(
    dict((o.slug, True) for o in OPERATING_SYSTEMS))
ALL_BROWSER_JSON = json.dumps(
    dict((v.slug, {'product': _split_browser_slug(v.slug)[0],
                   'maxFloatVersion': v.max_version})
         for v in FIREFOX_VERSIONS))
MOBILE_OS_JSON = json.dumps(
    dict((o.slug, True) for o in MOBILE_OPERATING_SYSTEMS))
MOBILE_BROWSER_JSON = json.dumps(
    dict((v.slug, {'product': _split_browser_slug(v.slug)[0],
                   'maxFloatVersion': v.max_version})
         for v in MOBILE_FIREFOX_VERSIONS))
DESKTOP_OS_JSON = json.dumps(
    dict((o.slug, True) for o in DESKTOP_OPERATING_SYSTEMS))
DESKTOP_BROWSER_JSON = json.dumps(
    dict((v.slug, {'product': _split_browser_slug(v.slug)[0],
                   'maxFloatVersion': v.max_version})
         for v in DESKTOP_FIREFOX_VERSIONS))

def _version_groups(versions):
    """Group versions so browser+version pairs can be mapped to {for} slugs.

    See test_version_groups for an example.

    """
    slug_groups = {}
    for v in versions:
        left, right = _split_browser_slug(v.slug)
        slug_groups.setdefault(left, []).append((v.max_version, right))
    for g in slug_groups.itervalues():
        g.sort()
    return slug_groups


ALL_VERSION_GROUP_JSON = json.dumps(
    _version_groups(FIREFOX_VERSIONS))
MOBILE_VERSION_GROUP_JSON = json.dumps(
    _version_groups(MOBILE_FIREFOX_VERSIONS))
DESKTOP_VERSION_GROUP_JSON = json.dumps(
    _version_groups(DESKTOP_FIREFOX_VERSIONS))


def showfor_data(products=None):
    """Return the showfor data required for the passed in products.

    If no products are passed, we will return the showfor data for all
    (mobile + desktop).
    """
    if products is None:
        slugs = ['firefox', 'mobile']
    else:
        slugs = [p.slug for p in products]

    if 'mobile' in slugs and 'firefox' in slugs:
        # Use ALL_*
        return {
            'oses': GROUPED_OPERATING_SYSTEMS,
            'oses_json': ALL_OS_JSON,
            'browsers': GROUPED_FIREFOX_VERSIONS,
            'browsers_json': ALL_BROWSER_JSON,
            'version_group_json': ALL_VERSION_GROUP_JSON}
    elif 'mobile' in slugs:
        # Use MOBILE_*
        return {
            'oses': (((_lazy(u'Mobile:'), 'mobile'),
                     MOBILE_OPERATING_SYSTEMS),),
            'oses_json': MOBILE_OS_JSON,
            'browsers': (((_lazy(u'Mobile:'), 'mobile'),
                         MOBILE_FIREFOX_VERSIONS),),
            'browsers_json': MOBILE_BROWSER_JSON,
            'version_group_json': MOBILE_VERSION_GROUP_JSON}
    else:
        # Use DESKTOP_*
        return {
            'oses': (((_lazy(u'Desktop:'), 'desktop'),
                     DESKTOP_OPERATING_SYSTEMS),),
            'oses_json': DESKTOP_OS_JSON,
            'browsers': (((_lazy(u'Desktop:'), 'desktop'),
                         DESKTOP_FIREFOX_VERSIONS),),
            'browsers_json': DESKTOP_BROWSER_JSON,
            'version_group_json': DESKTOP_VERSION_GROUP_JSON}
