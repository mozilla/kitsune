from jinja2.filters import do_striptags
from jingo.helpers import fe
from tower import ugettext as _

from kitsune.activity import ActionFormatter
from kitsune.users.helpers import display_name, profile_url


class ForumReplyFormatter(ActionFormatter):
    def __init__(self, action):
        title = _(u'<a href="{profile_url}">{user}</a> replied to '
                  u'<a href="{post_url}">{thread}</a>')
        self.action = action
        self.post = action.content_object
        self.title = fe(title, profile_url=profile_url(self.action.creator),
                        user=display_name(self.action.creator),
                        post_url=self.action.url,
                        thread=self.post.thread.title)
        # 225 was determined by experiment. Feel free to change if the
        # layout changes.
        self.content = self.post.content[0:225]

    def __unicode__(self):
        return do_striptags(self.title)
