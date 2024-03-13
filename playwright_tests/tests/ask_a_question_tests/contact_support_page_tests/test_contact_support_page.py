import allure
import pytest
from pytest_check import check
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
        with allure.step("Accessing the contact support page via the top navbar Get Help > Ask a "
                         "Question"):
            self.sumo_pages.top_navbar._click_on_ask_a_question_option()

        with check, allure.step("Verifying that the current milestone is the correct one"):
            assert self.sumo_pages.contact_support_page._get_text_of_current_milestone(
            ) == ContactSupportMessages.CURRENT_MILESTONE

        with check, allure.step("Verifying that the correct page header is displayed"):
            assert self.sumo_pages.contact_support_page._get_contact_support_main_heading(
            ) == ContactSupportMessages.MAIN_HEADER

        with check, allure.step("Verifying that the correct page subheading is displayed"):
            assert self.sumo_pages.contact_support_page._get_contact_support_subheading_text(
            ) == ContactSupportMessages.SUBHEADING

        with allure.step("Verifying that each product card has the correct subheading"):
            for card in self.sumo_pages.contact_support_page._get_all_product_card_titles():
                with check, allure.step(f"Verifying {card} card has the correct subheading"):
                    assert (ContactSupportMessages.
                            PRODUCT_CARDS_SUBHEADING[card] == self.sumo_pages.
                            contact_support_page._get_product_card_subtitle(card))

    # C890368, C890387, C890388
    @pytest.mark.contactSupportPage
    def test_contact_support_page_cards_redirect(self):
        with allure.step("Accessing the contact support page via the top navbar Get Help > "
                         "Browse All products"):
            self.sumo_pages.top_navbar._click_on_browse_all_products_option()

        for card in self.sumo_pages.contact_support_page._get_all_product_card_titles():
            with allure.step(f"Clicking on {card}"):
                self.sumo_pages.contact_support_page._click_on_a_particular_card(card)

            with check, allure.step("Verifying that we are on the correct product solutions page"):
                assert self.sumo_pages.product_solutions_page._get_product_solutions_heading(
                ) == card + ProductSolutionsMessages.PAGE_HEADER

            with check, allure.step("Verifying that we are on the correct milestone"):
                assert self.sumo_pages.product_solutions_page._get_current_milestone_text(
                ) == ProductSolutionsMessages.CURRENT_MILESTONE_TEXT

            with allure.step("Click on the 'Change Product' milestone"):
                self.sumo_pages.product_solutions_page._click_on_the_completed_milestone()

    @pytest.mark.contactSupportPage
    def test_browse_all_product_forums_button_redirect(self):
        with allure.step("Accessing the contact support page via the top navbar Get Help > Ask a "
                         "Question"):
            self.sumo_pages.top_navbar._click_on_ask_a_question_option()

        with allure.step("Clicking on browse all product forums button and verifying that we are "
                         "redirected to the correct page"):
            self.sumo_pages.contact_support_page._click_on_browse_all_product_forums_button()
            expect(
                self.page
            ).to_have_url(SupportForumsPageMessages.PAGE_URL)
