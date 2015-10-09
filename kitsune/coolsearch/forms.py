from tower import ugettext_lazy as _lazy

from django import forms
from django.conf import settings

from kitsune.lib.sumo_locales import LOCALES
from kitsune.products.models import Product, Topic
from kitsune.sumo.form_fields import TypedMultipleChoiceField
from kitsune.wiki.config import CATEGORIES


SEARCH_LANGUAGES = [
    (k, LOCALES[k].native)
    for k in settings.SUMO_LANGUAGES
]


class SearchForm(forms.Form):
    """Base form for searching. """
    query = forms.CharField(required=False)


class WikiSearchForm(SearchForm):
    """Django form specifically for querying the knowledge base data. """
    language = forms.ChoiceField(
        required=False,
        label=_lazy(u'Language'),
        choices=SEARCH_LANGUAGES
    )

    category = TypedMultipleChoiceField(
        required=False,
        coerce=int,
        label=_lazy(u'Category'),
        choices=CATEGORIES,
        coerce_only=True,
    )

    topics = forms.MultipleChoiceField(
        required=False,
        label=_lazy(u'Topics')
    )

    product = forms.MultipleChoiceField(
        required=False,
        label=_lazy(u'Relevant to'),
    )

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        product_field = self.fields['product']
        product_field.choices = Product.objects.values_list('slug', 'title')

        topics_field = self.fields['topics']
        topics_field.choices = (
            Topic.objects.values_list('slug', 'title').distinct()
        )


class QuestionSearchForm(SearchForm):
    """Django form specifically for querying the questions data. """
    topics = forms.MultipleChoiceField(
        required=False,
        label=_lazy(u'Topics')
    )

    product = forms.MultipleChoiceField(
        required=False,
        label=_lazy(u'Relevant to'),
    )

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        product_field = self.fields['product']
        product_field.choices = Product.objects.values_list('slug', 'title')

        topics_field = self.fields['topics']
        topics_field.choices = (
            Topic.objects.values_list('slug', 'title').distinct()
        )


class ForumSearchForm(SearchForm):
    """Django form specifically for querying the forum data. """
