import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from mobility.decorators import mobile_template
from product_details import product_details

from kitsune.products.models import Product, Topic
from kitsune.wiki.decorators import check_simple_wiki_locale
from kitsune.wiki.facets import topics_for, documents_for


@check_simple_wiki_locale
@mobile_template('products/{mobile/}products.html')
def product_list(request, template):
    """The product picker page."""
    products = Product.objects.filter(visible=True)
    return render(request, template, {
        'products': products})


@check_simple_wiki_locale
@mobile_template('products/{mobile/}product.html')
def product_landing(request, template, slug):
    """The product landing page."""
    product = get_object_or_404(Product, slug=slug)
    user = request.user

    if request.is_ajax():
        # Return a list of topics/subtopics for the product
        topic_list = list()
        for t in Topic.objects.filter(product=product, visible=True):
            topic_list.append({'id': t.id, 'title': t.title})
        return HttpResponse(json.dumps({'topics': topic_list}),
                            content_type='application/json')

    if slug == 'firefox':
        latest_version = product_details.firefox_versions['LATEST_FIREFOX_VERSION']
    else:
        versions = product.versions.filter(default=True)
        if versions:
            latest_version = versions[0].min_version
        else:
            latest_version = 0

    return render(request, template, {
        'product': product,
        'products': Product.objects.filter(visible=True),
        'topics': topics_for(product=product, parent=None),
        'search_params': {'product': slug},
        'latest_version': latest_version,
        'show_contact_form': user.profile.has_subscriptions if user.is_authenticated() else False
    })


@check_simple_wiki_locale
@mobile_template('products/{mobile/}documents.html')
def document_listing(request, template, product_slug, topic_slug,
                     subtopic_slug=None):
    """The document listing page for a product + topic."""
    product = get_object_or_404(Product, slug=product_slug)
    topic = get_object_or_404(Topic, slug=topic_slug, product=product,
                              parent__isnull=True)

    doc_kw = {'locale': request.LANGUAGE_CODE, 'products': [product]}

    if subtopic_slug is not None:
        subtopic = get_object_or_404(Topic, slug=subtopic_slug,
                                     product=product, parent=topic)
        doc_kw['topics'] = [subtopic]
    else:
        subtopic = None
        doc_kw['topics'] = [topic]

    documents, fallback_documents = documents_for(**doc_kw)

    return render(request, template, {
        'product': product,
        'topic': topic,
        'subtopic': subtopic,
        'topics': topics_for(product=product, parent=None),
        'subtopics': topics_for(product=product, parent=topic),
        'documents': documents,
        'fallback_documents': fallback_documents,
        'search_params': {'product': product_slug},
    })
