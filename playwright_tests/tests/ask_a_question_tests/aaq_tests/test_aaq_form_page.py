import pytest
import pytest_check as check

from playwright.sync_api import expect
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.aaq_form_page_messages import (
    AAQFormMessages)
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import \
    QuestionPageMessages
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import (
    ContactSupportMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)


class TestAAQPage(TestUtilities):

    # C2188694, C2188695
    @pytest.mark.aaqPage
    def test_community_card_and_helpful_tip_are_displayed_for_freemium_product(self):
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating to each freemium aaq form")
        for freemium_product in super().general_test_data["freemium_products"]:
            self.navigate_to_link(
                super().aaq_question_test_data["products_aaq_url"][freemium_product]
            )

            self.logger.info("Verifying that the helpful tip card is displayed")
            expect(
                self.sumo_pages.aaq_form_page._get_helpful_tip_locator()
            ).to_be_visible()

            self.logger.info("Clicking on the 'Learn More' button from the community help card")
            self.sumo_pages.aaq_form_page._click_on_learn_more_button()

            self.logger.info("Verifying that we are on the contribute_messages page")
            expect(
                self.page
            ).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)

    # C2188694, C2188695
    @pytest.mark.aaqPage
    def test_community_card_and_helpful_tip_not_displayed_for_premium_products(self):
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating to each premium aaq form")
        for premium_product in super().general_test_data["premium_products"]:
            self.navigate_to_link(
                super().aaq_question_test_data["products_aaq_url"][premium_product]
            )

            self.logger.info("Verifying that the helpful tip option is not displayed")
            expect(
                self.sumo_pages.aaq_form_page._get_helpful_tip_locator()
            ).to_be_hidden()

            self.logger.info("Verifying that the 'Learn More' button from the community help "
                             "banner is not displayed")
            expect(
                self.sumo_pages.aaq_form_page._get_learn_more_button_locator()
            ).to_be_hidden()

    # C1511570
    @pytest.mark.aaqPage
    @pytest.mark.parametrize("username", ['', 'TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR'])
    def test_scam_banner_premium_products_not_displayed(self, username):
        if username != '':
            self.logger.info("Signing in with a user account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts[username]
            ))
        self.logger.info("Navigating to each premium product solutions page")
        for premium_product in super().general_test_data["premium_products"]:
            self.navigate_to_link(
                super().general_test_data["product_solutions"][premium_product]
            )

            self.logger.info("Verifying that the scam banner is not displayed")
            expect(
                self.sumo_pages.product_solutions_page._get_scam_banner_locator()
            ).to_be_hidden()

            if username != '':
                self.logger.info("Clicking on the ask now button")
                self.sumo_pages.product_solutions_page._click_ask_now_button()
                self.wait_for_url_to_be(
                    super().aaq_question_test_data["products_aaq_url"][premium_product]
                )

                self.logger.info("Verifying that the scam banner is not displayed")
                expect(
                    self.sumo_pages.product_solutions_page._get_scam_banner_locator()
                ).to_be_hidden()

    # C2190040
    @pytest.mark.aaqPage
    @pytest.mark.parametrize("username", ['', 'TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR'])
    def test_scam_banner_for_freemium_products_is_displayed(self, username):
        if username != '':
            self.logger.info("Signing in with a user account")
            self.start_existing_session(super().username_extraction_from_email(
                self.user_secrets_accounts[username]
            ))

        self.logger.info("Navigating to each freemium product solutions page")
        for freemium_product in super().general_test_data["freemium_products"]:
            self.navigate_to_link(
                super().general_test_data["product_solutions"][freemium_product]
            )

            self.logger.info("Verifying that the 'Learn More' button contains the correct link")
            check.equal(
                self.sumo_pages.product_solutions_page._get_scam_alert_banner_link(),
                QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK
            )

            if username != '':
                self.logger.info("Clicking on the ask now button")
                self.sumo_pages.product_solutions_page._click_ask_now_button()
                self.wait_for_url_to_be(
                    super().aaq_question_test_data["products_aaq_url"][freemium_product]
                )

                self.logger.info(
                    "Verifying that the 'Learn More' button contains the correct link")
                check.equal(
                    self.sumo_pages.product_solutions_page._get_scam_alert_banner_link(),
                    QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK
                )

    # C890537
    @pytest.mark.aaqPage
    def test_corresponding_aaq_product_name_and_image_are_displayed(self):
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating to each product aaq form")
        for product in super().aaq_question_test_data["products_aaq_url"]:
            self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"][product])

            # This needs to change when we add the Mozilla Account icon/product.
            if product != "Mozilla Account":
                self.logger.info("Verifying that the product image is displayed")
                expect(
                    self.sumo_pages.aaq_form_page._get_product_image_locator()
                ).to_be_visible()
            else:
                self.logger.info("Verifying that the product image is hidden for Mozilla Account "
                                 "product")
                expect(
                    self.sumo_pages.aaq_form_page._get_product_image_locator()
                ).to_be_visible()

            self.logger.info("Verifying that the correct product header is displayed")
            check.equal(
                self.sumo_pages.aaq_form_page._get_aaq_form_page_heading(),
                product,
                f"Incorrect form header displayed. "
                f"Expected: {product} "
                f"Received: {self.sumo_pages.aaq_form_page._get_aaq_form_page_heading()}"
            )

    # C890535, C890536
    @pytest.mark.aaqPage
    def test_progress_milestone_redirect(self):
        self.logger.info("Signing in with a normal user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

        self.logger.info("Navigating to each product aaq form")
        for product in super().aaq_question_test_data["products_aaq_url"]:
            self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"][product])

            self.logger.info("Verifying that the correct in progress milestone is displayed")
            check.equal(
                self.sumo_pages.aaq_form_page._get_in_progress_item_label(),
                AAQFormMessages.IN_PROGRESS_MILESTONE,
                f"Incorrect current milestone. "
                f"Expected: {AAQFormMessages.IN_PROGRESS_MILESTONE} "
                f"Received: {self.sumo_pages.aaq_form_page._get_in_progress_item_label()}"
            )

            self.logger.info(
                f"Clicking on the {AAQFormMessages.COMPLETED_MILESTONE_TWO} milestone'"
            )
            self.sumo_pages.aaq_form_page._click_on_a_particular_completed_milestone(
                AAQFormMessages.COMPLETED_MILESTONE_TWO)

            self.logger.info("Verifying that the we are on the correct product solutions page")
            expect(
                self.page
            ).to_have_url(super().general_test_data["product_solutions"][product])

            self.logger.info(
                f"Navigating back to the aaq form and "
                f"clicking on the {AAQFormMessages.COMPLETED_MILESTONE_ONE} milestone")
            self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"][product])
            self.sumo_pages.aaq_form_page._click_on_a_particular_completed_milestone(
                AAQFormMessages.COMPLETED_MILESTONE_ONE)

            self.logger.info("Verifying that we are redirected to the correct page")
            expect(
                self.page
            ).to_have_url(ContactSupportMessages.PAGE_URL_CHANGE_PRODUCT_REDIRECT)

    # C890612
    @pytest.mark.aaqPage
    def test_aaq_form_cancel_button_freemium_products(self):
        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
        ))

        self.logger.info("Accessing the 'My profile' page via the top-navbar menu")
        self.sumo_pages.top_navbar._click_on_view_profile_option()

        self.logger.info("Extracting original number of posted questions")
        original_number_of_questions = self.number_extraction_from_string(
            self.sumo_pages.my_profile_page._get_my_profile_questions_text()
        )

        self.logger.info("Navigating to each product aaq form")
        for product in super().general_test_data["freemium_products"]:
            self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"][product])

            self.logger.info("Adding data inside AAQ form fields without submitting the form")
            self.sumo_pages.aaq_flow.add__valid_data_to_all_input_fields_without_submitting(
                subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_value=self.sumo_pages.aaq_form_page._get_aaq_form_topic_options()[0],
                body_text=super().aaq_question_test_data["valid_firefox_question"]["question_body"]
            )

            self.logger.info("Clicking on the Cancel button")
            self.sumo_pages.aaq_form_page._click_aaq_form_cancel_button()

            self.logger.info("Verifying that we are redirected back to the correct product "
                             "solutions page")
            expect(
                self.page
            ).to_have_url(super().general_test_data["product_solutions"][product])

            self.logger.info("Navigating back to the My Profile page")
            self.sumo_pages.top_navbar._click_on_view_profile_option()

            new_number = self.number_extraction_from_string(
                self.sumo_pages.my_profile_page._get_my_profile_questions_text()
            )

            self.logger.info("Verifying that the correct number of posted questions is displayed "
                             "at profile level")
            check.equal(
                new_number,
                original_number_of_questions,
                f"Incorrect number of questions displayed. "
                f"Expected: {original_number_of_questions} "
                f"Received: {new_number}"
            )

    # C890614, C890613, C890538
    @pytest.mark.aaqPage
    def test_post_aaq_questions_for_all_freemium_products_topics(self):
        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to each product aaq form")
        for product in super().general_test_data["freemium_products"]:
            self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"][product])

            for topic in self.sumo_pages.aaq_form_page._get_aaq_form_topic_options():
                self.logger.info(f"Submitting question for {product} product")
                question_info = self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
                    subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                    topic_name=topic,
                    body=super().aaq_question_test_data["valid_firefox_question"]["question_body"],
                    attach_image=False
                )

                self.logger.info("Verifying that the correct implicit tags are added to the "
                                 "question")
                slugs = [super().aaq_question_test_data['aaq_topic_tags'][product][topic]]
                if (super().aaq_question_test_data['aaq_topic_tags'][product]['default_slug']
                        != "none"):
                    slugs.append(
                        super().aaq_question_test_data['aaq_topic_tags'][product]['default_slug']
                    )
                assert (
                    all(map(
                        lambda x: x in self.sumo_pages.question_page._get_question_tag_options(),
                        slugs))
                )

                self.logger.info("Clicking on the 'My Questions' banner option")
                self.sumo_pages.question_page._click_on_my_questions_banner_option()

                self.logger.info(
                    "Verifying that the posted question is displayed inside the 'My Questions "
                    "page'")

                expect(
                    self.sumo_pages.my_questions_page._get_listed_question(
                        question_info['aaq_subject']
                    )
                ).to_be_visible()

                self.logger.info("Clicking on the question and deleting it")
                self.sumo_pages.my_questions_page._click_on_a_question_by_name(
                    question_info['aaq_subject']
                )

                self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
                self.sumo_pages.question_page._click_delete_this_question_button()

                self.logger.info(
                    "Verifying that the question is no longer displayed inside My Questions page")
                self.sumo_pages.top_navbar._click_on_my_questions_profile_option()

                expect(
                    self.sumo_pages.my_questions_page._get_listed_question(
                        question_info['aaq_subject']
                    )
                ).to_be_hidden()

                self.logger.info(f"Navigating back to the {product} product aa form")
                self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"][product])

    @pytest.mark.aaqPage
    def test_share_firefox_data_functionality(self):
        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to the Firefox AAQ form page")
        self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"]["Firefox"])

        self.logger.info("Clicking on the 'Share Data' option")
        self.sumo_pages.aaq_form_page._click_on_share_data_button()

        self.logger.info("Verifying that the 'try these manual steps' contains the correct link")
        check.equal(
            self.sumo_pages.aaq_form_page._get_try_these_manual_steps_link(),
            QuestionPageMessages.TRY_THESE_MANUAL_STEPS_LINK
        )

        self.logger.info("Adding data inside AAQ form fields without submitting the form")
        self.sumo_pages.aaq_flow.add__valid_data_to_all_input_fields_without_submitting(
            subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_value=self.sumo_pages.aaq_form_page._get_aaq_form_topic_options()[0],
            body_text=super().aaq_question_test_data["valid_firefox_question"]["question_body"]
        )

        self.logger.info("Adding text inside the troubleshooting information field")
        self.sumo_pages.aaq_form_page._add_text_to_troubleshooting_information_textarea(
            super().aaq_question_test_data["troubleshooting_information_textarea_field"]
        )

        self.logger.info("Submitting the aaq question")
        self.sumo_pages.aaq_form_page._click_aaq_form_submit_button()

        self.logger.info("Verifying that the troubleshooting information is displayed")
        self.sumo_pages.question_page._click_on_question_details_button()
        self.sumo_pages.question_page._click_on_more_system_details_option()

        expect(
            self.sumo_pages.question_page._get_more_information_with_text_locator(
                super().aaq_question_test_data["troubleshooting_information_textarea_field"]
            )
        ).to_be_visible()

        self.logger.info("Closing additional details panel")
        self.sumo_pages.question_page._click_on_the_additional_system_panel_close_button()

        self.logger.info("Deleting the posted question")
        self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
        self.sumo_pages.question_page._click_delete_this_question_button()

    @pytest.mark.aaqPage
    def test_additional_system_details_user_agent_information(self):
        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to each product aaq form")
        for product in super().general_test_data["freemium_products"]:
            self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"][product])

            self.logger.info(f"Submitting question for {product} product")
            self.sumo_pages.aaq_flow.submit_an_aaq_question_for_a_product(
                subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                topic_name=self.sumo_pages.aaq_form_page._get_aaq_form_topic_options()[0],
                body=super().aaq_question_test_data["valid_firefox_question"]["question_body"],
                attach_image=True
            )

            self.logger.info("Verifying that the correct user-agent information is displayed")
            self.sumo_pages.question_page._click_on_question_details_button()
            self.sumo_pages.question_page._click_on_more_system_details_option()

            check.equal(
                "User Agent: " + self.get_user_agent(),
                self.sumo_pages.question_page._get_user_agent_information(),
                f"Incorrect user agent displayed. "
                f"Expected: {'User Agent: ' + self.get_user_agent()} "
                f"Received: {self.sumo_pages.question_page._get_user_agent_information()}"
            )

            self.logger.info("Closing additional details panel")
            self.sumo_pages.question_page._click_on_the_additional_system_panel_close_button()

            self.logger.info("Deleting the posted question")
            self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
            self.sumo_pages.question_page._click_delete_this_question_button()

    @pytest.mark.aaqPage
    def test_system_details_information(self):
        troubleshooting_info = [
            super().aaq_question_test_data["troubleshoot_product_and_os_versions"][
                0],
            "Firefox " + super().aaq_question_test_data["troubleshoot_product_and_os_versions"][1]
        ]

        self.logger.info("Signing in with a admin user account")
        self.start_existing_session(super().username_extraction_from_email(
            self.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

        self.logger.info("Navigating to each product aaq form")
        for product in super().general_test_data["freemium_products"]:
            self.logger.info(product)
            if product == 'Firefox Reality' or product == "Thunderbird":
                continue
            else:
                self.navigate_to_link(super().aaq_question_test_data["products_aaq_url"][product])

                self.logger.info("Adding data inside AAQ form fields without submitting the form")
                self.sumo_pages.aaq_flow.add__valid_data_to_all_input_fields_without_submitting(
                    subject=super().aaq_question_test_data["valid_firefox_question"]["subject"],
                    topic_value=self.sumo_pages.aaq_form_page._get_aaq_form_topic_options()[0],
                    body_text=super().aaq_question_test_data["valid_firefox_question"][
                        "question_body"]
                )

                self.logger.info("Clicking on the 'Show details' option")
                self.sumo_pages.aaq_form_page._click_on_show_details_option()

                self.logger.info("Adding data to product version and OS fields")
                self.sumo_pages.aaq_form_page._add_text_to_product_version_field(
                    super().aaq_question_test_data[
                        "troubleshoot_product_and_os_versions"][1]
                )
                self.sumo_pages.aaq_form_page._add_text_to_os_field(
                    super().aaq_question_test_data[
                        "troubleshoot_product_and_os_versions"][0]
                )

                self.logger.info("Submitting the aaq question")
                self.sumo_pages.aaq_form_page._click_aaq_form_submit_button()

                self.logger.info(
                    "Verifying that the correct provided troubleshooting information is displayed")
                self.sumo_pages.question_page._click_on_question_details_button()
                check.equal(
                    self.sumo_pages.question_page._get_system_details_information(),
                    troubleshooting_info,
                    f"Expected: {troubleshooting_info} "
                    f"Received:{self.sumo_pages.question_page._get_system_details_information()}"
                )

                self.logger.info("Deleting the posted question")
                self.sumo_pages.question_page._click_delete_this_question_question_tools_option()
                self.sumo_pages.question_page._click_delete_this_question_button()
