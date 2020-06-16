from django import forms
from django.conf import settings
from timeout_decorator import TimeoutError
from waffle import switch_is_active

from kitsune.sumo.utils import match_regex_with_timeout


class KitsuneBaseForumForm(forms.Form):
    """Base form suitable for all the project.

    Mainly adds a common clean method to deal with spam.
    """

    def __init__(self, *args, **kwargs):
        """Override init method to get the user if possible."""
        self.user = kwargs.pop('user', None)
        super(KitsuneBaseForumForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        """Generic clean method used by all forms in the question app.

        Parse content for any toll free numbers.
        """
        cdata = self.cleaned_data.get('content')
        if not cdata:
            return super(KitsuneBaseForumForm, self).clean(*args, **kwargs)

        # At the moment validation doesn't reach this point b/c the logout and deactivation
        # is_spam = is_toll_free_number(cdata)

        # if is_spam:
        #     self.cleaned_data.update({
        #         'is_spam': True
        #     })

        if not self.user:
            raise forms.ValidationError('Something went terribly wrong. Please try again')

        # Allow moderators to post anything
        has_links = False
        if not self.user.has_perm('flagit.can_moderate'):
            if switch_is_active('disallow_all_links'):
                try:
                    has_links = match_regex_with_timeout(settings.GRUBER_V2_URL_REGEX, cdata)
                except TimeoutError:
                    has_links = True

        if has_links:
            raise forms.ValidationError('Links are not allowed in the forums.')
        return self.cleaned_data
