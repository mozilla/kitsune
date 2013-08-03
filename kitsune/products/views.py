import json

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from mobility.decorators import mobile_template
from taggit.models import Tag

from kitsune.products.models import Product, Topic
from kitsune.topics.models import HOT_TOPIC_SLUG
from kitsune.wiki.facets import topics_for, documents_for
from kitsune.questions.models import Question


@mobile_template('products/{mobile/}products.html')
def product_list(request, template):
    """The product picker page."""
    products = Product.objects.filter(visible=True)
    return render(request, template, {
        'products': products})


@mobile_template('products/{mobile/}product.html')
def product_landing(request, template, slug):
    """The product landing page."""
    product = get_object_or_404(Product, slug=slug)

    if request.is_ajax():
        # Return a list of topics/subtopics for the product
        topic_list = list()
        for t in Topic.objects.filter(product=product, visible=True):
            topic_list.append({'id': t.id, 'title': t.title})
        return HttpResponse(json.dumps({'topics': topic_list}),
                            mimetype='application/json')

    try:
        topic = Topic.objects.get(product=product, slug=HOT_TOPIC_SLUG)

        hot_docs, fallback_hot_docs = documents_for(
            locale=request.LANGUAGE_CODE,
            topics=[topic],
            products=[product])
    except Topic.DoesNotExist:
        # "hot" topic doesn't exist, move on.
        hot_docs = fallback_hot_docs = None

    hot_questions = []
    try:
        hot_tag = Tag.objects.get(slug=HOT_TOPIC_SLUG)
        if request.LANGUAGE_CODE in settings.AAQ_LANGUAGES:
            hot_questions = Question.objects.filter(
                locale=request.LANGUAGE_CODE,
                products=product,
                tags=hot_tag)
            hot_questions = hot_questions.order_by('-created')[:3]
    except Tag.DoesNotExist:
        pass

    return render(request, template, {
        'product': product,
        'products': Product.objects.filter(visible=True),
        'topics': topics_for(products=[product], parent=None),
        'hot_docs': hot_docs,
        'hot_questions': hot_questions,
        'fallback_hot_docs': fallback_hot_docs,
        'search_params': {'product': slug}})


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
        'topics': topics_for(products=[product], parent=None),
        'subtopics': topics_for(products=[product], parent=topic),
        'documents': documents,
        'fallback_documents': fallback_documents,
        'search_params': {'product': product_slug}})
