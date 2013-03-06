from django.core.management import call_command

from sumo.tests import TestCase


class TestGenerateData(TestCase):
    def test_generate_data(self):
        """Make sure ./manage.py generatedata runs."""
        call_command('generatedata')
