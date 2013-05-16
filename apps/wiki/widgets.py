import collections

from django import forms
from django.utils.safestring import mark_safe

from topics.models import Topic
from wiki.config import SIGNIFICANCES_HELP


class TopicsAndSubtopicsWidget(forms.widgets.SelectMultiple):
    """A widget to render topics organized with subtopics."""

    def render(self, name, value, attrs=None):
        topics_and_subtopics = Topic.objects.all()
        topics = [t for t in topics_and_subtopics if t.parent_id is None]

        output = [u'<ul class="topics">']
        for topic in topics:
            output.append(u'<li>')
            output.append(
                self.render_topic(name, value, topic.id, topic.title))

            subtopics = [t for t in topics_and_subtopics
                         if t.parent_id == topic.id]
            if subtopics:
                output.append(u'<ul class="subtopics">')
                for subtopic in subtopics:
                    output.append(u'<li>')
                    output.append(self.render_topic(
                        name, value, subtopic.id, subtopic.title))
                    output.append(u'</li>')
                output.append(u'</ul>')
            output.append(u'</li>')

        output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))

    def render_topic(self, name, value, topic_id, title):
        if isinstance(value, (int, long)) and topic_id == value:
            checked = u' checked'
        elif (not isinstance(value, basestring)
              and isinstance(value, collections.Iterable)
              and topic_id in value):
            checked = u' checked'
        else:
            checked = u''

        return (
            u'<label><input type="checkbox" name="%s" value="%s"%s/> %s'
            u'</label>' % (name, topic_id, checked, title))


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
