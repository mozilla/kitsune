import requests
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


TwitterValidator = RegexValidator(r'^[\w]+$',
                                  message='Please enter correct Twitter Handle',
                                  code='Invalid name')


def FacebookValidator(facebook_url):

    # Check if the facebook profile URL is correct by using Facebook Graph API.
    if facebook_url:
        facebook_graph_url = facebook_url.replace(
            'www.facebook.com', 'graph.facebook.com').replace(
            'facebook.com', 'graph.facebook.com').replace(
            'profile.php?id=', '')
        facebook_profile_data = requests.get(facebook_graph_url).json()

        try:
            facebook_profile_data['username']
            return False
        except:
            raise ValidationError('Facebook profile URL is wrong. Please enter correct URL')
