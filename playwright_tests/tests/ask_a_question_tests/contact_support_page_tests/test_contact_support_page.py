import pytest
import pytest_check as check
from playwright.sync_api import expect

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import (
    ContactSupportMessages)
from playwright_tests.messages.contribute_messages.con_discussions.support_forums_messages import (
    SupportForumsPageMessages)
from playwright_tests.messages.ask_a_question_messages.product_solutions_messages import (
    ProductSolutionsMessages)


class TestContactSupportPage(TestUtilities):
    # C890363
    @pytest.mark.contactSupportPage
    def test_contact_support_page_content(self):
        self.logger.info("Accessing the contact support page via the top navbar Get Help > Ask a "
                         "Question")
        self.sumo_pages.top_navbar._click_on_ask_a_question_option()

        self.logger.info("Verifying that the current milestone is the correct one")
        check.equal(
            self.sumo_pages.contact_support_page._get_text_of_current_milestone(),
            ContactSupportMessages.CURRENT_MILESTONE,
            f"Incorrect current milestone displayed. "
            f"Expected: {ContactSupportMessages.CURRENT_MILESTONE}"
            f"Received: {self.sumo_pages.contact_support_page._get_text_of_current_milestone()}"
        )

        self.logger.info("Verifying that the correct page header is displayed")
        check.equal(
            self.sumo_pages.contact_support_page._get_contact_support_main_heading(),
            ContactSupportMessages.MAIN_HEADER,
            f"Incorrect page header displayed. "
            f"Expected: {ContactSupportMessages.MAIN_HEADER} "
            f"Received: {self.sumo_pages.contact_support_page._get_contact_support_main_heading()}"
        )

        self.logger.info("Verifying that the correct page subheading is displayed")
        check.equal(
            self.sumo_pages.contact_support_page._get_contact_support_subheading_text(),
            ContactSupportMessages.SUBHEADING,
            f"Incorrect page subheading displayed. "
            f"Expected: {ContactSupportMessages.SUBHEADING} "
            f"Actual:{self.sumo_pages.contact_support_page._get_contact_support_subheading_text()}"
        )

        self.logger.info("Verifying that each product card has the correct subheading")
        for card in self.sumo_pages.contact_support_page._get_all_product_card_titles():
            check.equal(
                ContactSupportMessages.PRODUCT_CARDS_SUBHEADING[card],
                self.sumo_pages.contact_support_page._get_product_card_subtitle(card),
                f"Incorrect card subheading displayed "
                f"Expected: {ContactSupportMessages.PRODUCT_CARDS_SUBHEADING[card]} "
                f"Actual: {self.sumo_pages.contact_support_page._get_product_card_subtitle(card)}"
            )

    # C890368, C890387, C890388
    @pytest.mark.contactSupportPage
    def test_contact_support_page_cards_redirect(self):
        self.logger.info("Accessing the contact support page via the top navbar Get Help > "
                         "Browse All products")
        self.sumo_pages.top_navbar._click_on_browse_all_products_option()

        self.logger.info("Clicking on all product cards")

        for card in self.sumo_pages.contact_support_page._get_all_product_card_titles():
            self.sumo_pages.contact_support_page._click_on_a_particular_card(card)

            self.logger.info("Verifying that we are on the correct product solutions page")
            check.equal(
                self.sumo_pages.product_solutions_page._get_product_solutions_heading(),
                card + ProductSolutionsMessages.PAGE_HEADER,
                f"Incorrect product solutions page displayed: "
                f"Expected: {card + ProductSolutionsMessages.PAGE_HEADER} "
                f"Actual:{self.sumo_pages.product_solutions_page._get_product_solutions_heading()}"
            )

            self.logger.info("Verifying that we are on the correct milestone")
            check.equal(
                self.sumo_pages.product_solutions_page._get_current_milestone_text(),
                ProductSolutionsMessages.CURRENT_MILESTONE_TEXT,
                f"Incorrect current milestone displayed "
                f"Expected: {ProductSolutionsMessages.CURRENT_MILESTONE_TEXT} "
                f"Received: {self.sumo_pages.product_solutions_page._get_current_milestone_text()}"
            )

            self.logger.info("Click on the 'Change Product' milestone")
            self.sumo_pages.product_solutions_page._click_on_the_completed_milestone()

    @pytest.mark.contactSupportPage
    def test_browse_all_product_forums_button_redirect(self):
        self.logger.info("Accessing the contact support page via the top navbar Get Help > Ask a "
                         "Question")
        self.sumo_pages.top_navbar._click_on_ask_a_question_option()

        self.sumo_pages.contact_support_page._click_on_browse_all_product_forums_button()

        self.logger.info("Verifying that we are redirected to the correct page url")

        expect(
            self.page
        ).to_have_url(SupportForumsPageMessages.PAGE_URL)
