from itertools import chain

import yaml

from kitsune.products.models import Product, Topic


def get_taxonomy(product_slug=None, **kwargs):
    """
    Print the taxonomy as YAML for the given product
    or for all products if no product slug is given.
    """

    def clean(text):
        return text.replace("\u2019", "'")

    result = dict(products=[])

    if product_slug:
        products = [Product.active.get(slug=product_slug)]
    else:
        products = chain(
            Product.active.filter(visible=True),
            Product.active.filter(slug="mozilla-account"),
        )

    for product in products:
        pdict = dict(title=product.title, description=clean(product.description), topics=[])
        result["products"].append(pdict)
        for t1 in Topic.active.filter(
            products=product, parent=None, visible=True, **kwargs
        ).order_by("title"):
            t1_dict = dict(title=t1.title, description=clean(t1.description), subtopics=[])
            pdict["topics"].append(t1_dict)
            for t2 in Topic.active.filter(
                products=product, parent=t1, visible=True, **kwargs
            ).order_by("title"):
                t2_dict = dict(title=t2.title, description=clean(t2.description), subtopics=[])
                t1_dict["subtopics"].append(t2_dict)
                for t3 in Topic.active.filter(
                    products=product, parent=t2, visible=True, **kwargs
                ).order_by("title"):
                    t2_dict["subtopics"].append(
                        dict(title=t3.title, description=clean(t3.description))
                    )

    return print(yaml.dump(result, sort_keys=False))
