import mock
from nose.tools import eq_
from pyquery import PyQuery as pq
from zendesk import Zendesk

import questions
from questions.marketplace import submit_ticket
import questions.views
from sumo.tests import TestCase, LocalizingClient, get, post
from users.tests import user


class MarketplaceAaqTests(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(MarketplaceAaqTests, self).setUp()

        self.user = user(email='s@s.com', save=True)
        self.client.login(username=self.user.username, password='testpass')

    def test_aaq_page(self):
        """Verify the initial AAQ page."""
        response = get(self.client, 'questions.marketplace_aaq')
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(3, len(doc('ul.select-one li')))

    def test_invalid_category(self):
        """Invalid category slug should result in 404"""
        response = get(self.client,
                       'questions.marketplace_aaq_category',
                       args=['invalid-category'])
        eq_(404, response.status_code)

    def test_payments_category(self):
        """Verify the payments category page."""
        response = get(self.client,
                       'questions.marketplace_aaq_category',
                       args=['payments'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert 'Paypal Help Center' in doc('div.inner-wrap').text()

    def test_account_category(self):
        """Verify the account category page."""
        response = get(self.client,
                       'questions.marketplace_aaq_category',
                       args=['account'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(4, len(doc('#question-form li')))

    def test_account_category_anon(self):
        """Verify the account category page with unauth'd user."""
        self.client.logout()
        response = get(self.client,
                       'questions.marketplace_aaq_category',
                       args=['account'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        # One extra form field (email) in this case.
        eq_(5, len(doc('#question-form li')))

    @mock.patch.object(questions.views, 'submit_ticket')
    def test_submit_ticket(self, submit_ticket):
        """Verify form post."""
        subject = 'A new ticket'
        body = 'Lorem ipsum dolor sit amet'
        cat = 'account'

        response = post(self.client,
                        'questions.marketplace_aaq_category',
                        {'subject': subject, 'body': body, 'category': cat},
                        args=['account'])
        eq_(200, response.status_code)
        submit_ticket.assert_called_with(self.user.email, cat, subject, body)

    @mock.patch.object(questions.views, 'submit_ticket')
    def test_submit_ticket_anon(self, submit_ticket):
        """Verify form post from unauth'd user."""
        email = 'foo@bar.com'
        subject = 'A new ticket'
        body = 'Lorem ipsum dolor sit amet'
        cat = 'account'

        self.client.logout()
        response = post(self.client,
                        'questions.marketplace_aaq_category',
                        {'subject': subject, 'body': body, 'category': cat,
                         'email': email},
                        args=['account'])
        eq_(200, response.status_code)
        submit_ticket.assert_called_with(email, cat, subject, body)


class FauxZendesk(Zendesk):
    def __init__(self, *args, **kwargs):
        super(FauxZendesk, self).__init__(*args, **kwargs)
        self.client = mock.Mock()
        self.client.request.return_value = '', ''

    @staticmethod
    def _response_handler(response, content, status):
        return 'https://appsmarket.zendesk.com/ticket/1'


class SubmitTicketTests(TestCase):
    @mock.patch.object(questions.marketplace, 'get_zendesk')
    def test_submit_ticket(self, get_zendesk):
        """Verify the http calls that are triggered by submit_ticket"""
        zd = FauxZendesk('https://appsmarket.zendesk.com', 'x@y.z', 'pwd')
        get_zendesk.return_value = zd

        submit_ticket('a@b.c', 'cat', 'subject', 'description')
        zd.client.request.assert_called_with(
            'https://appsmarket.zendesk.com/tickets.json?',
            'POST',
            body='{"ticket": {"requester_email": "a@b.c", "set_tags": "cat", '
                 '"description": "description", '
                 '"subject": "[TEST] subject"}}',
            headers={
                'Content-Type': 'application/json',
                'User-agent': 'Zendesk Python Library v1.1.0'})
