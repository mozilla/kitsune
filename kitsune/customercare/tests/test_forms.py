from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.utils import translation

from kitsune.customercare.forms import ZendeskForm
from kitsune.customercare.models import SupportTicket
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    TopicFactory,
    ZendeskConfigFactory,
    ZendeskTopicConfigurationFactory,
    ZendeskTopicFactory,
)
from kitsune.sumo.tests import TestCase, translated_db_strings
from kitsune.users.tests import UserFactory


class ZendeskFormTests(TestCase):
    """Tests for ZendeskForm with new product-specific categories."""

    def setUp(self):
        """Set up test data."""
        self.vpn_product = ProductFactory(title="Mozilla VPN", slug="mozilla-vpn", codename="vpn")
        self.relay_product = ProductFactory(title="Firefox Relay", slug="relay", codename="relay")
        self.accounts_product = ProductFactory(
            title="Mozilla Accounts", slug="mozilla-account", codename="accounts"
        )
        self.user = UserFactory(email="test@example.com")

        # Create ZendeskConfig for VPN
        self.vpn_zendesk = ZendeskConfigFactory(name="Mozilla VPN Support")
        vpn_topic1 = ZendeskTopicFactory(
            slug="vpn-connection-issues",
            form_title="I can't connect to Mozilla VPN",
            legacy_tag="technical",
            tier_tags=[
                "t1-performance-and-connectivity",
                "t2-connectivity",
                "t3-connection-failure",
            ],
            automation_tags=["ssa-connection-issues-automation"],
            segmentation_tag="",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.vpn_zendesk,
            zendesk_topic=vpn_topic1,
            display_order=0,
            loginless_only=False,
        )
        vpn_topic2 = ZendeskTopicFactory(
            slug="vpn-server-selection",
            form_title="I can't choose a VPN location",
            legacy_tag="technical",
            tier_tags=[
                "t1-performance-and-connectivity",
                "t2-connectivity",
                "t3-cant-select-server",
            ],
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.vpn_zendesk,
            zendesk_topic=vpn_topic2,
            display_order=1,
            loginless_only=False,
        )
        vpn_topic3 = ZendeskTopicFactory(
            slug="payments",
            form_title="I need help with a billing or subscription question",
            legacy_tag="payments",
            tier_tags=["t1-billing-and-subscriptions"],
            segmentation_tag="",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.vpn_zendesk,
            zendesk_topic=vpn_topic3,
            display_order=2,
            loginless_only=False,
        )
        ProductSupportConfigFactory(
            product=self.vpn_product, zendesk_config=self.vpn_zendesk, forum_config=None
        )

        # Create ZendeskConfig for Relay
        self.relay_zendesk = ZendeskConfigFactory(name="Firefox Relay Support")
        relay_topic1 = ZendeskTopicFactory(
            slug="relay-email-forwarding",
            form_title="I'm not receiving emails to my Relay mask",
            legacy_tag="technical",
            tier_tags=["t1-privacy-and-security", "t2-masking", "t3-email-masking"],
            segmentation_tag="seg-relay-no-fwd-deliver",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.relay_zendesk,
            zendesk_topic=relay_topic1,
            display_order=0,
            loginless_only=False,
        )
        relay_topic2 = ZendeskTopicFactory(
            slug="relay-domain-change",
            form_title="I want to change my Relay email domain",
            legacy_tag="technical",
            tier_tags=["t1-privacy-and-security", "t2-masking", "t3-email-masking"],
            segmentation_tag="seg-relay-chg-domain",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.relay_zendesk,
            zendesk_topic=relay_topic2,
            display_order=1,
            loginless_only=False,
        )
        ProductSupportConfigFactory(
            product=self.relay_product, zendesk_config=self.relay_zendesk, forum_config=None
        )

        # Create ZendeskConfig for Mozilla Account with loginless topics
        self.accounts_zendesk = ZendeskConfigFactory(name="Mozilla Account Support")
        accounts_topic1 = ZendeskTopicFactory(
            slug="fxa-2fa-lockout",
            form_title="My security code isn't working or is lost",
            legacy_tag="accounts",
            tier_tags=[
                "t1-passwords-and-sign-in",
                "t2-two-factor-authentication",
                "t3-two-factor-lockout",
            ],
            automation_tags=["ssa-2fa-automation"],
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.accounts_zendesk,
            zendesk_topic=accounts_topic1,
            display_order=0,
            loginless_only=True,
        )
        accounts_topic2 = ZendeskTopicFactory(
            slug="fxa-reset-password",
            form_title="I forgot my password",
            legacy_tag="accounts",
            tier_tags=["t1-passwords-and-sign-in", "t2-reset-passwords"],
            automation_tags=["ssa-emailverify-automation"],
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.accounts_zendesk,
            zendesk_topic=accounts_topic2,
            display_order=1,
            loginless_only=True,
        )
        ProductSupportConfigFactory(
            product=self.accounts_product, zendesk_config=self.accounts_zendesk, forum_config=None
        )

    def test_authenticated_form_gets_correct_categories(self):
        """Test that authenticated users get product-specific categories."""
        form = ZendeskForm(
            product=self.vpn_product, zendesk_config=self.vpn_zendesk, user=self.user
        )

        category_topics = [choice[1] for choice in form.fields["category"].choices if choice[0]]
        self.assertIn("I can't connect to Mozilla VPN", category_topics)
        self.assertIn("I can't choose a VPN location", category_topics)
        self.assertEqual(len(category_topics), 3)  # 3 topics for VPN

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
    def test_loginless_form_gets_loginless_categories(self):
        """Test that loginless users get FxA-specific categories."""
        anonymous_user = AnonymousUser()
        form = ZendeskForm(
            product=self.accounts_product,
            zendesk_config=self.accounts_zendesk,
            user=anonymous_user,
        )

        category_topics = [choice[1] for choice in form.fields["category"].choices if choice[0]]
        self.assertIn("I forgot my password", category_topics)
        self.assertIn("My security code isn't working or is lost", category_topics)
        self.assertEqual(len(category_topics), 2)  # 2 loginless topics for Mozilla Account

    def test_topic_titles_are_localized(self):
        title = ("DB: products.ZendeskTopic.form_title", "I can't connect to Mozilla VPN")
        german = "Ich kann keine Verbindung zu Mozilla VPN herstellen"
        with translated_db_strings("de", {title: german}), translation.override("de"):
            form = ZendeskForm(
                product=self.vpn_product, zendesk_config=self.vpn_zendesk, user=self.user
            )
        self.assertIn(("vpn-connection-issues", german), form.fields["category"].choices)

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_send_creates_pending_ticket_with_tags(self, mock_task):
        root_topic = TopicFactory(
            title="Billing and subscriptions",
            slug="billing-and-subscriptions",
            parent=None,
            legacy_tag="payments",
        )
        linked_topic = ZendeskTopicFactory(
            slug="linked-billing",
            form_title="I need help with a billing or subscription question",
            topic=root_topic,
            # Stored fallbacks differ to prove the linked Topic wins.
            legacy_tag="stale-legacy",
            tier_tags=["stale-tier"],
            automation_tags=["ssa-billing-automation"],
            segmentation_tag="",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.vpn_zendesk,
            zendesk_topic=linked_topic,
            display_order=3,
            loginless_only=False,
        )
        targets = {
            "vpn": (self.vpn_product, self.vpn_zendesk, self.user, self.user),
            "relay": (self.relay_product, self.relay_zendesk, self.user, self.user),
            "loginless": (self.accounts_product, self.accounts_zendesk, AnonymousUser(), None),
        }
        flags = ("enable_os_field", "enable_deployment_fields", "enable_urgency_field")
        for target, enabled_flags, data, tags in (
            (
                "vpn",
                (),
                {"category": "vpn-connection-issues", "country": "US"},
                [
                    "technical",
                    "t1-performance-and-connectivity",
                    "t2-connectivity",
                    "t3-connection-failure",
                    "ssa-connection-issues-automation",
                ],
            ),
            (
                "relay",
                (),
                {"category": "relay-email-forwarding"},
                [
                    "technical",
                    "t1-privacy-and-security",
                    "t2-masking",
                    "t3-email-masking",
                    "seg-relay-no-fwd-deliver",
                ],
            ),
            ("vpn", (), {"category": "payments"}, ["payments", "t1-billing-and-subscriptions"]),
            (
                "vpn",
                (),
                {"category": "linked-billing"},
                ["payments", "t1-billing-and-subscriptions", "ssa-billing-automation"],
            ),
            (
                "loginless",
                (),
                {"category": "fxa-2fa-lockout"},
                [
                    "accounts",
                    "t1-passwords-and-sign-in",
                    "t2-two-factor-authentication",
                    "t3-two-factor-lockout",
                    "ssa-2fa-automation",
                ],
            ),
            (
                "vpn",
                flags,
                {
                    "category": "payments",
                    "os": "mac",
                    "update_channel": "esr",
                    "policy_distribution": "group_policy_admx",
                    "urgency": "critical",
                },
                [
                    "payments",
                    "t1-billing-and-subscriptions",
                    "seg-platform-mac",
                    "seg-rel-esr",
                    "seg-policy-windows-gpo",
                    "seg-sev1",
                ],
            ),
        ):
            with self.subTest(target=target, **data):
                product, zendesk_config, user, owner = targets[target]
                for flag in flags:
                    setattr(zendesk_config, flag, flag in enabled_flags)
                mock_task.reset_mock()
                submitted = {
                    "email": "test@example.com",
                    "subject": "Test subject",
                    "description": "Test description",
                    **data,
                }
                form = ZendeskForm(
                    data=submitted,
                    product=product,
                    zendesk_config=zendesk_config,
                    user=user,
                )
                self.assertTrue(form.is_valid(), form.errors)

                ticket = form.send(user)

                self.assertIsInstance(ticket, SupportTicket)
                self.assertEqual(ticket.zendesk_tags, tags)
                self.assertEqual(ticket.submission_status, SupportTicket.STATUS_PENDING)
                expected = {
                    "country": "",
                    "os": "",
                    "update_channel": "",
                    "policy_distribution": "",
                    "urgency": "",
                    **submitted,
                }
                self.assertEqual({field: getattr(ticket, field) for field in expected}, expected)
                self.assertEqual(ticket.product, product)
                self.assertEqual(ticket.user, owner)
                mock_task.assert_called_once_with(ticket.id)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_send_maps_field_values_to_segmentation_tags(self, mock_task):
        self.vpn_zendesk.enable_os_field = True
        self.vpn_zendesk.enable_deployment_fields = True
        self.vpn_zendesk.enable_urgency_field = True
        required = {
            "update_channel": "esr",
            "policy_distribution": "policies_json",
            "urgency": "normal",
        }
        for field, value, tag in (
            ("os", "win64", "seg-platform-win64"),
            ("os", "win_arm64", "seg-platform-win-arm64"),
            ("os", "win32", "seg-platform-win32"),
            ("os", "mac", "seg-platform-mac"),
            ("os", "linux64", "seg-platform-linux64"),
            ("os", "linux_arm64", "seg-platform-linux-arm64"),
            ("os", "linux32", "seg-platform-linux32"),
            ("os", "android", "seg-platform-android"),
            ("os", "ios", "seg-platform-ios"),
            ("update_channel", "esr", "seg-rel-esr"),
            ("update_channel", "rapid_release", "seg-rel-rapid-release"),
            ("update_channel", "full_release", "seg-rel-full-release"),
            ("update_channel", "beta", "seg-rel-beta"),
            ("update_channel", "other", "seg-rel-channel-other"),
            ("policy_distribution", "firefox_admin_console", "seg-firefox-admin-console"),
            ("policy_distribution", "group_policy_admx", "seg-policy-windows-gpo"),
            ("policy_distribution", "windows_mdm", "seg-policy-windows-mdm"),
            ("policy_distribution", "macos_config_profiles", "seg-policy-macos-config-profiles"),
            ("policy_distribution", "policies_json", "seg-policy-json"),
            ("policy_distribution", "autoconfig", "seg-policy-autoconfig"),
            ("policy_distribution", "not_sure", "seg-policy-dist-other"),
            ("urgency", "normal", "seg-sev3"),
            ("urgency", "high", "seg-sev2"),
            ("urgency", "critical", "seg-sev1"),
        ):
            with self.subTest(field=field, value=value):
                form = ZendeskForm(
                    data={
                        "email": "test@example.com",
                        "category": "payments",
                        "subject": "Test subject",
                        "description": "Test description",
                        **required,
                        field: value,
                    },
                    product=self.vpn_product,
                    zendesk_config=self.vpn_zendesk,
                    user=self.user,
                )
                self.assertTrue(form.is_valid(), form.errors)
                self.assertIn(tag, form.send(self.user).zendesk_tags)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_send_with_no_category_selected(self, mock_task):
        """Test that no tags are collected when no category is selected."""
        form = ZendeskForm(
            data={
                "email": "test@example.com",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.vpn_product,
            zendesk_config=self.vpn_zendesk,
            user=self.user,
        )

        if not form.is_valid():
            form.cleaned_data = {
                "email": "test@example.com",
                "subject": "Test subject",
                "description": "Test description",
                "category": "",  # Empty category
            }
        submission = form.send(self.user)

        self.assertIsInstance(submission, SupportTicket)
        self.assertEqual(submission.zendesk_tags, [])
        self.assertEqual(submission.submission_status, SupportTicket.STATUS_PENDING)
        self.assertEqual(submission.category, "")
        mock_task.assert_called_once_with(submission.id)

    def test_config_controls_topics_without_product_support_config(self):
        form = ZendeskForm(
            product=ProductFactory(), zendesk_config=self.vpn_zendesk, user=self.user
        )
        self.assertIn("payments", dict(form.fields["category"].choices))

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
    def test_email_validation(self):
        for email, valid in (
            ("frvv4@gmail.com8050262430", False),  # issue 2669
            ("test@@example.com", False),
            ("test @example.com", False),
            ("mozilla.test334@example.com", True),  # issue 2830
            ("valid.email+tag@example.com", True),
        ):
            with self.subTest(email=email):
                form = ZendeskForm(
                    data={
                        "email": email,
                        "category": "fxa-2fa-lockout",
                        "subject": "Test subject",
                        "description": "Test description",
                    },
                    product=self.accounts_product,
                    zendesk_config=self.accounts_zendesk,
                    user=AnonymousUser(),
                )

                self.assertEqual(form.is_valid(), valid)
                if not valid:
                    self.assertEqual(set(form.errors), {"email"})
                    self.assertIn("valid email address", str(form.errors["email"]))

    def test_config_flags_show_their_fields(self):
        for field, flag in (
            ("os", "enable_os_field"),
            ("update_channel", "enable_deployment_fields"),
            ("policy_distribution", "enable_deployment_fields"),
            ("urgency", "enable_urgency_field"),
        ):
            for enabled in (False, True):
                with self.subTest(field=field, enabled=enabled):
                    setattr(self.vpn_zendesk, flag, enabled)
                    form = ZendeskForm(
                        product=self.vpn_product, zendesk_config=self.vpn_zendesk, user=self.user
                    )

                    widget = form.fields[field].widget
                    if enabled:
                        self.assertEqual(widget.__class__.__name__, "Select")
                        self.assertEqual(widget.choices, form.fields[field].choices)
                    else:
                        self.assertEqual(widget.__class__.__name__, "HiddenInput")

        urgency_values = [value for value, _ in form.fields["urgency"].choices if value]
        self.assertEqual(urgency_values, ["critical", "high", "normal"])

    def test_config_controls_required_fields_and_rejects_other_configs_topics(self):
        self.relay_zendesk.enable_os_field = True
        self.relay_zendesk.enable_urgency_field = True
        self.relay_zendesk.enable_deployment_fields = True
        data = {
            "email": self.user.email,
            "category": "vpn-connection-issues",
            "subject": "Connection trouble",
            "description": "Cannot connect",
        }
        vpn_form = ZendeskForm(
            data, product=self.vpn_product, zendesk_config=self.vpn_zendesk, user=self.user
        )
        relay_form = ZendeskForm(
            data, product=self.vpn_product, zendesk_config=self.relay_zendesk, user=self.user
        )
        self.assertTrue(vpn_form.is_valid(), vpn_form.errors)
        self.assertFalse(relay_form.is_valid())
        self.assertEqual(
            set(relay_form.errors),
            {"category", "urgency", "update_channel", "policy_distribution"},
        )

        data.update(
            category="None",
            os="None",
            urgency="normal",
            update_channel="esr",
            policy_distribution="policies_json",
        )
        relay_form = ZendeskForm(
            data, product=self.vpn_product, zendesk_config=self.relay_zendesk, user=self.user
        )
        self.assertFalse(relay_form.is_valid())
        self.assertEqual(set(relay_form.errors), {"category", "os"})

        data.update(category="relay-email-forwarding", os="win64")
        relay_form = ZendeskForm(
            data, product=self.vpn_product, zendesk_config=self.relay_zendesk, user=self.user
        )
        self.assertTrue(relay_form.is_valid(), relay_form.errors)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_authenticated_submission_uses_account_email_and_validated_topics(self, mock_task):
        topic = TopicFactory(products=[self.vpn_product])
        selected = ZendeskTopicFactory(topic=topic, automation_tags=["accepted-automation"])
        mapping = ZendeskTopicConfigurationFactory(
            zendesk_config=self.vpn_zendesk, zendesk_topic=selected
        )
        form = ZendeskForm(
            {
                "email": "someone-else@example.com",
                "category": selected.slug,
                "subject": "Connection trouble",
                "description": "Cannot connect",
            },
            product=self.vpn_product,
            zendesk_config=self.vpn_zendesk,
            user=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        mapping.delete()
        selected.automation_tags = ["changed-automation"]
        selected.save()

        ticket = form.send(self.user)

        self.assertEqual(ticket.email, self.user.email)
        self.assertIn("accepted-automation", ticket.zendesk_tags)
        self.assertEqual(ticket.accepted_context["selected_topic_id"], topic.pk)
        self.assertEqual(
            ticket.accepted_context["automation_tags"][str(topic.pk)], ["accepted-automation"]
        )

    def test_text_fields_must_fit_the_saved_ticket(self):
        for field in ("subject", "country"):
            with self.subTest(field=field):
                form = ZendeskForm(
                    {
                        "category": "vpn-connection-issues",
                        "subject": "Connection trouble",
                        "description": "Cannot connect",
                        field: "x" * 256,
                    },
                    product=self.vpn_product,
                    zendesk_config=self.vpn_zendesk,
                    user=self.user,
                )
                self.assertFalse(form.is_valid())
                self.assertEqual(set(form.errors), {field})

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_disabled_fields_drop_submitted_values(self, mock_task):
        for value in ("invalid-choice", "critical"):
            with self.subTest(value=value):
                form = ZendeskForm(
                    {
                        "email": self.user.email,
                        "category": "vpn-connection-issues",
                        "subject": "Connection trouble",
                        "description": "Cannot connect",
                        "os": "win64",
                        "urgency": value,
                        "update_channel": "esr",
                        "policy_distribution": "policies_json",
                    },
                    product=self.vpn_product,
                    zendesk_config=self.vpn_zendesk,
                    user=self.user,
                )
                self.assertTrue(form.is_valid(), form.errors)
                ticket = form.send(self.user)
                for field in ("os", "urgency", "update_channel", "policy_distribution"):
                    self.assertEqual(getattr(ticket, field), "")
                self.assertFalse(any(tag.startswith("seg-") for tag in ticket.zendesk_tags))
