from django import forms

from kitsune.sumo.utils import check_for_spam_content, is_trusted_user


class KitsuneBaseForumForm(forms.Form):
    """Base form suitable for all the project.

    Mainly adds a common clean method to deal with spam.
    """

    def __init__(self, *args, **kwargs):
        """Override init method to get the user if possible."""
        self.user = kwargs.pop("user", None)
        self.question = kwargs.pop("question", None)
        super(KitsuneBaseForumForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        """Generic clean method used by all forms in the question app.

        Parse content for suspicious content.
        - Toll free numbers
        - NANP numbers
        - Links - not necessarily spam content
        """

        cdata = self.cleaned_data.get("content")
        if not cdata:
            return super(KitsuneBaseForumForm, self).clean(*args, **kwargs)

        if not self.user:
            raise forms.ValidationError("Something went terribly wrong. Please try again")

        # Exclude moderators and trusted contributors
        if not (
            is_trusted_user(self.user)
            or self.user.has_perm("flagit.can_moderate")
            or self.user.has_perm("sumo.bypass_ratelimit")
        ) and check_for_spam_content(cdata):
            self.cleaned_data.update({"is_spam": True})

        return self.cleaned_data
