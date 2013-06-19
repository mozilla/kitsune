# -*- coding: utf-8 -*-
from datetime import datetime

from django.template.defaultfilters import slugify

from kitsune.products.models import Product
from kitsune.products.tests import product, topic
from kitsune.sumo.tests import LocalizingClient, TestCase, with_save
from kitsune.users.tests import user
from kitsune.wiki.models import Document, Revision, HelpfulVote, Locale
from kitsune.wiki.config import CATEGORIES, SIGNIFICANCES


class TestCaseBase(TestCase):
    """Base TestCase for the wiki app test cases."""
    client_class = LocalizingClient


# Model makers. These make it clearer and more concise to create objects in
# test cases. They allow the significant attribute values to stand out rather
# than being hidden amongst the values needed merely to get the model to
# validate.

@with_save
def document(**kwargs):
    """Return an empty document with enough stuff filled out that it can be
    saved."""
    defaults = {'category': CATEGORIES[0][0],
                'title': u'đ' + str(datetime.now())}
    defaults.update(kwargs)
    if 'slug' not in kwargs:
        defaults['slug'] = slugify(defaults['title'])
    return Document(**defaults)


@with_save
def revision(**kwargs):
    """Return an empty revision with enough stuff filled out that it can be
    saved.

    Revision's is_approved=False unless you specify otherwise.

    Requires a users fixture if no creator is provided.

    """
    d = kwargs.pop('document', None) or document(save=True)

    defaults = {'summary': 'đSome summary', 'content': u'đSome content',
                'significance': SIGNIFICANCES[0][0],
                'comment': r'đSome comment',
                'creator': kwargs.get('creator', user(save=True)),
                'document': d}
    defaults.update(kwargs)

    return Revision(**defaults)


@with_save
def helpful_vote(**kwargs):
    r = kwargs.pop('revision', None) or revision(save=True)
    defaults = {'created': datetime.now(), 'helpful': False, 'revision': r}
    defaults.update(kwargs)
    return HelpfulVote(**defaults)


@with_save
def locale(**kwargs):
    defaults = {'locale': 'en-US'}
    defaults.update(kwargs)
    return Locale(**defaults)


def translated_revision(locale='de', save=False, **kwargs):
    """Return a revision that is the translation of a default-language one."""
    parent_rev = revision(is_approved=True,
                          is_ready_for_localization=True,
                          save=True)
    translation = document(parent=parent_rev.document, locale=locale,
                           save=True)
    new_kwargs = {'document': translation, 'based_on': parent_rev}
    new_kwargs.update(kwargs)
    return revision(save=save, **new_kwargs)


# I don't like this thing. revision() is more flexible. All this adds is
# is_approved=True, but it doesn't even mention approval in its name.
# TODO: Remove.
def doc_rev(content=''):
    """Save a document and an approved revision with the given content."""
    r = revision(content=content, is_approved=True)
    r.save()
    return r.document, r

# End model makers.


def new_document_data(topic_ids=None, product_ids=None):
    product_ids = product_ids or [product(save=True).id]
    p = Product.objects.get(id=product_ids[0])
    topic_ids = topic_ids or [topic(product=p, save=True).id]
    return {
        'title': 'A Test Article',
        'slug': 'a-test-article',
        'locale': 'en-US',
        'topics': topic_ids,
        'products': product_ids,
        'category': CATEGORIES[0][0],
        'keywords': 'key1, key2',
        'summary': 'lipsum',
        'content': 'lorem ipsum dolor sit amet',
    }
