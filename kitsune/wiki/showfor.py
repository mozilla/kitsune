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
        data['products'].append({
            'title': prod.title,
            'slug': prod.slug,
            'platforms': [plat.slug for plat in prod.platforms.all()],
            'visible': prod.visible,
        })

    all_versions = dict((p.slug, p.versions.all())
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
                'visible': version.visible,
            })

    # Get every platform, for every product. The result will have no
    # duplicates, and will be dicts like {'name': ..., 'slug': ...}
    platforms = set()
    for prod in products:
        platforms.update(prod.platforms.all())
    data['platforms'] = []
    for plat in sorted(platforms, key=order):
        data['platforms'].append({
            'name': plat.name,
            'slug': plat.slug,
            'visible': plat.visible,
        })

    return data
