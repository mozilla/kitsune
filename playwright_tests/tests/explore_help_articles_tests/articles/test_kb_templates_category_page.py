import allure
import pytest
from playwright.sync_api import expect, Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages


# C2266246
@pytest.mark.kbTemplatesCategoryPage
def test_unreviewed_template_visibility_in_templates_category(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    templates_category_link = utilities.different_endpoints['kb_categories_links']["Templates"]

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])
    test_user_two = create_user_factory(groups=["Knowledge Base Reviewers"])
    test_user_three = create_user_factory()

    with allure.step(f"Signing in with the {test_user['username']} KB Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new template without reviewing its first revision"):
        template_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            is_template=True, approve_first_revision=False
        )

    with check, allure.step("Verifying that the unreviewed template is displayed inside the "
                            "Templates category page for the KB Reviewer who created it"):
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_visible()

    with check, allure.step("Verifying that the unreviewed template is displayed inside the "
                            "Templates category page for a different KB Reviewer"):
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_visible()

    with check, allure.step("Verifying that the unreviewed template is not displayed inside the "
                            "Templates category page for a user without the necessary permissions"):
        utilities.start_existing_session(cookies=test_user_three)
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_hidden()

    with check, allure.step("Verifying that the unreviewed template is not displayed inside the "
                            "Templates category page for signed out users"):
        utilities.delete_cookies()
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_hidden()

# C2266246
@pytest.mark.kbTemplatesCategoryPage
def test_approved_template_visibility_in_templates_category(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    templates_category_link = utilities.different_endpoints['kb_categories_links']["Templates"]

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])
    test_user_two = create_user_factory()

    with allure.step(f"Signing in with the {test_user['username']} KB Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new template and approving its first revision"):
        template_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            is_template=True, approve_first_revision=True
        )

    with check, allure.step("Verifying that the approved template is displayed inside the "
                            "Templates category page for the KB Reviewer"):
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_visible()

    with check, allure.step("Verifying that the approved template is displayed inside the "
                            "Templates category page for a user without elevated permissions"):
        utilities.start_existing_session(cookies=test_user_two)
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_visible()

    with check, allure.step("Verifying that the approved template is displayed inside the "
                            "Templates category page for signed out users"):
        utilities.delete_cookies()
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_visible()


# C2266247, C891400
@pytest.mark.kbTemplatesCategoryPage
def test_deleted_template_not_visible_in_templates_category(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    templates_category_link = utilities.different_endpoints['kb_categories_links']["Templates"]

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"],
                                    permissions=["delete_document"])

    with allure.step(f"Signing in with the {test_user['username']} KB Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new template and approving its first revision"):
        template_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            is_template=True, approve_first_revision=True
        )

    with check, allure.step("Verifying that the template is displayed inside the Templates "
                            "category page before deletion"):
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_visible()

    with allure.step("Clicking on the template link from the Templates category page and "
                     "navigating to its history page"):
        sumo_pages.kb_category_page.click_on_article_from_list(template_details['article_title'])
        sumo_pages.kb_article_page.click_on_show_history_option()

    with allure.step("Deleting the template"):
        sumo_pages.kb_article_show_history_page.click_on_delete_this_document_button()
        sumo_pages.kb_article_show_history_page.click_on_confirmation_delete_button()

    with check, allure.step("Verifying that the deleted template is no longer displayed inside "
                            "the Templates category page for the KB Reviewer"):
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_hidden()

    with check, allure.step("Verifying that the deleted template is no longer displayed inside "
                            "the Templates category page for signed out users"):
        utilities.delete_cookies()
        utilities.navigate_to_link(templates_category_link)
        expect(sumo_pages.kb_category_page.article_from_list(
            template_details['article_title'])).to_be_hidden()


# C891402
@pytest.mark.kbTemplatesCategoryPage
def test_templates_category_page_pagination(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    templates_category_link = utilities.different_endpoints['kb_categories_links']["Templates"]

    with allure.step("Navigating to the Templates category page"):
        utilities.navigate_to_link(templates_category_link)

    with check, allure.step("Verifying that the pagination is displayed and that we are on the "
                            "first pagination page"):
        expect(sumo_pages.kb_category_page.pagination_section).to_be_visible()
        expect(sumo_pages.kb_category_page.selected_pagination_page).to_have_text("1")
        first_page_templates = sumo_pages.kb_category_page.get_all_listed_articles()

    with check, allure.step("Clicking on the 'Next' pagination button and verifying that we are "
                            "navigated to the second page with a new set of templates"):
        sumo_pages.kb_category_page.click_on_next_pagination_page()
        expect(sumo_pages.kb_category_page.selected_pagination_page).to_have_text("2")
        assert "page=2" in utilities.get_page_url(), (
            "The URL was not updated with the second pagination page query parameter")
        second_page_templates = sumo_pages.kb_category_page.get_all_listed_articles()
        assert set(second_page_templates) - set(first_page_templates), (
            "The second pagination page is not displaying a new set of templates")

    with check, allure.step("Clicking on the 'Previous' pagination button and verifying that we "
                            "are navigated back to the first page with a new set of templates"):
        sumo_pages.kb_category_page.click_on_previous_pagination_page()
        expect(sumo_pages.kb_category_page.selected_pagination_page).to_have_text("1")
        first_page_templates_revisited = sumo_pages.kb_category_page.get_all_listed_articles()
        assert set(first_page_templates_revisited) - set(second_page_templates), (
            "The first pagination page is not displaying a new set of templates")

    with check, allure.step("Clicking on the second pagination page number and verifying that a "
                            "new set of templates is displayed"):
        sumo_pages.kb_category_page.click_on_pagination_page(2)
        expect(sumo_pages.kb_category_page.selected_pagination_page).to_have_text("2")
        second_page_templates_revisited = sumo_pages.kb_category_page.get_all_listed_articles()
        assert set(second_page_templates_revisited) - set(first_page_templates_revisited), (
            "The second pagination page is not displaying a new set of templates")
