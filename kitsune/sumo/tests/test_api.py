import json

from nose.tools import eq_

from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.tests import TestCase


class TestLocalesAPIView(TestCase):
    def test_basic(self):
        url = reverse('sumo.locales_api')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        content = json.loads(response.content)

        # Do some spot checks.
        # NB: These checks will break when we change other parts of SUMO.
        eq_(content['en-US'], {
            'name': 'English',
            'localized_name': 'English',
            'aaq_enabled': True
        })

        eq_(content['fr'], {
            'name': 'French',
            'localized_name': 'Fran\xe7ais',
            'aaq_enabled': False
        })
