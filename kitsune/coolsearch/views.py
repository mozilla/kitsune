from rest_framework.renderers import JSONRenderer

from django.shortcuts import render

from tower import ugettext_lazy as _lazy

from kitsune.coolsearch.forms import WikiSearchForm


def _options_tuple_to_dict(options):
    return [
        dict(value=x[0], label=x[1])
        for x in options
    ]


def search(request):
    to_json = JSONRenderer().render
    context = {}
    form = WikiSearchForm()

    # Get options to fill the various select boxes of the search forms.
    languages = _options_tuple_to_dict(form.fields['language'].choices)
    categories = _options_tuple_to_dict(form.fields['category'].choices)
    products = _options_tuple_to_dict(form.fields['product'].choices)
    topics = _options_tuple_to_dict(form.fields['topics'].choices)

    filters = {
        'language': {
            'meta': {
                'name': 'language',
                'label': _lazy(u'Language'),
                'multi': False,
            },
            'options': languages,
        },
        'category': {
            'meta': {
                'name': 'category',
                'label': _lazy(u'Category'),
                'multi': True,
            },
            'options': categories,
        },
        'product': {
            'meta': {
                'name': 'product',
                'label': _lazy(u'Relevant to'),
                'multi': True,
            },
            'options': products,
        },
        'topics': {
            'meta': {
                'name': 'topics',
                'label': _lazy(u'Topics'),
                'multi': True,
            },
            'options': topics,
        },
    }
    context['filters_json'] = to_json(filters)

    return render(request, 'coolsearch/search.html', context)
