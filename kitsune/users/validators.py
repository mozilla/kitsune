import re
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


TwitterValidator = RegexValidator(r'^[\w]+$',
                                  message='Please enter correct Twitter Handle',
                                  code='Invalid name')


def FacebookValidator(facebook_username):

    # Check if the facebook username is correct
    facebook_username = re.sub(r'https?://(?:www\.)?facebook\.com/(?:profile.php\?id=)?', '',
                               facebook_username)

    if '/' in facebook_username[-1]:
        raise ValidationError('Your Facebook username is containing slash "/" at the end.'
                              ' Please remove it')

    if not re.match(r'^\w.+$', facebook_username):
        raise ValidationError('Your Facebook username is incorrect. Facebook username can'
                              ' contain only Letters, Numbers, Dot and Underscore')

    if len(facebook_username) > 50:
        raise ValidationError('Facebok username can not be longer than 50 charectors')
