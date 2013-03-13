from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from products.models import Product
from sumo.urlresolvers import reverse
from topics.models import Topic
from wiki.facets import products_for, documents_for
from wiki.models import Document


def topic_landing(request, slug):
    """The topic landing page.

    If `selectproduct=1` query param is passed, shows the product picker.
    Else, shows the list of articles.
    """
    topic = get_object_or_404(Topic, slug=slug)
    topics = Topic.objects.filter(visible=True)

    data = dict(topic=topic, topics=topics)
    if request.GET.get('selectproduct') == '1':
        data.update(products=products_for(topics=[topic]))
    else:
        docs, fallback = documents=documents_for(
            locale=request.LANGUAGE_CODE, topics=[topic])
        data.update(documents=docs, fallback_documents=fallback)

    return render(request, 'topics/topic.html', data)
