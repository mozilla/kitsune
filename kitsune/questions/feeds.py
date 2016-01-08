from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.utils.feedgenerator import Atom1Feed
from django.utils.html import strip_tags, escape
from django.utils.translation import ugettext as _

from taggit.models import Tag

from kitsune.products.models import Product, Topic
from kitsune.questions import config
from kitsune.questions.models import Question
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.templatetags.jinja_helpers import urlparams


class QuestionsFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request):
        query = {}

        product_slug = request.GET.get('product')
        topic_slug = request.GET.get('topic')
        locale = request.LANGUAGE_CODE

        if product_slug and product_slug != 'all':
            query['product'] = get_object_or_404(Product, slug=product_slug)

            if topic_slug:
                query['topic'] = get_object_or_404(Topic, slug=topic_slug,
                                                   product__slug=product_slug)
        if locale:
            query['locale'] = locale

        return query

    def title(self):
        return _('Recently updated questions')

    def link(self, query):
        slugs = {}

        if 'product' in query:
            slugs['product'] = query['product'].slug

            if 'topic' in query:
                slugs['topic'] = query['topic'].slug

        url = reverse('questions.list', args=[slugs.get('product', 'all')],
                      locale=query.get('locale'))
        return urlparams(url, **slugs)

    def items(self, query):
        qs = Question.objects.filter(creator__is_active=True, is_spam=False)

        if 'product' in query:
            qs = qs.filter(product=query['product'])

            if 'topic' in query:
                qs = qs.filter(topic=query['topic'])

        if 'locale' in query:
            qs = qs.filter(locale=query['locale'])

        return qs.order_by('-updated')[:config.QUESTIONS_PER_PAGE]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return escape(item.content_parsed)

    def item_author_name(self, item):
        return item.creator

    def item_pubdate(self, item):
        return item.created


class TaggedQuestionsFeed(QuestionsFeed):

    def get_object(self, request, tag_slug):
        return get_object_or_404(Tag, slug=tag_slug)

    def title(self, tag):
        return _('Recently updated questions tagged %s' % tag.name)

    def link(self, tag):
        return urlparams(reverse('questions.list', args=['all']),
                         tagged=tag.slug)

    def items(self, tag):
        qs = Question.objects.filter(creator__is_active=True,
                                     tags__name__in=[tag.name],
                                     is_spam=False).distinct()
        return qs.order_by('-updated')[:config.QUESTIONS_PER_PAGE]


class AnswersFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, question_id):
        return get_object_or_404(Question, pk=question_id)

    def title(self, question):
        return _('Recent answers to %s') % question.title

    def link(self, question):
        return question.get_absolute_url()

    def description(self, question):
        return self.title(question)

    def items(self, question):
        return question.answers.filter(is_spam=False).order_by('-created')

    def item_title(self, item):
        return strip_tags(item.content_parsed)[:100]

    def item_description(self, item):
        return escape(item.content_parsed)

    def item_author_name(self, item):
        return item.creator

    def item_pubdate(self, item):
        return item.created
