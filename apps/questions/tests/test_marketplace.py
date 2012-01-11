import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

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
