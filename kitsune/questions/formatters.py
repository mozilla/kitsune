from jinja2.filters import do_striptags
from jingo.helpers import fe
from tower import ugettext as _

from kitsune.activity import ActionFormatter
from kitsune.users.helpers import display_name, profile_url


class AnswerFormatter(ActionFormatter):
    def __init__(self, action):
        title = _(u'<a href="{profile_url}">{user}</a> answered '
                  u'<a href="{answer_url}">{question}</a>')
        self.action = action
        self.answer = action.content_object
        self.title = fe(title, profile_url=profile_url(self.action.creator),
                        user=display_name(self.action.creator),
                        answer_url=self.action.url,
                        question=self.answer.question.title)
        # 225 - determined by experiment.
        self.content = self.answer.content[0:255]

    def __unicode__(self):
        return do_striptags(self.title)
