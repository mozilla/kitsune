from products.models import Product
from topics.models import Topic
from wiki.models import Document


# !!!!! TODO: !!!!!
# Catch errors, add caching and redundancy and whatever to minimize
# the chance of returning a server error or empty list due to ES
# being down. See Bug 781402
def products_for(topics):
    """Returns a list of products that apply to passed in topics.

    :arg topics: a list of Topic instances
    """
    product_field = 'document_product'

    s = Document.search().values_dict('id')
    for topic in topics:
        s = s.filter(document_topic=topic.slug)
    s = s.facet(product_field, filtered=True)
    facet_counts = s.facet_counts()[product_field]

    products = Product.objects.filter(
        slug__in=[f['term'] for f in facet_counts]).filter(visible=True)

    return products


def topics_for(products):
    """Returns a list of topics that apply to passed in products.

    :arg topics: a list of Product instances
    """
    topic_field = 'document_topic'

    s = Document.search().values_dict('id')
    for product in products:
        s = s.filter(document_product=product.slug)
    s = s.facet(topic_field, filtered=True)
    facet_counts = s.facet_counts()[topic_field]

    topics = Topic.objects.filter(
        slug__in=[f['term'] for f in facet_counts]).filter(visible=True)

    return topics


def documents_for(locale, topics, products=None):
    """Returns a list of articles that apply to passed in topics and products.

    :arg locale: the locale
    :arg topics: a list of Topic instances
    :arg products: (optional) a list of Product instances

    The articles are returned as a list of dicts with the following keys:
        id
        document_title
        url
    """
    s = Document.search().values_dict('id', 'document_title', 'url')
    for topic in topics:
        s = s.filter(document_topic=topic.slug)
    for product in products or []:
        s = s.filter(document_product=product.slug)

    return list(s)
