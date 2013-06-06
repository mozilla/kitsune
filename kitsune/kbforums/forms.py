from django import forms

from tower import ugettext_lazy as _lazy

from kitsune.kbforums.models import Thread, Post
from kitsune.sumo.form_fields import StrippedCharField


MSG_TITLE_REQUIRED = _lazy(u'Please provide a title.')
MSG_TITLE_SHORT = _lazy(u'Your title is too short (%(show_value)s '
                        u'characters). It must be at least %(limit_value)s '
                        u'characters.')
MSG_TITLE_LONG = _lazy(u'Please keep the length of your title to '
                       u'%(limit_value)s characters or less. It is '
                       u'currently %(show_value)s characters.')
MSG_CONTENT_REQUIRED = _lazy(u'Please provide a message.')
MSG_CONTENT_SHORT = _lazy(u'Your message is too short (%(show_value)s '
                          u'characters). It must be at least %(limit_value)s '
                          u'characters.')
MSG_CONTENT_LONG = _lazy(u'Please keep the length of your message to '
                         u'%(limit_value)s characters or less. It is '
                         u'currently %(show_value)s characters.')


class ReplyForm(forms.ModelForm):
    """Reply form for forum threads."""
    content = StrippedCharField(
                label=_lazy('Content:'),
                min_length=5,
                max_length=10000,
                widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
                error_messages={'required': MSG_CONTENT_REQUIRED,
                                'min_length': MSG_CONTENT_SHORT,
                                'max_length': MSG_CONTENT_LONG})

    class Meta:
        model = Post
        fields = ('content', )


class NewThreadForm(forms.Form):
    """Form to start a new thread."""
    title = StrippedCharField(min_length=5, max_length=255,
                              label=_lazy('Title:'),
                              widget=forms.TextInput(attrs={'size': 80}),
                              error_messages={'required': MSG_TITLE_REQUIRED,
                                              'min_length': MSG_TITLE_SHORT,
                                              'max_length': MSG_TITLE_LONG})
    content = StrippedCharField(
                label=_lazy('Content:'),
                min_length=5,
                max_length=10000,
                widget=forms.Textarea(attrs={'rows': 30, 'cols': 76}),
                error_messages={'required': MSG_CONTENT_REQUIRED,
                                'min_length': MSG_CONTENT_SHORT,
                                'max_length': MSG_CONTENT_LONG})


class EditThreadForm(forms.ModelForm):
    """Form to start a new thread."""
    title = StrippedCharField(min_length=5, max_length=255,
                              label=_lazy('Title:'),
                              widget=forms.TextInput(attrs={'size': 80}),
                              error_messages={'required': MSG_TITLE_REQUIRED,
                                              'min_length': MSG_TITLE_SHORT,
                                              'max_length': MSG_TITLE_LONG})

    class Meta:
        model = Thread
        fields = ('title',)


class EditPostForm(forms.Form):
    """Form to edit an existing post."""
    content = StrippedCharField(
            label=_lazy('Content:'),
            min_length=5,
            max_length=10000,
            widget=forms.Textarea(attrs={'rows': 30, 'cols': 76}),
            error_messages={'required': MSG_CONTENT_REQUIRED,
                            'min_length': MSG_CONTENT_SHORT,
                            'max_length': MSG_CONTENT_LONG})

    class Meta:
        model = Post
        exclude = ('thread', 'author', 'updated', 'created', 'updated_by')
