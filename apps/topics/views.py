from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

import jingo

from products.models import Product
from sumo.helpers import show_new_sumo
from sumo.urlresolvers import reverse
from topics.models import Topic
from wiki.facets import products_for, documents_for
from wiki.models import Document


def topic_landing(request, slug):
    """The topic landing page.

    If `selectproduct=1` query param is passed, shows the product picker.
    Else, shows the list of articles.
    """
    if not show_new_sumo(request):
        # User should only be able to get here in new IA.
        # Redirect to home page
        return HttpResponseRedirect(reverse('home'))

    topic = get_object_or_404(Topic, slug=slug)

    data = dict(topic=topic)
    if request.GET.get('selectproduct') == '1':
        data.update(products=products_for(topics=[topic]))
    else: 
        data.update(documents=documents_for(
            locale=request.locale, topics=[topic]))

    return jingo.render(request, 'topics/topic.html', data)
