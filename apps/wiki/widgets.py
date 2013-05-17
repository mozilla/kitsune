import collections

from django import forms
from django.conf import settings

import jingo
from test_utils import RequestFactory

from topics.models import Topic
from wiki.config import SIGNIFICANCES_HELP


class TopicsAndSubtopicsWidget(forms.widgets.SelectMultiple):
    """A widget to render topics organized with subtopics."""

    def render(self, name, value, attrs=None):
        topics_and_subtopics = Topic.objects.all()
        topics = [t for t in topics_and_subtopics if t.parent_id is None]

        for topic in topics:
            self.process_topic(value, topic)

            topic.my_subtopics = [t for t in topics_and_subtopics
                                  if t.parent_id == topic.id]

            for subtopic in topic.my_subtopics:
                self.process_topic(value, subtopic)

        # Create a fake request to make jingo happy.
        req = RequestFactory()
        req.META = {}
        req.locale = settings.WIKI_DEFAULT_LANGUAGE

        return jingo.render_to_string(
            req,
            'wiki/includes/topics_widget.html',
            {
                'topics': topics,
                'name': name,
            })

    def process_topic(self, value, topic):
        if isinstance(value, (int, long)) and topic.id == value:
            topic.checked = True
        elif (not isinstance(value, basestring)
              and isinstance(value, collections.Iterable)
              and topic.id in value):
            topic.checked = True
        else:
            topic.checked = False


class RadioInputWithHelpText(forms.widgets.RadioInput):
    """Extend django's RadioInput with some <div class="help-text" />."""
    # NOTE: I tried to have the help text be part of the choices tuple,
    # but it caused all sorts of validation errors in django. For now,
    # just using SIGNIFICANCES_HELP directly here.
    def __init__(self, name, value, attrs, choice, index):
        super(RadioInputWithHelpText, self).__init__(name, value, attrs,
                                                     choice, index)
        self.choice_help = SIGNIFICANCES_HELP[choice[0]]

    def __unicode__(self):
        label = super(RadioInputWithHelpText, self).__unicode__()
        return mark_safe('%s<div class="help-text">%s</div>' %
                         (label, self.choice_help))


class RadioFieldRendererWithHelpText(forms.widgets.RadioFieldRenderer):
    """Modifies django's RadioFieldRenderer to use RadioInputWithHelpText."""
    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield RadioInputWithHelpText(self.name, self.value,
                                         self.attrs.copy(), choice, i)
