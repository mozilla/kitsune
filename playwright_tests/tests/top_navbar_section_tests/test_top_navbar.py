import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import \
    ContactSupportMessages
from playwright_tests.messages.ask_a_question_messages.community_forums_messages import \
    SupportForumsPageMessages
from playwright_tests.messages.explore_help_articles.products_page_messages import \
    ProductsPageMessages
from playwright_tests.messages.top_navbar_messages import TopNavbarMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C876534, C890961
@pytest.mark.topNavbarTests
def test_number_of_options_not_signed_in(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with check, allure.step("Verifying that the SUMO logo is successfully displayed"):
        image = sumo_pages.top_navbar.get_sumo_nav_logo()
        image_link = image.get_attribute("src")
        response = utilities.get_api_response(page, image_link)
        assert response.status < 400

    with allure.step("Verifying that the top-navbar for signed in users contains: Explore "
                     "Help Articles, Community Forums, Ask a Question and Contribute"):
        expect(sumo_pages.top_navbar.menu_titles).to_have_text(
            TopNavbarMessages.TOP_NAVBAR_OPTIONS)


# C876539
@pytest.mark.topNavbarTests
def test_number_of_options_signed_in(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step("Signing in using a non-admin user"):
        utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Verifying that the SUMO logo is successfully displayed"):
        image = sumo_pages.top_navbar.get_sumo_nav_logo()
        image_link = image.get_attribute("src")
        response = utilities.get_api_response(page, image_link)
        assert response.status < 400

    with allure.step("Verifying that the top-navbar contains: Explore Help Articles, "
                     "Community Forums, Ask a Question, Contribute"):
        expect(sumo_pages.top_navbar.menu_titles).to_have_text(
            TopNavbarMessages.TOP_NAVBAR_OPTIONS)


# C2462866
@pytest.mark.smokeTest
@pytest.mark.topNavbarTests
def test_explore_by_product_redirects(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Clicking on all options from the 'Explore Help Articles' and verifying the "
                     "redirect"):
        for index, option in enumerate(
            sumo_pages.top_navbar.get_all_explore_by_product_options_locators()):
            current_option = sumo_pages.top_navbar.get_text_of_option_and_click(
                option,
                sumo_pages.top_navbar.hover_over_explore_by_product_top_navbar_option,
                is_first=index == 0,
            )

            if current_option == "Firefox desktop":
                current_option = utilities.remove_character_from_string(current_option, 'desktop')

            if current_option != "View all products":
                expect(sumo_pages.product_support_page.product_title).to_contain_text(
                    current_option)
            else:
                expect(sumo_pages.products_page.page_header).to_have_text(
                    ProductsPageMessages.PRODUCTS_PAGE_HEADER)


# C2462867, C2663957
@pytest.mark.smokeTest
@pytest.mark.topNavbarTests
def test_explore_by_topic_redirects(page: Page):
    sumo_pages = SumoPages(page)

    with allure.step("Clicking on all options from the 'Explore by topic' and verifying the "
                     "redirect"):
        for index, option in enumerate(sumo_pages.top_navbar.get_all_explore_by_topic_locators()):
            current_option = sumo_pages.top_navbar.get_text_of_option_and_click(
                option,
                sumo_pages.top_navbar.hover_over_explore_by_product_top_navbar_option,
                is_first=index == 0,
            )
            expect(sumo_pages.explore_by_topic_page.explore_by_topic_page_header).to_have_text(
                current_option)

            with check, allure.step("Verifying that the correct option is selected inside the"
                                    " 'All Topics' side navbar"):
                expect(sumo_pages.explore_by_topic_page.all_topics_selected_option).to_have_text(
                    current_option)

            with check, allure.step("Verifying that the 'All Products' option is displayed inside"
                                    " the 'Filter by product' dropdown"):
                expect(sumo_pages.explore_by_topic_page.filter_by_product_dropdown_selected_option
                       ).to_have_text("All Products")


# C2462868
@pytest.mark.smokeTest
@pytest.mark.topNavbarTests
def test_browse_by_product_community_forum_redirect(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on all options from the 'Browse by product' and verifying the "
                     "redirect"):
        for index, option in enumerate(
            sumo_pages.top_navbar.get_all_browse_by_product_options_locators()):
            current_option = sumo_pages.top_navbar.get_text_of_option_and_click(
                option,
                sumo_pages.top_navbar.hover_over_community_forums_top_navbar_option,
                is_first=index == 0,
            )

            if current_option == "Firefox desktop":
                current_option = utilities.remove_character_from_string(
                    current_option, 'desktop').rstrip()

            if current_option != "View all forums":
                expect(sumo_pages.product_support_page.product_title).to_have_text(
                    f"{current_option} Community Forum")
            else:
                expect(page).to_have_url(SupportForumsPageMessages.PAGE_URL)


# C2462869
@pytest.mark.smokeTest
@pytest.mark.topNavbarTests
def test_browse_all_forum_threads_by_topic_redirect(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on all options from the 'Browse all forum threads by topic' and "
                     "verifying the redirect"):
        for index, option in enumerate(
            sumo_pages.top_navbar.get_all_browse_all_forum_threads_by_topic_locators()):
            current_option = sumo_pages.top_navbar.get_text_of_option_and_click(
                option,
                sumo_pages.top_navbar.hover_over_community_forums_top_navbar_option,
                is_first=index == 0,
            )
            expect(sumo_pages.product_support_page.product_title).to_have_text(
                "All Products Community Forum")

            with allure.step("Verifying that the correct default topic filter is selected"):
                expect(sumo_pages.product_support_forum.topic_dropdown_selected_option
                       ).to_have_text(current_option)


# T5696576, T5696591, C2663303
@pytest.mark.smokeTest
@pytest.mark.topNavbarTests
def test_ask_a_question_top_navbar_redirect(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Clicking on all options from the 'Ask a Question' and verifying the "
                     "redirect"):
        for index, option in enumerate(sumo_pages.top_navbar.get_all_ask_a_question_locators()):
            current_option = sumo_pages.top_navbar.get_text_of_option_and_click(
                option,
                sumo_pages.top_navbar.hover_over_ask_a_question_top_navbar,
                is_first=index == 0,
            )
            redirect_target = utilities.general_test_data['subscription_redirects'].get(
                current_option
            )

            if current_option == "Firefox desktop":
                current_option = utilities.remove_character_from_string(
                    current_option, 'desktop').rstrip()
            elif current_option == "Monitor":
                current_option = f"Mozilla {current_option}"

            if redirect_target:
                expect(sumo_pages.product_solutions_page.product_title_heading).to_have_text(
                    f"{redirect_target} Solutions")
            elif current_option != "View all":
                expect(sumo_pages.product_solutions_page.product_title_heading).to_have_text(
                    f"{current_option} Solutions")
            else:
                expect(page).to_have_url(ContactSupportMessages.PAGE_URL)


# C2462871, C890957
@pytest.mark.smokeTest
@pytest.mark.topNavbarTests
def test_contribute_top_navbar_redirects(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    utilities.start_existing_session(cookies=test_user)

    with allure.step("Clicking on the 'Contributor discussions' top-navbar option and verifying "
                     "the redirect"):
        sumo_pages.top_navbar.click_on_contributor_discussions_top_navbar_option()
        expect(sumo_pages.contributor_discussions_page.contributor_discussions_page_title
               ).to_contain_text("Contributor Discussions", ignore_case=True)

    with allure.step("Clicking on the 'Contributor discussions' top-navbar options and verifying "
                     "the redirects"):
        for index, option in enumerate(sumo_pages.top_navbar
                                       .get_all_contributor_discussions_locators()):
            current_option = sumo_pages.top_navbar.get_text_of_option_and_click(
                option,
                sumo_pages.top_navbar.hover_over_contribute_top_navbar,
                is_first=index == 0,
            )

            if current_option == "Article discussions":
                expect(sumo_pages.forum_discussions_page.forum_page_title).to_contain_text(
                    "english knowledge base discussions", ignore_case=True)
                with allure.step("Verifying that the correct option is highlighted inside the "
                                 "'Contributor discussions' side navbar"):
                    expect(sumo_pages.forum_discussions_page.forum_side_nav_selected_option
                           ).to_contain_text(current_option, ignore_case=True)
            elif current_option == "View all discussions":
                expect(sumo_pages.contributor_discussions_page.contributor_discussions_page_title
                       ).to_contain_text("contributor discussions", ignore_case=True)
            else:
                expect(sumo_pages.forum_discussions_page.forum_page_title).to_contain_text(
                    current_option, ignore_case=True)
                with allure.step("Verifying that the correct option is highlighted inside the "
                                 "'Contributor discussions' side navbar"):
                    expect(sumo_pages.forum_discussions_page.forum_side_nav_selected_option
                           ).to_contain_text(current_option, ignore_case=True)
