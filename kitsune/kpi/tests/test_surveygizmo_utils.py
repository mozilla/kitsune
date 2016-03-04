from datetime import datetime

from mock import patch
from nose.tools import eq_, ok_

from kitsune.kpi.surveygizmo_utils import (
    add_email_to_campaign,
    get_email_addresses,
    get_exit_survey_results
)
from kitsune.sumo.tests import TestCase


class GetEmailAddressesTests(TestCase):
    @patch('kitsune.kpi.surveygizmo_utils.requests')
    def test_early_exit(self, mock_requests):
        """
        If there are no creds, don't hit the API and return an empty
        list.
        """
        with self.settings(SURVEYGIZMO_API_TOKEN=None,
                           SURVEYGIZMO_API_TOKEN_SECRET=None):
            emails = get_email_addresses(
                'general',
                datetime(2016, 1, 1),
                datetime(2016, 1, 2)
            )

            eq_(emails, [])
            ok_(not mock_requests.get.called)

    @patch('kitsune.kpi.surveygizmo_utils.requests')
    def test_creds(self, mock_requests):
        """Ensure the token and secret are passed correctly."""
        mock_requests.get.return_value.content = SURVEY_GIZMO_EMPTY_RESPONSE

        with self.settings(SURVEYGIZMO_API_TOKEN='mytoken',
                           SURVEYGIZMO_API_TOKEN_SECRET='mysecret'):
            get_email_addresses('general', datetime(2016, 1, 1), datetime(2016, 1, 2))

            url = mock_requests.get.call_args[0][0]
            ok_('api_token=mytoken' in url)
            ok_('api_token_secret=mysecret' in url)


class AddEmailToCampaignTests(TestCase):
    @patch('kitsune.kpi.surveygizmo_utils.requests')
    def test_early_exit(self, mock_requests):
        """
        If there are no creds, don't hit the API and return an empty
        list.
        """
        with self.settings(SURVEYGIZMO_API_TOKEN=None,
                           SURVEYGIZMO_API_TOKEN_SECRET=None):
            add_email_to_campaign('general', 'a@example.com')
            ok_(not mock_requests.put.called)

    @patch('kitsune.kpi.surveygizmo_utils.requests')
    def test_creds(self, mock_requests):
        """Ensure the token and secret are passed correctly."""
        with self.settings(SURVEYGIZMO_API_TOKEN='mytoken',
                           SURVEYGIZMO_API_TOKEN_SECRET='mysecret'):
            add_email_to_campaign('general', 'a@example.com')

            url = mock_requests.put.call_args[0][0]
            ok_('api_token=mytoken' in url)
            ok_('api_token_secret=mysecret' in url)


class GetExitSurveyResults(TestCase):
    @patch('kitsune.kpi.surveygizmo_utils.requests')
    def test_early_exit(self, mock_requests):
        """
        If there are no creds, don't hit the API and return an empty
        list.
        """
        with self.settings(SURVEYGIZMO_API_TOKEN=None,
                           SURVEYGIZMO_API_TOKEN_SECRET=None):
            summary = get_exit_survey_results('general', datetime(2016, 1, 1))
            eq_(summary, {'yes': 0, 'no': 0, 'dont-know': 0})
            ok_(not mock_requests.put.called)

    @patch('kitsune.kpi.surveygizmo_utils.requests')
    def test_creds(self, mock_requests):
        """Ensure the token and secret are passed correctly."""
        mock_requests.get.return_value.content = SURVEY_GIZMO_EMPTY_RESPONSE

        with self.settings(SURVEYGIZMO_API_TOKEN='mytoken',
                           SURVEYGIZMO_API_TOKEN_SECRET='mysecret'):
            get_exit_survey_results('general', datetime(2016, 1, 1))

            url = mock_requests.get.call_args[0][0]
            ok_('api_token=mytoken' in url)
            ok_('api_token_secret=mysecret' in url)


SURVEY_GIZMO_EMPTY_RESPONSE = """
{
    "total_count": "0",
    "total_pages": 1,
    "results_per_page": "500",
    "result_ok": true,
    "data": [],
    "page": "1"
}
"""
