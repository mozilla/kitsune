import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect, Page
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import (
    ContactSupportMessages)
from playwright_tests.messages.ask_a_question_messages.community_forums_messages import (
    SupportForumsPageMessages)
from playwright_tests.messages.ask_a_question_messages.product_solutions_messages import (
    ProductSolutionsMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C890363
@pytest.mark.smokeTest
@pytest.mark.contactSupportPage
def test_contact_support_page_content(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar via Ask a "
                     "Question > View All"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()

    with check, allure.step("Verifying that the current milestone is the correct one"):
        assert sumo_pages.contact_support_page.get_text_of_current_milestone(
        ) == ContactSupportMessages.CURRENT_MILESTONE

    with check, allure.step("Verifying that the correct page header is displayed"):
        assert sumo_pages.contact_support_page.get_contact_support_main_heading(
        ) == ContactSupportMessages.MAIN_HEADER

    with check, allure.step("Verifying that the correct page subheading is displayed"):
        assert sumo_pages.contact_support_page.get_contact_support_subheading_text(
        ) == ContactSupportMessages.SUBHEADING

    with allure.step("Verifying that each product card has the correct subheading"):
        for card in sumo_pages.contact_support_page.get_all_product_card_titles():
            with check, allure.step(f"Verifying {card} card has the correct subheading"):
                assert (ContactSupportMessages.PRODUCT_CARDS_SUBHEADING[card] == sumo_pages.
                        contact_support_page.get_product_card_subtitle(card))


# C890368, C890387, C890388
# T5696578, T5696592
@pytest.mark.smokeTest
@pytest.mark.contactSupportPage
def test_contact_support_page_cards_redirect(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar Ask a Question > "
                     "View All"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()

    for card in sumo_pages.contact_support_page.get_all_product_card_titles():
        with allure.step(f"Clicking on {card}"):
            sumo_pages.contact_support_page.click_on_a_particular_card(card)

        with check, allure.step("Verifying that we are on the correct product solutions page"):
            assert sumo_pages.product_solutions_page.get_product_solutions_heading(
            ) == card + ProductSolutionsMessages.PAGE_HEADER

        with check, allure.step("Verifying that we are on the correct milestone"):
            assert sumo_pages.product_solutions_page.get_current_milestone_text(
            ) == ProductSolutionsMessages.CURRENT_MILESTONE_TEXT

        with allure.step("Clicking on the 'Change Product' milestone"):
            sumo_pages.product_solutions_page.click_on_the_completed_milestone()


# T5696795
@pytest.mark.smokeTest
@pytest.mark.contactSupportPage
def test_browse_all_product_forums_button_redirect(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Accessing the contact support page via the top navbar Ask a Question > "
                     "View All option"):
        sumo_pages.top_navbar.click_on_browse_all_products_option()

    with allure.step("Clicking on browse all product forums button and verifying that we are "
                     "redirected to the correct page"):
        sumo_pages.contact_support_page.click_on_browse_all_product_forums_button()
        expect(page).to_have_url(SupportForumsPageMessages.PAGE_URL)
