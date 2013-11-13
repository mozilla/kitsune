from itertools import chain
from string import ascii_letters

from tower import ugettext_lazy as _lazy

from kitsune.products.models import Product, Version, Platform


def _split_browser_slug(slug):
    """Given something like fx35, split it into an alphabetic prefix and a
    suffix, returning a 2-tuple like ('fx', '35')."""
    right = slug.lstrip(ascii_letters)
    left_len = len(slug) - len(right)
    return slug[:left_len], slug[left_len:]


def showfor_data(products):
    def order(obj):
        return obj.display_order

    # This is all a little gross, but it is 90% smaller than just
    # dumping the models to json.

    data = {
        'products': [],
        'versions': {},
        'platforms': [],
    }

    for prod in sorted(products, key=order):
        if prod.visible:
            data['products'].append({
                'title': prod.title,
                'slug': prod.slug,
                'platforms': [plat.slug for plat in
                              prod.platforms.filter(visible=True)],
            })

    all_versions = dict((p.slug, p.versions.filter(visible=True))
                        for p in products)
    # data['versions'] = dict((p.slug, p.versions.all()) for p in products)
    for slug, versions in all_versions.items():
        data['versions'][slug] = []
        for version in versions:
            data['versions'][slug].append({
                'name': version.name,
                'slug': version.slug,
                'product': version.product.slug,
                'default': version.default,
                'min_version': version.min_version,
                'max_version': version.max_version,
            })

    # Get every platform, for every product. The result will have no
    # duplicates, and will be dicts like {'name': ..., 'slug': ...}
    platforms = set()
    for prod in products:
        platforms.update(prod.platforms.filter(visible=True))
    data['platforms'] = [{'name': plat.name, 'slug': plat.slug}
                         for plat in sorted(platforms, key=order)]

    return data
