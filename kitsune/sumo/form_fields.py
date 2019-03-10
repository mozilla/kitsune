from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils import translation
from django.utils.translation import ugettext as _

from babel import Locale, localedata
from babel.support import Format


class TypedMultipleChoiceField(forms.MultipleChoiceField):
    """Coerce choices to a specific type and don't validate them.

    Based on implementation in Django ticket 12398.
    Bonus feature: optional coerce_only=True, doesn't raise ValidationError,
    best used in combination with required=False, to pass form validation
    if a field is optional and all you want is value casting.

    """
    def valid_value(self, val):
        """Override: don't raise validation error in parent, if coerce_only."""
        if self.coerce_only:
            return True
        return super(TypedMultipleChoiceField, self).valid_value(val)

    def __init__(self, coerce_only=False, *args, **kwargs):
        self.coerce = kwargs.pop('coerce', lambda val: val)
        self.empty_value = kwargs.pop('empty_value', [])
        self.coerce_only = coerce_only
        super(TypedMultipleChoiceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """
        Validates that the values are in self.choices and can be coerced to the
        right type.
        """
        value = super(TypedMultipleChoiceField, self).to_python(value)
        super(TypedMultipleChoiceField, self).validate(value)
        if value == self.empty_value or value in validators.EMPTY_VALUES:
            return self.empty_value
        new_value = []
        is_valid = super(TypedMultipleChoiceField, self).valid_value
        for choice in value:
            if self.coerce_only and not is_valid(choice):
                continue
            try:
                new_value.append(self.coerce(choice))
            except (ValueError, TypeError, ValidationError):
                raise ValidationError(self.error_messages['invalid_choice'] %
                                      {'value': choice})
        return new_value

    def validate(self, value):
        pass


class MultiUsernameField(forms.Field):
    """Form field that takes a comma-separated list of usernames as input,
    validates that users exist for each one, and returns the list of users."""
    def to_python(self, value):
        if not value:
            if self.required:
                raise forms.ValidationError(_(u'To field is required.'))
            else:
                return []

        users = []
        for username in value.split(','):
            username = username.strip()
            if username:
                try:
                    user = User.objects.get(username=username)
                    users.append(user)
                except User.DoesNotExist:
                    msg = _(u'{username} is not a valid username.')
                    raise forms.ValidationError(msg.format(username=username))

        return users


class BaseValidator(validators.BaseValidator):
    """Override the BaseValidator from django to format numbers."""
    def __call__(self, value):
        cleaned = self.clean(value)
        params = {'limit_value': _format_decimal(self.limit_value),
                  'show_value': _format_decimal(cleaned)}
        if self.compare(cleaned, self.limit_value):
            raise ValidationError(
                self.message % params,
                code=self.code,
                params=params,
            )


def _format_decimal(num, format=None):
    """Returns the string of a number formatted for the current language.

    Uses django's translation.get_language() to find the current language from
    the request.
    Falls back to the default language if babel does not support the current.

    """
    lang = translation.get_language()
    if not localedata.exists(lang):
        lang = settings.LANGUAGE_CODE
    locale = Locale(translation.to_locale(lang))
    return Format(locale).decimal(num, format)
