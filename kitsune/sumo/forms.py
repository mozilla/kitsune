from django import forms

from kitsune.sumo.utils import check_for_spam_content

TRUSTED_GROUPS = [
    "Forum Moderators",
    "Administrators",
    "SUMO Locale Leaders",
    "Knowledge Base Reviewers",
    "Reviewers",
    # Temporary workaround to exempt individual users if needed
    "Escape Spam Filtering",
]


class KitsuneBaseForumForm(forms.Form):
    """Base form suitable for all the project.

    Mainly adds a common clean method to deal with spam.
    """

    def __init__(self, *args, **kwargs):
        """Override init method to get the user if possible."""
        self.user = kwargs.pop("user", None)
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
        if not self.user.groups.filter(
            name__in=TRUSTED_GROUPS
        ).exists() and check_for_spam_content(cdata):
            self.cleaned_data.update({"is_spam": True})

        return self.cleaned_data
