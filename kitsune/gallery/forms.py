from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from tower import ugettext_lazy as _lazy, ugettext as _

from kitsune.gallery.models import Image, Video
from kitsune.sumo.form_fields import StrippedCharField
from kitsune.upload.forms import clean_image_extension
from sumo_locales import LOCALES

# Error messages
MSG_TITLE_REQUIRED = _lazy(u'Please provide a title.')
MSG_TITLE_SHORT = _lazy(
    u'The title is too short (%(show_value)s characters). It must be at '
     'least %(limit_value)s characters.')
MSG_TITLE_LONG = _lazy(
    u'Please keep the length of your title to %(limit_value)s characters '
     'or less. It is currently %(show_value)s characters.')
MSG_DESCRIPTION_REQUIRED = _lazy(u'Please provide a description.')
MSG_DESCRIPTION_LONG = _lazy(
    u'Please keep the length of your description to %(limit_value)s '
     'characters or less. It is currently %(show_value)s characters.')
MSG_IMAGE_REQUIRED = _lazy(u'You have not selected an image to upload.')
MSG_IMAGE_LONG = _lazy(
    u'Please keep the length of your image filename to %(max)s '
     'characters or less. It is currently %(length)s characters.')
MSG_WEBM_LONG = _lazy(
    u'Please keep the length of your webm filename to %(max)s '
     'characters or less. It is currently %(length)s characters.')
MSG_OGV_LONG = _lazy(
    u'Please keep the length of your ogv filename to %(max)s '
     'characters or less. It is currently %(length)s characters.')
MSG_FLV_LONG = _lazy(
    u'Please keep the length of your flv filename to %(max)s '
     'characters or less. It is currently %(length)s characters.')
MSG_VID_REQUIRED = _lazy(
    u'The video has no files associated with it. You must upload one of the '
     'following extensions: webm, ogv, flv.')
MSG_TITLE_DRAFT = _lazy(u'Please select a different title.')

TITLE_HELP_TEXT = _lazy(u'Include this in wiki syntax with [[%(type)s:title]]')
DESCRIPTION_HELP_TEXT = _lazy(u'Provide a brief description of this media.')


class UploadTypeForm(forms.Form):
    type = forms.ChoiceField(
        label=_lazy(u'Upload'), initial='image', widget=forms.RadioSelect,
        choices=(('image', _lazy(u'Image')), ('video', _lazy('Video'))))


class MediaForm(forms.ModelForm):
    """Common abstractions for Image and Video forms."""
    locale = forms.ChoiceField(
                    required=False,
                    label=_lazy(u'Locale'),
                    choices=[(k, LOCALES[k].native) for
                             k in settings.SUMO_LANGUAGES],
                    initial=settings.WIKI_DEFAULT_LANGUAGE)
    title = StrippedCharField(
        required=False,
        label=_lazy(u'Title'),
        help_text=TITLE_HELP_TEXT % {'type': u'Image'},
        min_length=5, max_length=255,
        error_messages={'required': MSG_TITLE_REQUIRED,
                        'min_length': MSG_TITLE_SHORT,
                        'max_length': MSG_TITLE_LONG})
    description = StrippedCharField(
        required=False,
        label=_lazy(u'Description'),
        help_text=DESCRIPTION_HELP_TEXT,
        max_length=10000, widget=forms.Textarea(),
        error_messages={'required': MSG_DESCRIPTION_REQUIRED,
                        'max_length': MSG_DESCRIPTION_LONG})

    def __init__(self, *args, **kwargs):
        self.is_ajax = kwargs.pop('is_ajax', True)
        super(MediaForm, self).__init__(*args, **kwargs)
        if not self.is_ajax:
            self.fields['locale'].required = True
            self.fields['title'].required = True
            self.fields['description'].required = True

    def save(self, update_user=None, is_draft=True, **kwargs):
        return save_form(self, update_user, is_draft=is_draft, **kwargs)


class ImageForm(MediaForm):
    """Image form."""
    file = forms.ImageField(error_messages={'required': MSG_IMAGE_REQUIRED,
                                            'max_length': MSG_IMAGE_LONG},
                            label=_lazy('Image'),
                            max_length=settings.MAX_FILENAME_LENGTH)

    def __init__(self, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)
        self.fields['file'].help_text = _(
            u'Accepted formats include: PNG, JPEG, GIF. <a target="_blank" '
            'href="{learn_more}">Learn more...</a>').format(
                learn_more='http://infohost.nmt.edu/tcc/help/pubs/pil/'
                           'formats.html')

    def clean(self):
        c = super(ImageForm, self).clean()
        clean_image_extension(c.get('file'))
        return c

    class Meta:
        model = Image
        fields = ('file', 'locale', 'title', 'description')


class VideoForm(MediaForm):
    """Video form."""
    flv = forms.FileField(
        required=False, error_messages={'max_length': MSG_FLV_LONG},
        max_length=settings.MAX_FILENAME_LENGTH, label=_lazy('Video (flv)'))
    ogv = forms.FileField(required=False, label=_lazy('Video (ogv)'),
                          error_messages={'max_length': MSG_OGV_LONG},
                          max_length=settings.MAX_FILENAME_LENGTH)
    webm = forms.FileField(required=False, label=_lazy('Video (webm)'),
                           error_messages={'max_length': MSG_WEBM_LONG},
                           max_length=settings.MAX_FILENAME_LENGTH)
    thumbnail = forms.ImageField(
        label=_lazy('Thumbnail'),
        required=False, error_messages={'max_length': MSG_IMAGE_LONG},
        max_length=settings.MAX_FILENAME_LENGTH)

    def __init__(self, *args, **kwargs):
        super(VideoForm, self).__init__(*args, **kwargs)
        self.fields['flv'].help_text = _(
            'Select a Flash video (FLV) to upload.')
        self.fields['ogv'].help_text = _('Select an Ogv video to upload.')
        self.fields['webm'].help_text = _('Select a WebM video to upload.')
        self.fields['thumbnail'].help_text = _(
            'Suggested size: {width}x{height}px').format(
                width=settings.THUMBNAIL_SIZE, height=settings.THUMBNAIL_SIZE)

    def clean(self):
        """Ensure one of the supported file formats has been uploaded"""
        c = super(VideoForm, self).clean()
        if not ('webm' in c and c['webm'] and
                    c['webm'].name.endswith('.webm') or
                'ogv' in c and c['ogv'] and
                    (c['ogv'].name.endswith('.ogv') or
                     c['ogv'].name.endswith('.ogg')) or
                'flv' in c and c['flv'] and c['flv'].name.endswith('.flv') or
                'thumbnail' in c and c['thumbnail']):
            raise ValidationError(MSG_VID_REQUIRED)
        clean_image_extension(c.get('thumbnail'))
        return self.cleaned_data

    class Meta:
        model = Video
        fields = ('webm', 'ogv', 'flv', 'thumbnail', 'locale',
                  'title', 'description')


def save_form(form, update_user=None, is_draft=True, **kwargs):
    """Save a media form, add user to updated_by.

    Warning: this assumes you're calling it from a subclass of MediaForm.

    """
    obj = super(MediaForm, form).save(commit=False, **kwargs)
    if update_user:
        obj.updated_by = update_user
    obj.is_draft = is_draft
    obj.save()
    return obj
