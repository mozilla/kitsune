from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from pyquery import PyQuery as pq

from kitsune.customercare.models import SupportTicket
from kitsune.products.models import ProductSupportConfig, SupportContract
from kitsune.products.routing import ENTERPRISE_SUPPORT, PRODUCT_SUPPORT
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportCoverageFactory,
    TopicFactory,
    ZendeskConfigFactory,
    ZendeskTopicConfigurationFactory,
)
from kitsune.questions.models import Question, QuestionLocale
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory


class EnterpriseTicketTests(TestCase):
    def setUp(self):
        self.product = ProductFactory(slug="firefox")
        self.product_config = ZendeskConfigFactory(ticket_form_id="42")
        self.support_config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=self.product_config
        )
        self.product_topic = ZendeskTopicConfigurationFactory(
            zendesk_config=self.product_config,
            zendesk_topic__slug="product-topic",
            zendesk_topic__form_title="Product support topic",
        )
        self.coverage = SupportCoverageFactory(
            product=self.product,
            zendesk_config__ticket_form_id="84",
            zendesk_config__enable_urgency_field=True,
            zendesk_product_value="enterprise-firefox",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.coverage.zendesk_config,
            zendesk_topic__slug="enterprise-topic",
            zendesk_topic__form_title="Enterprise support topic",
        )
        self.company = self.coverage.contract.company
        self.user = UserFactory()
        self.user.groups.add(self.company.group)
        self.client.force_login(self.user)
        self.url = reverse("questions.aaq_step3", args=[self.product.slug])
        self.data = {
            "support_action": ENTERPRISE_SUPPORT,
            "coverage": str(self.coverage.pk),
            "email": self.user.email,
            "category": "enterprise-topic",
            "subject": "Managed browser issue",
            "description": "Our managed browsers cannot load the company website.",
            "urgency": "high",
        }
        self.product_data = {
            **self.data,
            "support_action": PRODUCT_SUPPORT,
            "category": "product-topic",
        }
        classifier = patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
        self.classifier = classifier.start()
        self.addCleanup(classifier.stop)

    def use_forum_support(self, *, hybrid=False):
        locale, _ = QuestionLocale.objects.get_or_create(locale="en-US")
        self.support_config.forum_config = AAQConfigFactory(enabled_locales=[locale])
        self.support_config.zendesk_config = self.product_config if hybrid else None
        self.support_config.save()

    def assert_fresh_form_requested(self, response, url=None):
        url = url or self.url
        self.assertRedirects(response, url, fetch_redirect_response=False)
        self.assertFalse(SupportTicket.objects.exists())
        self.assertFalse(Question.objects.exists())
        fresh = self.client.get(url)
        self.assertContains(fresh, "This form changed. Review it and submit again.")
        return fresh

    def test_anonymous_user_must_log_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response, f"{reverse('users.login')}?next={self.url}", fetch_redirect_response=False
        )

    def test_covered_member_get_uses_coverage_config_and_enterprise_notice(self):
        response = self.client.get(self.url, HTTP_X_CLIENT_GEO_COUNTRY_NAME="Germany")
        self.assertContains(response, "Enterprise support topic")
        self.assertNotContains(response, "Product support topic")
        self.assertContains(response, "not publicly visible")
        self.assertContains(response, 'value="Germany"')
        doc = pq(response.content)
        self.assertEqual(doc("h2.sumo-page-heading").text(), "Contact Support")
        self.assertEqual(len(doc('select[name="urgency"][required]')), 1)
        self.assertEqual(len(doc(".switcher-actions")), 0)
        self.assertEqual(
            doc('#question-form input[type="hidden"][name="support_action"]').val(),
            ENTERPRISE_SUPPORT,
        )
        self.assertEqual(
            doc('#question-form input[type="hidden"][name="coverage"]').val(),
            str(self.coverage.pk),
        )

    def test_submission_keeps_accepted_coverage_and_company(self):
        response = self.client.post(self.url, self.data)
        self.assertRedirects(
            response,
            reverse("products.product", args=[self.product.slug]) + "#user-messages",
            fetch_redirect_response=False,
        )
        ticket = SupportTicket.objects.get()
        self.assertEqual(ticket.origin, SupportTicket.Origin.ENTERPRISE)
        self.assertEqual(ticket.coverage, self.coverage)
        self.assertEqual(ticket.org_group, self.company)
        self.assertEqual(ticket.accepted_context["form_id"], "84")
        self.assertEqual(ticket.accepted_context["product_value"], "enterprise-firefox")
        self.assertEqual(ticket.accepted_context["coverage_id"], self.coverage.pk)
        self.assertEqual(ticket.accepted_context["company"]["name"], self.company.group.name)
        self.assertTrue(ticket.accepted_context["skip_spam"])
        self.classifier.assert_called_once_with(ticket.pk)

    def test_invalid_zendesk_ids_do_not_reject_submission(self):
        config = self.coverage.zendesk_config
        config.ticket_form_id = ""
        config.brand_id = "invalid"
        config.save()

        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 302)
        ticket = SupportTicket.objects.get()
        self.assertEqual(ticket.accepted_context["form_id"], "")
        self.assertEqual(ticket.accepted_context["brand_id"], "invalid")

    def test_uncovered_user_gets_product_form_but_cannot_submit_enterprise_action(self):
        self.user.groups.clear()
        response = self.client.get(self.url)
        self.assertContains(response, "Product support topic")
        self.assertNotContains(response, "Enterprise support topic")
        self.assertEqual(
            pq(response.content)('#question-form input[name="support_action"]').val(),
            PRODUCT_SUPPORT,
        )

        response = self.client.post(self.url, self.data)
        self.assertContains(response, "cover this product right now.", status_code=403)
        self.assertContains(
            response, reverse("products.product", args=[self.product.slug]), status_code=403
        )
        self.assertFalse(SupportTicket.objects.exists())
        self.assertFalse(Question.objects.exists())

    def test_coverage_expiring_or_cancelled_after_get_denies_submission(self):
        contract = self.coverage.contract
        for field, value in (
            ("ends_on", timezone.localdate() - timedelta(days=1)),
            ("status", SupportContract.Status.CANCELLED),
        ):
            with self.subTest(field=field):
                contract.ends_on = timezone.localdate() + timedelta(days=2)
                contract.status = SupportContract.Status.ACTIVE
                contract.save()
                self.assertEqual(self.client.get(self.url).status_code, 200)
                setattr(contract, field, value)
                contract.save()
                response = self.client.post(self.url, self.data)
                self.assertEqual(response.status_code, 403)
                self.assertFalse(SupportTicket.objects.exists())
                self.assertFalse(Question.objects.exists())

    def test_changed_or_missing_coverage_reference_requests_fresh_get(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.coverage.delete()
        replacement = SupportCoverageFactory(
            product=self.product,
            contract=self.coverage.contract,
            zendesk_config=self.coverage.zendesk_config,
        )
        other_coverage = SupportCoverageFactory(product=self.product)
        for data in (
            self.data,
            {k: v for k, v in self.data.items() if k != "coverage"},
            {**self.data, "coverage": str(other_coverage.pk)},
        ):
            with self.subTest(coverage=data.get("coverage")):
                fresh = self.assert_fresh_form_requested(self.client.post(self.url, data))
                self.assertEqual(
                    pq(fresh.content)('#question-form input[name="coverage"]').val(),
                    str(replacement.pk),
                )

    def test_non_english_locale_redirects_to_english_form(self):
        response = self.client.get(
            reverse("questions.aaq_step3", args=[self.product.slug], locale="fr"),
            {"support_type": "zendesk"},
        )
        self.assertRedirects(
            response,
            self.url + "?support_type=zendesk&from_locale=fr",
            fetch_redirect_response=False,
        )

    def test_coverage_for_other_product_keeps_subscriber_ticket_ordinary(self):
        self.coverage.product = ProductFactory(slug="thunderbird")
        self.coverage.save()
        self.product.slug = "mozilla-vpn"
        self.product.save()
        self.support_config.subscription_only = True
        self.support_config.save()
        self.user.profile.products.add(self.product)
        url = reverse("questions.aaq_step3", args=[self.product.slug])

        response = self.client.get(url)
        self.assertContains(response, "Product support topic")
        self.assertNotContains(response, "Enterprise support topic")
        response = self.client.post(url, self.product_data)
        self.assertEqual(response.status_code, 302)
        ticket = SupportTicket.objects.get()
        self.assertEqual(ticket.origin, SupportTicket.Origin.PRODUCT)
        self.assertIsNone(ticket.coverage)
        self.assertIsNone(ticket.org_group)
        self.assertEqual(ticket.accepted_context["form_id"], "42")
        self.assertEqual(ticket.accepted_context["product_value"], "firefox-private-network-vpn")
        self.assertFalse(ticket.accepted_context["skip_spam"])
        self.assertEqual(ticket.urgency, "")

    def test_covered_subscriber_cannot_bypass_enterprise_with_product_action(self):
        self.support_config.subscription_only = True
        self.support_config.save()
        self.user.profile.products.add(self.product)
        response = self.client.get(self.url, {"support_type": "zendesk"})
        self.assertContains(response, "Enterprise support topic")

        self.assert_fresh_form_requested(self.client.post(self.url, self.product_data))

    def test_coverage_activated_after_product_get_requires_fresh_enterprise_form(self):
        contract = self.coverage.contract
        contract.status = SupportContract.Status.SUSPENDED
        contract.save()
        response = self.client.get(self.url)
        self.assertContains(response, "Product support topic")
        self.assertEqual(
            pq(response.content)('#question-form input[name="support_action"]').val(),
            PRODUCT_SUPPORT,
        )
        contract.status = SupportContract.Status.ACTIVE
        contract.save()

        fresh = self.assert_fresh_form_requested(self.client.post(self.url, self.product_data))
        self.assertContains(fresh, "Enterprise support topic")

    def test_missing_or_invalid_action_requests_fresh_get(self):
        url = self.url + "?support_type=zendesk"
        for action in (None, "", "zendesk", "invalid"):
            with self.subTest(action=action):
                data = self.data.copy()
                if action is None:
                    del data["support_action"]
                else:
                    data["support_action"] = action
                self.assert_fresh_form_requested(self.client.post(url, data), url)

    def test_forum_action_no_longer_allowed_requests_fresh_get(self):
        self.use_forum_support()
        self.assertContains(
            self.client.get(self.url, {"support_type": "forum"}), "Ask your question"
        )
        self.support_config.forum_config = None
        self.support_config.zendesk_config = self.product_config
        self.support_config.save()

        response = self.client.post(
            self.url,
            {
                "support_action": ProductSupportConfig.SUPPORT_TYPE_FORUM,
                "title": "A private support request",
                "content": "This must not become a ticket or public question.",
            },
        )
        self.assert_fresh_form_requested(response)

    def test_covered_forum_product_defaults_to_enterprise_with_forum_alternative(self):
        self.use_forum_support()
        response = self.client.get(self.url)
        self.assertContains(response, "Enterprise support topic")
        doc = pq(response.content)
        self.assertEqual(
            doc('#question-form input[type="hidden"][name="support_action"]').val(),
            ENTERPRISE_SUPPORT,
        )
        self.assertEqual(doc('input[name="coverage"]').val(), str(self.coverage.pk))
        self.assertTrue(doc('.switcher-actions a[href$="?support_type=forum"]'))

        response = self.client.get(self.url, {"support_type": "forum"})
        self.assertContains(response, "Ask your question")
        self.assertEqual(
            pq(response.content)('#question-form input[name="support_action"]').val(),
            ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )
        self.assertFalse(pq(response.content)('input[name="coverage"]'))

    def test_uncovered_forum_user_has_no_ticket_switcher(self):
        self.use_forum_support()
        self.user.groups.clear()
        for has_offering in (True, False):
            with self.subTest(has_offering=has_offering):
                if not has_offering:
                    self.coverage.delete()
                response = self.client.get(self.url, {"support_type": "zendesk"})
                self.assertContains(response, "Ask your question")
                self.assertFalse(pq(response.content)(".switcher-actions"))
                self.assertFalse(pq(response.content)('input[name="coverage"]'))

    def test_forum_submission_keeps_its_channel_when_enterprise_is_the_default(self):
        self.use_forum_support(hybrid=True)
        topic = TopicFactory(products=[self.product], in_aaq=True)
        response = self.client.post(
            self.url,
            {
                "support_action": ProductSupportConfig.SUPPORT_TYPE_FORUM,
                "title": "A question for the community",
                "content": "How do I customize the browser toolbar?",
                "category": topic.pk,
            },
        )
        question = Question.objects.get()
        self.assertRedirects(
            response,
            reverse("questions.details", args=[question.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(question.product, self.product)
        self.assertEqual(question.creator, self.user)
        self.assertFalse(SupportTicket.objects.exists())
        self.assertEqual(
            self.client.session["aaq_context"]["current_support_type"],
            ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )

    def test_loginless_product_submission_requires_a_supported_referer(self):
        self.product.slug = "mozilla-account"
        self.product.save()
        self.product_topic.loginless_only = True
        self.product_topic.save()
        self.client.logout()
        url = reverse("questions.aaq_step3", args=[self.product.slug])

        response = self.client.post(url, self.product_data)
        self.assertRedirects(
            response, f"{reverse('users.login')}?next={url}", fetch_redirect_response=False
        )
        self.assertFalse(SupportTicket.objects.exists())

        response = self.client.post(url, self.product_data, HTTP_REFERER=reverse("users.auth"))
        self.assertEqual(response.status_code, 302)
        ticket = SupportTicket.objects.get()
        self.assertEqual(ticket.origin, SupportTicket.Origin.PRODUCT)
        self.assertIsNone(ticket.user)
        self.assertIsNone(ticket.org_group)
        self.assertFalse(Question.objects.exists())

    def test_coverage_without_product_support_config_shows_enterprise_form(self):
        self.support_config.delete()
        response = self.client.get(self.url)
        self.assertContains(response, "Enterprise support topic")
        self.assertEqual(
            pq(response.content)('#question-form input[name="coverage"]').val(),
            str(self.coverage.pk),
        )
        cancel_url = pq(response.content)("#question-form .aaq-form-buttons a").attr("href")
        step2_url = reverse("questions.aaq_step2", args=[self.product.slug])
        self.assertEqual(cancel_url, step2_url)
        step2 = self.client.get(cancel_url)
        self.assertEqual(step2.status_code, 200)
        self.assertEqual(pq(step2.content)(".aaq-widget a").attr("href"), self.url)

    def test_step1_and_question_list_offer_products_with_a_support_action(self):
        self.support_config.delete()
        configured = ProductSupportConfigFactory(zendesk_config=self.product_config).product
        step1_url = reverse("questions.aaq_step1")
        step2_url = reverse("questions.aaq_step2", args=[self.product.slug])
        question_list_url = reverse("questions.list", args=[self.product.slug])
        community_cta = (step1_url, "Ask the Community")

        def question_list_cta():
            response = self.client.get(question_list_url, follow=True)
            cta = pq(response.content)(".forum--masthead-cta a")
            return cta.attr("href"), cta.text()

        for persona, user, offered in (
            ("covered member", self.user, True),
            ("uncovered user", UserFactory(), False),
            ("anonymous", None, False),
        ):
            with self.subTest(persona=persona):
                if user:
                    self.client.force_login(user)
                else:
                    self.client.logout()
                picker = pq(self.client.get(step1_url).content)("#product-picker .card--title a")
                hrefs = [a.attr("href") for a in picker.items()]
                self.assertEqual(step2_url in hrefs, offered)
                self.assertIn(reverse("questions.aaq_step2", args=[configured.slug]), hrefs)
                self.assertEqual(
                    question_list_cta(),
                    (step2_url, "Contact Support") if offered else community_cta,
                )

        ProductSupportConfigFactory(
            product=self.product, zendesk_config=self.product_config, subscription_only=True
        )
        self.client.force_login(UserFactory())
        self.assertEqual(question_list_cta(), community_cta)

    def test_covered_non_subscriber_gets_enterprise_instead_of_redirect_or_hide(self):
        self.support_config.subscription_only = True
        for redirect_product in (None, ProductFactory()):
            with self.subTest(redirect_product=redirect_product):
                self.support_config.unsubscribed_redirect_product = redirect_product
                self.support_config.save()
                response = self.client.get(self.url)
                self.assertContains(response, "Enterprise support topic")
                self.assertNotContains(response, "Product support topic")
                self.assertEqual(len(pq(response.content)(".switcher-actions")), 0)
                step2 = self.client.get(reverse("questions.aaq_step2", args=[self.product.slug]))
                self.assertEqual(step2.status_code, 200)
                self.assertEqual(pq(step2.content)(".aaq-widget a").attr("href"), self.url)

    def test_uncovered_non_subscriber_keeps_redirect_or_hide(self):
        self.user.groups.clear()
        self.support_config.subscription_only = True
        self.support_config.save()
        self.assertEqual(self.client.get(self.url).status_code, 404)

        redirect_product = ProductFactory()
        self.support_config.unsubscribed_redirect_product = redirect_product
        self.support_config.save()
        self.assertRedirects(
            self.client.get(self.url),
            reverse("questions.aaq_step2", args=[redirect_product.slug]),
            fetch_redirect_response=False,
        )

    @patch("kitsune.questions.views.is_ratelimited")
    def test_each_origin_has_its_own_daily_limit(self, ratelimited):
        def submit(origin):
            if origin == SupportTicket.Origin.ENTERPRISE:
                self.user.groups.add(self.company.group)
                return self.client.post(self.url, self.data)
            self.user.groups.clear()
            return self.client.post(self.url, self.product_data)

        enterprise, product = SupportTicket.Origin.ENTERPRISE, SupportTicket.Origin.PRODUCT
        for limited, allowed, limit in (
            (enterprise, product, ("enterprise-ticket", "20/d")),
            (product, enterprise, ("loginless", "3/d")),
        ):
            with self.subTest(limited=limited):
                SupportTicket.objects.all().delete()

                def check_limit(request, group, rate, limit=limit):
                    request.limited = (group, rate) == limit
                    return request.limited

                ratelimited.side_effect = check_limit
                response = submit(limited)
                self.assertContains(response, "exceeded the number of submissions for today.")
                self.assertFalse(SupportTicket.objects.exists())

                self.assertEqual(submit(allowed).status_code, 302)
                self.assertEqual(SupportTicket.objects.get().origin, allowed)
