import random
import time
import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import \
    QuestionPageMessages
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.search_page_messages import SearchPageMessage
from playwright_tests.pages.sumo_pages import SumoPages


# C890369
@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_product_solutions_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "NVDA fails to load"

    with allure.step("Navigating to the Firefox product solutions page and using the searchbar to "
                     "search for a particular kb Article"):
        utilities.navigate_to_link(utilities.general_test_data['product_solutions']['Firefox'])
        sumo_pages.search_page.fill_into_searchbar(text=test_article_name, is_aaq=True)

    with allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.fill_into_searchbar(text=test_question_name, is_aaq=True)

    with allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"


@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_product_support_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "NVDA fails to load"

    with allure.step("Navigating to the Firefox product support page and using the searchbar to "
                     "search for a particular kb Article"):
        utilities.navigate_to_link(utilities.general_test_data['product_support']['Firefox'])
        sumo_pages.search_page.fill_into_searchbar(test_article_name)

    with allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.fill_into_searchbar(test_question_name)

    with allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"


@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_explore_by_topic_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "NVDA fails to load"

    with allure.step("Navigating to the 'Browse' explore by topic page and using the searchbar to "
                     "search for a particular kb Article"):
        utilities.navigate_to_link("https://support.allizom.org/en-US/topics/browse")
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"


# C891284
@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_product_community_forum_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "NVDA fails to load"

    with allure.step("Navigating to the Firefox community forum page and using the searchbar to "
                     "search for a particular kb Article"):
        utilities.navigate_to_link("https://support.allizom.org/en-US/questions/firefox")
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"


@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_browse_all_forum_threads_by_topic_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "NVDA fails to load"

    with allure.step("Navigating to the 'Settings' browse all forum threads by topic page and "
                     "using the searchbar to search for a particular kb Article"):
        utilities.navigate_to_link("https://support.allizom.org/en-US/questions/topic/settings")
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"


# C1329227, C1492391
@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_and_search_filters(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_user = create_user_factory()
    search_page_messages = SearchPageMessage()

    with allure.step("Submitting a new Firefox AAQ question and using the searchbar to search for "
                     "a particular kb Article and for the submitted question"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        question_info = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.
            aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.
            aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )
        question_tile = question_info["aaq_subject"]

    with allure.step("Leaving a question reply so the question will be returned in search "
                     "results"):
        sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=test_user["username"],
            reply=utilities.aaq_question_test_data['valid_firefox_question']['question_reply']
        )
        utilities.wait_for_given_timeout(65000)
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    product_filter = sumo_pages.search_page.get_the_highlighted_side_nav_item()

    with check, allure.step("Verifying that the question is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert product_filter == "All Products"

    with check, allure.step("Verifying that the 'View All' filter is applied"):
        result_count = utilities.number_extraction_from_string(
            sumo_pages.search_page.get_search_results_header())
        assert sumo_pages.search_page.get_doctype_filter() == "View All"
        assert (sumo_pages.search_page.get_search_results_header() in search_page_messages.
                expected_found_search_results_message(search_results_count=str(result_count),
                                                      search_string=test_article_name,
                                                      product_filter_option=product_filter))

    with check, allure.step("Clicking on the 'Help Articles only' option and verifying that:"
                            "1.The correct search results message is displayed."
                            "2.The correct doctype filter is applied."
                            "3.The article is successfully returned inside the search results."):
        sumo_pages.search_page.click_on_help_articles_only_doctype_filter()
        utilities.wait_for_given_timeout(2000)
        result_count = utilities.number_extraction_from_string(
            sumo_pages.search_page.get_search_results_header())
        assert sumo_pages.search_page.get_doctype_filter() == "Help Articles Only"
        assert (sumo_pages.search_page.get_search_results_header() in search_page_messages.
                expected_found_search_results_message(search_results_count=str(result_count),
                                                      search_string=test_article_name,
                                                      product_filter_option=product_filter))
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Clicking on the 'Community Discussions Only' and verifying that:"
                            "1. The correct search results message is displayed."
                            "2. The correct doctype filter is applied."
                            "3. The article is not returned inside the search results."):
        sumo_pages.search_page.click_on_community_discussions_only_doctype_filter()
        utilities.wait_for_given_timeout(2000)
        assert sumo_pages.search_page.get_doctype_filter() == "Community Discussion Only"
        assert (sumo_pages.search_page.get_search_results_header() in search_page_messages.
                expected_no_results_search_results_message(search_string=test_article_name,
                                                           product_filter_option=product_filter))
        assert (test_article_name not in sumo_pages.search_page.
                get_all_search_results_article_titles())

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(question_tile, is_sidebar=True)
        utilities.wait_for_given_timeout(2000)
        result_count = utilities.number_extraction_from_string(
            sumo_pages.search_page.get_search_results_header())

    with check, allure.step("Verifying that:"
                            "1. The question is successfully returned inside the search results."
                            "2. The correct doctype filter is applied."
                            "3. The correct search results message is returned."):
        assert (question_tile in sumo_pages.search_page.
                get_all_search_results_article_titles())
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"
        assert sumo_pages.search_page.get_doctype_filter() == "Community Discussion Only"
        assert (sumo_pages.search_page.get_search_results_header() in search_page_messages.
                expected_found_search_results_message(search_results_count=str(result_count),
                                                      search_string=question_tile,
                                                      product_filter_option=product_filter))

    with check, allure.step("Clicking on the 'Help Articles Only' doctype filter and verifying:"
                            "1. The question is not returned inside the search results."
                            "2. The correct doctype filter is applied."
                            "3. The correct search results message is returned."):
        sumo_pages.search_page.click_on_help_articles_only_doctype_filter()
        utilities.wait_for_given_timeout(2000)
        assert (question_tile not in sumo_pages.search_page.
                get_all_search_results_article_titles())
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"
        assert sumo_pages.search_page.get_doctype_filter() == "Help Articles Only"
        assert (sumo_pages.search_page.get_search_results_header() in search_page_messages.
                expected_no_results_search_results_message(search_string=question_tile,
                                                           product_filter_option=product_filter))

    with check, allure.step("Clicking on the 'View All' doctype filter and verifying:"
                            "1. The question is successfully returned inside the search results."
                            "2. The correct doctype filter is applied."
                            "3. The correct search results message is returned."):
        sumo_pages.search_page.click_on_view_all_doctype_filter()
        utilities.wait_for_given_timeout(2000)
        result_count = utilities.number_extraction_from_string(
            sumo_pages.search_page.get_search_results_header())
        assert (question_tile in sumo_pages.search_page.
                get_all_search_results_article_titles())
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"
        assert sumo_pages.search_page.get_doctype_filter() == "View All"
        assert (sumo_pages.search_page.get_search_results_header() == search_page_messages.
                expected_found_search_results_message(search_results_count=str(result_count),
                                                      search_string=question_tile,
                                                      product_filter_option=product_filter))


# C890835
@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_on_article_page(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "NVDA fails to load"
    test_user = create_user_factory(groups=["kb-contributors"])

    with allure.step("Submitting a new KB article against the Firefox product and using the "
                     "searchbar to search for a particular kb Article"):
        utilities.start_existing_session(cookies=test_user)

        sumo_pages.submit_kb_article_flow.submit_simple_kb_article()
        sumo_pages.kb_article_page.click_on_article_option()

        utilities.wait_for_given_timeout(2000)
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct "
                     "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with allure.step("Verifying that the filter by product is applied to the correct product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"
    sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)


# C1329220
@pytest.mark.searchTests
def test_popular_searches_homepage(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Clicking on all popular searches for the homepage searchbar"):
        for popular_search in sumo_pages.search_page.get_list_of_popular_searches():
            sumo_pages.search_page.click_on_a_popular_search(popular_search)
            with allure.step("Verifying that the correct text is added inside the search field"):
                assert sumo_pages.search_page.get_text_of_searchbar_field() == popular_search

            with allure.step("Verifying that 'All products' is highlighted inside the "
                             "side-navbar"):
                assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"
            with allure.step("Verifying that search results contain the correct keyword"):
                if not sumo_pages.search_page.get_all_search_results_article_titles():
                    raise AssertionError(f"Search results contains 0 results for the {popular_search} " f"search term")
                for title in sumo_pages.search_page.get_all_search_results_article_titles():
                    content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                        title
                    )
                    assert _verify_search_results(page, popular_search, 'english', title, content)
            with allure.step("Navigating back"):
                utilities.navigate_back()


# Skipping because of https://github.com/mozilla/sumo/issues/1924 failure.
# This tests also causes a failure (driver becomes unresponsive) on rerun which needs to be
# investigated.
@pytest.mark.skip
def test_popular_searches_products(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Navigating to each product support page"):
        for product, support_link in utilities.general_test_data['product_support'].items():
            print(support_link)
            utilities.navigate_to_link(support_link)
            for popular_search in sumo_pages.search_page.get_list_of_popular_searches():
                sumo_pages.search_page.click_on_a_popular_search(popular_search)
                with allure.step("Verifying that the correct text was added inside the search"
                                 " field"):
                    assert sumo_pages.search_page.get_text_of_searchbar_field() == popular_search

                with allure.step("Verifying that the correct product is listed in the side "
                                 "navbar"):
                    assert sumo_pages.search_page.get_the_highlighted_side_nav_item(
                    ) == product.strip()
                    if not sumo_pages.search_page.get_all_search_results_article_titles():
                        raise AssertionError(f"Search results contains 0 results for the" f" {popular_search} search term on the {product}" f" product!")

                for title in sumo_pages.search_page.get_all_search_results_article_titles():
                    content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                        title)
                    assert _verify_search_results(page, popular_search, 'english', title, content)

                with allure.step("Navigating back"):
                    utilities.navigate_back()


# C1329221
@pytest.mark.searchTests
def test_stopwords(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_term = 'oricând instalez firefox'

    with allure.step("Switching the SUMO version to RO"):
        sumo_pages.footer_section.switch_to_a_locale("ro")
        utilities.wait_for_given_timeout(2000)

    with allure.step("Adding a search term inside the search bar which contains a stopword: "
                     "'oricând' and verifying that it does not impact the search result"):
        sumo_pages.search_page.fill_into_searchbar(search_term)

        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            assert _verify_search_results(page, search_term.replace('oricând', ''),
                                          'romanian', title, content)


# C1329222, C2667545
@pytest.mark.searchTests
def test_synonyms(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ['addon', 'add-on', 'add', 'how to add bookmarks', 'how to add themes',
                    'pop-ups', 'popups', 'pop ups', 'bookmarks bar', 'bookmark bar',
                    'bookmarks toolbar', 'bookmark toolbar']
    with allure.step("Adding a search term and validating the search results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)

                assert _verify_search_results(page, search_term, 'english', title, content)


# C2796125
@pytest.mark.searchTests
def test_pagination_scroll_position(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Adding the 'Test' search term and clicking on the next pagination item"):
        sumo_pages.search_page.fill_into_searchbar("Test")
        sumo_pages.common_web_elements.click_on_next_pagination_item()
        utilities.wait_for_given_timeout(1000)

    with check, allure.step("Verifying that the page is scrolled to the top of the page and the"
                            "highlighted pagination item is 1"):
        assert utilities.fetch_scrolly() == 0
        assert sumo_pages.common_web_elements.get_selected_pagination_item() == "2"

    with check, allure.step("Clicking on the 4 pagination item and verifying that the page is "
                            "scrolled to the top of the page and the highlighted pagination item "
                            "is 4"):
        sumo_pages.common_web_elements.click_on_pagination_item("4")
        utilities.wait_for_given_timeout(1000)
        assert utilities.fetch_scrolly() == 0
        assert sumo_pages.common_web_elements.get_selected_pagination_item() == "4"

    with check, allure.step("Clicking on the previous pagination item and verifying that the "
                            "page is scrolled to the top of the page and the highlighted "
                            "pagination item is 2"):
        sumo_pages.common_web_elements.click_on_previous_pagination_item()
        utilities.wait_for_given_timeout(1000)
        assert utilities.fetch_scrolly() == 0
        assert sumo_pages.common_web_elements.get_selected_pagination_item() == "3"


# C1329223
@pytest.mark.searchTests
def test_brand_synonyms(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ['mozilla', 'modzilla', 'mozzila', 'mozzilla', 'mozila', 'ios', 'ipad',
                    'iphone', 'ipod']
    with allure.step("Adding a search term inside the search bar and validating search results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)

                assert _verify_search_results(page, search_term, 'english', title, content)


#  C1329234
@pytest.mark.searchTests
def test_searchbar_content_during_navigation(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_term = 'test'

    with allure.step("Typing inside the searchbar and navigating back"):
        sumo_pages.search_page.fill_into_searchbar(search_term)
        sumo_pages.search_page._wait_for_visibility_of_search_results_section()
        utilities.navigate_back()

    with allure.step("Verifying that the searchbar is empty"):
        assert sumo_pages.search_page.get_text_of_searchbar_field() == ''

    with allure.step("Navigating forward and verifying that the previously added search term is"
                     " displayed inside the searchbar"):
        utilities.navigate_forward()
        assert sumo_pages.search_page.get_text_of_searchbar_field() == search_term


# C1329236
@pytest.mark.searchTests
def test_logo_redirect_during_search(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_term = 'test'

    with allure.step("Typing inside the searchbar and clicking on the logo"):
        sumo_pages.search_page.fill_into_searchbar(search_term)
        sumo_pages.search_page._wait_for_visibility_of_search_results_section()
        sumo_pages.top_navbar.click_on_sumo_nav_logo()

    with allure.step("Verifying that the user was redirected to the homepage and that the "
                     "searchbar is empty"):
        assert utilities.get_page_url() == HomepageMessages.STAGE_HOMEPAGE_URL_EN_US
        assert sumo_pages.search_page.get_text_of_searchbar_field() == ''

    with allure.step("Navigating back and verifying that the searchbar contains the previously"
                     " used search term"):
        utilities.navigate_back()
        assert sumo_pages.search_page.get_text_of_searchbar_field() == search_term


# C1329239
@pytest.mark.searchTests
def test_searchbar_search_update(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ['Mozilla', 'Mozilla themes', 'install']

    with allure.step("Adding a search term inside the search bar and validating search results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)
                assert _verify_search_results(page, search_term, 'english', title, content)


# C1329243
@pytest.mark.searchTests
def test_search_from_products_page(page: Page):
    sumo_pages = SumoPages(page)
    search_term = 'Mozilla'

    with allure.step("Clicking on each product card from the SUMO homepage"):
        card_titles = sumo_pages.homepage.get_text_of_product_card_titles()
        for product_card in card_titles:
            with allure.step("Verifying that the search results are filtered by the correct"
                             " product and the search term is present"):
                sumo_pages.homepage.click_on_product_card_by_title(product_card)
                sumo_pages.search_page.fill_into_searchbar(search_term)
                assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == product_card
                for title in sumo_pages.search_page.get_all_search_results_article_titles():
                    content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                        title)
                    assert _verify_search_results(page, search_term, 'english', title, content)

            with allure.step("Navigating back to the homepage"):
                sumo_pages.top_navbar.click_on_sumo_nav_logo()


# C1329243
@pytest.mark.searchTests
def test_filter_switching(page: Page):
    sumo_pages = SumoPages(page)
    search_term = "Firefox Focus"

    with allure.step("Adding a search term inside the search bar and validating search results"):
        sumo_pages.search_page.fill_into_searchbar(search_term)
        sumo_pages.search_page.click_on_a_particular_side_nav_item('Firefox for Android')
        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            assert _verify_search_results(page, search_term, 'english', title, content)

        with allure.step("Switching the product filter to something that returns 0 results"):
            sumo_pages.search_page.click_on_a_particular_side_nav_item('Firefox Relay')
            time.sleep(2)
            assert not sumo_pages.search_page.is_search_content_section_displayed()


# C1349875, C1349876
@pytest.mark.searchTests
def test_advanced_search_syntax(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ["crash sync", "crash + sync", "crash - sync", "crash +- sync"]

    with allure.step("Adding a search term inside the search bar and validating search results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)
                assert _verify_search_results(page, search_term, 'english', title, content)


# C1350860, C1349859, C1352396, C1352398, C1350863
@pytest.mark.searchTests
def test_conjunctions_and_disjunction_operators(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ["add-ons AND cache", "clear AND add-ons AND cache"]

    with allure.step("Adding a search term inside the search bar and validating search results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)
                assert _verify_search_results(page, search_term.replace("AND", ""), 'english',
                                              title, content), (f"{search_term} not found in "
                                                                f"search result with title: "
                                                                f"{title} and bolded content: "
                                                                f"{content}")

# C1358447
@pytest.mark.searchTests
def test_search_by_doc_id(page: Page):
    sumo_pages = SumoPages(page)

    # 67390 is the docId for the DoNotDelete article
    search_string = "field:doc_id.en-US:67390"
    document_title = "DoNotDelete"

    with allure.step("Searching by document Id and verifying that the correct document is"
                     " returned"):
        sumo_pages.search_page.fill_into_searchbar(search_string)
        assert document_title in sumo_pages.search_page.get_all_search_results_article_titles()


# C1350861, C1349864, C1352398
@pytest.mark.searchTests
@pytest.mark.parametrize("locale", ['en-US', 'ro'])
def test_or_operator(page: Page, locale):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_term = "crash OR Mozilla"

    if locale != 'en-US':
        utilities.navigate_to_link(f"https://support.allizom.org/{locale}")

    with allure.step("Adding a search term which contains the 'OR' inside the search term"):
        sumo_pages.search_page.fill_into_searchbar(search_term)

        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            assert _verify_search_results(page, search_term.replace("OR", ""), 'english',
                                          title, content), (f"{search_term} not found in "
                                                            f"search result with title: "
                                                            f"{title} and bolded content: "
                                                            f"{content}")


# C1350862, C1349865, # C1350993
@pytest.mark.searchTests
def test_not_operator(page: Page):
    sumo_pages = SumoPages(page)
    search_term = "crash NOT Mozilla"

    with allure.step("Adding a search term which contains the 'NOT' inside the search term"):
        sumo_pages.search_page.fill_into_searchbar(search_term)
        split_search_term = search_term.split("NOT")

        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            with allure.step("Verifying that the term used before the 'NOT' keyword is returned"):
                assert _verify_search_results(page, split_search_term[0].strip(), 'english',
                                              title, content), (f"{split_search_term[0]} not found"
                                                                f" in search result with title: "
                                                                f"{title} and bolded content: "
                                                                f"{content}")
            with allure.step("Verifying that the term used after the 'NOT' keyword is not "
                             "returned"):
                assert not _verify_search_results(page, split_search_term[1].strip(),
                                                  'english', title, content
                                                  ), (f"{split_search_term[1]} is found "
                                                      f"in search result with title: "
                                                      f"{title} and bolded content: "
                                                      f"{content}")


# C1350991, C1352392, C1352394
@pytest.mark.searchTests
def test_exact_phrase_searching(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_term = '"Firefox desktop"'
    second_search_term = '"Firefox desktop'
    no_results_search_term = '"test test bla blatest test"'

    with allure.step("Adding a search term which contains the quotes inside the search term"):
        sumo_pages.search_page.fill_into_searchbar(search_term)

        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            with allure.step("Verifying that all search results contain the full search term"):
                assert _verify_search_results(page, search_term, 'english',
                                              title, content, exact_phrase=True), (f"{search_term}"
                                                                                   f" not found "
                                                                                   f"in search "
                                                                                   f"result with "
                                                                                   f"title: "
                                                                                   f"{title} and "
                                                                                   f"bolded "
                                                                                   f"content: "
                                                                                   f"{content}")

        with allure.step("Adding a search term with invalid exact phrase searching syntax"):
            sumo_pages.search_page.fill_into_searchbar(second_search_term)
            not_exact_match = False
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)
                if not _verify_search_results(page, search_term, 'english', title, content,
                                              exact_phrase=True):
                    not_exact_match = True
                    break

            with allure.step("Verifying that not all search results contain the exact phrase"):
                assert not_exact_match

        with allure.step("Adding an exact search phrase which should return 0 results"):
            sumo_pages.search_page.fill_into_searchbar(no_results_search_term)
            utilities.wait_for_given_timeout(2000)

        with allure.step("Verifying that no results are returned for the given exact search "
                         "phrase"):
            assert not sumo_pages.search_page.is_search_content_section_displayed()


# C1352395, C1352397, C1352400, C1493903
@pytest.mark.searchTests
def test_keywords_field_and_content_operator(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(permissions=["review_revision"])

    utilities.start_existing_session(cookies=test_user)

    search_term_keyword = "field:keywords.en-US:playwright search test"
    second_search_term_keyword = "field:keywords.en-US:(playwright search NOT test)"
    third_search_term_keyword = "field:keywords.en-US:(playwright search test NOT music)"
    search_term_content = "field:content.en-US:playwright search test the content"
    article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
        approve_first_revision=True,
        article_keyword=search_term_keyword.replace("field:keywords.en-US:", ""),
        article_content=search_term_content.replace("field:content.en-US:", "")
    )
    utilities.wait_for_given_timeout(65000)
    sumo_pages.top_navbar.click_on_sumo_nav_logo()
    with allure.step("Searching for an article using the keywords field operator"):
        sumo_pages.search_page.fill_into_searchbar(search_term_keyword)

        with allure.step("Verifying that the article is successfully returned after searching for"
                         " its keyword"):
            assert sumo_pages.search_page.is_a_particular_article_visible(
                article_details['article_title'])

    with allure.step("Searching for an article using the keywords field operator and the NOT "
                     "operator"):
        sumo_pages.search_page.fill_into_searchbar(second_search_term_keyword)

        with allure.step("Verifying that the test article is not returned when a keyword is placed"
                         " after the 'NOT' operator"):
            assert not sumo_pages.search_page.is_a_particular_article_visible(
                article_details['article_title'])

        sumo_pages.search_page.fill_into_searchbar(third_search_term_keyword)

        with allure.step("Verifying that the test article is returned when a non-keyword term is"
                         " used after the NOT operator"):
            assert sumo_pages.search_page.is_a_particular_article_visible(
                article_details['article_title'])

    with allure.step("Searching for an article using the content field operator"):
        sumo_pages.search_page.fill_into_searchbar(search_term_content)
        with allure.step("Verifying that the test article is successfully displayed"):
            assert sumo_pages.search_page.is_a_particular_article_visible(
                article_details['article_title']
            )
        with allure.step("Verifying that the search term is successfully highlighted in search"
                         " results"):
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title
                )
                assert _verify_search_results(page, search_term_content, 'english', title,
                                              content)


# C1352401
@pytest.mark.searchTests
def test_search_firefox_internal_pages(page: Page):
    sumo_pages = SumoPages(page)
    search_term = "field:content.en-US:about:config"

    with (allure.step("Searching for an internal firefox about page inside the content field")):
        sumo_pages.search_page.fill_into_searchbar(search_term)

        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            with allure.step("Verifying that the internal firefox page is returned in search"
                             " results content"):
                assert _verify_search_results(page, search_term, 'english', title,
                                              content), (f"{search_term} is found in search result"
                                                         f" with title: {title} and bolded "
                                                         f"content: {content}")


# C1358442, C1358445, C1358443, C1358444, C1358446
@pytest.mark.searchTests
def test_field_operators_for_non_us_locales(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(permissions=["review_revision"])

    utilities.start_existing_session(cookies=test_user)
    article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
        approve_first_revision=True
    )

    ro_article_info = sumo_pages.submit_kb_translation_flow._add_article_translation(
        approve_translation_revision=True,
        title=(article_details['article_title'] + "Articol de test " + utilities.
               generate_random_number(1, 100)),
        keyword="Keyword pentru articolul de test " + utilities.generate_random_number(1, 100),
        body="Continutul articolului de test " + utilities.generate_random_number(1, 100),
        summary="Sumarul articolului de test " + utilities.generate_random_number(1, 100),
        locale='ro'
    )

    utilities.navigate_to_link(article_details['article_url'])
    ja_article_info = sumo_pages.submit_kb_translation_flow._add_article_translation(
        approve_translation_revision=True,
        title=(article_details['article_title'] + " アカウント " + utilities.
               generate_random_number(1, 100)),
        keyword="アカウ " + utilities.generate_random_number(1, 100),
        body="アンカンウ " + utilities.generate_random_number(1, 100),
        summary="ンンンン " + utilities.generate_random_number(1, 100),
        locale='ja'
    )

    utilities.wait_for_given_timeout(65000)
    sumo_pages.top_navbar.click_on_sumo_nav_logo()

    with allure.step("Switching the locale to ro"):
        sumo_pages.footer_section.switch_to_a_locale('ro')
        utilities.wait_for_given_timeout(2000)

    with allure.step("Searching for the ro article using the title field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:title.ro:" + ro_article_info['translation_title'])

    with allure.step("Verifying that the ro article is successfully returned"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ro_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the content field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:content.ro:" + ro_article_info['translation_body'])

    with allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ro_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the summary field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:summary.ro:" + ro_article_info['translation_summary']
        )

    with allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ro_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the slug field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            " field:slug.ro:" + ro_article_info['translation_slug']
        )

    with allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ro_article_info['translation_title']
        )

    with allure.step("Switching the locale to ja"):
        sumo_pages.footer_section.switch_to_a_locale('ja')

    with allure.step("Searching for the ja article using the title field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:title.ja:" + ja_article_info['translation_title'])

    with allure.step("Verifying that the ja article is successfully returned"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ja_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the content field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:content.ja:" + ja_article_info['translation_body'])

    with allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ja_article_info['translation_title']
        )

    with allure.step("Searching for the ja article using the summary field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:summary.ja:" + ja_article_info['translation_summary']
        )

    with allure.step("Verifying that the ja article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ja_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the slug field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            " field:slug.ja:" + ja_article_info['translation_slug']
        )

    with allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ja_article_info['translation_title']
        )


# C1358447
@pytest.mark.searchTests
def test_doc_id_field_operator(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Performing a GET request against the /api/1/kb endpoint and saving the "
                     "first returned kb article information"):
        kb_list = utilities.get_api_response(page, f"{HomepageMessages.STAGE_HOMEPAGE_URL}"
                                                   f"/api/1/kb")
        first_kb_result = kb_list.json()['results'][0]
        kb_result_dict = {
            "kb_title": first_kb_result["title"],
            "kb_slug": first_kb_result["slug"]
        }

    with allure.step("Performing a GET request against the /api/1/kb/{first article slug} and "
                     "fetching the document_id"):
        document_info = utilities.get_api_response(page, f"{HomepageMessages.STAGE_HOMEPAGE_URL}"
                                                         f"/api/1/kb/{kb_result_dict['kb_slug']}")
        document_id = document_info.json()['id']

    with allure.step("Searching for the doc_id field operator inside the main searchbar"):
        sumo_pages.search_page.fill_into_searchbar(f"field:doc_id.en-US:{document_id}")

    with allure.step("Verifying that the correct article is returned"):
        sumo_pages.search_page.is_a_particular_article_visible(kb_result_dict['kb_title'])


# C1329240
@pytest.mark.searchTests
def test_obsolete_marked_documents_visibility(page: Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    utilities.start_existing_session(cookies=test_user)

    with allure.step("Submitting a new KB article"):
        test_article = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)
        utilities.wait_for_given_timeout(65000)

    with allure.step("Verifying that the article is successfully returned"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar(test_article["article_title"])
        assert (test_article["article_title"] in sumo_pages.search_page.
                get_all_search_results_article_titles())

    with allure.step("Marking the question as obsolete"):
        utilities.navigate_to_link(test_article["article_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(obsolete=True)
        utilities.wait_for_given_timeout(65000)

    with allure.step("Verifying that the article is no longer returned"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar(test_article["article_title"])
        assert (test_article["article_title"] not in sumo_pages.search_page.
                get_all_search_results_article_titles())

    with allure.step("Unmarking the question as obsolete"):
        utilities.navigate_to_link(test_article["article_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(obsolete=False)
        utilities.wait_for_given_timeout(65000)

    with allure.step("Verifying that the article is returned"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar(test_article["article_title"])
        assert (test_article["article_title"] in sumo_pages.search_page.
                get_all_search_results_article_titles())


#  C1329226
@pytest.mark.searchTests
def test_article_product_metadata_update_and_search_filter_by_product(page: Page,
                                                                      create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    utilities.start_existing_session(cookies=test_user)

    with allure.step("Submitting a new KB article"):
        test_article = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)
        utilities.wait_for_given_timeout(65000)

    with check, allure.step("Searching for the article and verifying that the article is returned "
                            "inside the search results if the filter is applied to"
                            " 'All Products'"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar(test_article["article_title"])
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"
        assert (test_article["article_title"] in sumo_pages.search_page.
                get_all_search_results_article_titles())

    with check, allure.step("Clicking on the 'Firefox' filter and verifying that the article"
                            "is displayed inside the search results"):
        sumo_pages.search_page.click_on_a_particular_side_nav_item("Firefox")
        utilities.wait_for_given_timeout(2000)
        assert (test_article["article_title"] in sumo_pages.search_page.
                get_all_search_results_article_titles())

    with check, allure.step("Clicking on the 'Firefox for Android' filter and verifying that the"
                            "article is not displayed inside the search results"):
        sumo_pages.search_page.click_on_a_particular_side_nav_item("Firefox for Android")
        utilities.wait_for_given_timeout(2000)
        assert (test_article["article_title"] not in sumo_pages.search_page.
                get_all_search_results_article_titles())

    with allure.step("Editing the article by adding 'Firefox for Android' as a product"):
        utilities.navigate_to_link(test_article["article_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(product="Firefox for Android")
        utilities.wait_for_given_timeout(65000)

    with check, allure.step("Searching for the article and verifying that the article is returned "
                            "in both 'Firefox' and 'Firefox for Android' product filters"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar(test_article["article_title"])
        assert (test_article["article_title"] in sumo_pages.search_page.
                get_all_search_results_article_titles())

        sumo_pages.search_page.click_on_a_particular_side_nav_item("Firefox")
        utilities.wait_for_given_timeout(2000)
        assert (test_article["article_title"] in sumo_pages.search_page.
                get_all_search_results_article_titles())

        sumo_pages.search_page.click_on_a_particular_side_nav_item("Firefox for Android")
        utilities.wait_for_given_timeout(2000)
        assert (test_article["article_title"] in sumo_pages.search_page.
                get_all_search_results_article_titles())

    with allure.step("Searching for the article by filtering against a different product and "
                     "verifying that the article is not displayed"):
        sumo_pages.search_page.click_on_a_particular_side_nav_item("Thunderbird")
        utilities.wait_for_given_timeout(2000)
        assert (test_article["article_title"] not in sumo_pages.search_page.
                get_all_search_results_article_titles())


# C2873849
@pytest.mark.searchTests
def test_archived_questions_are_returned_advanced_search_results_only(page: Page,
                                                                      create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Posting a Firefox product question"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])

        question_details = sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body=utilities.aaq_question_test_data["valid_firefox_question"]
            ["simple_body_text"],
            attach_image=False,
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Leaving a question reply so that the question is returned in search "
                     "results"):
        question_reply = (
            utilities.aaq_question_test_data['valid_firefox_question']['question_reply'])
        sumo_pages.aaq_flow.post_question_reply_flow( repliant_username=test_user['username'],
                                                      reply=question_reply)
        utilities.start_existing_session(session_file_name=user)
        sumo_pages.question_page.click_on_archive_this_question_option()

    with allure.step("Waiting for 1 minute so that the question is successfully returned in "
                     "search results"):
        utilities.wait_for_given_timeout(65000)

    with allure.step("Searching for the question inside the searchbar"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar(question_details["aaq_subject"])
        assert (question_details["aaq_subject"] not in sumo_pages.search_page.
                get_all_search_results_article_titles())

    with allure.step("Searching for the question inside the searchbar using advanced search"
                     "syntax"):
        sumo_pages.search_page.clear_the_searchbar()
        sumo_pages.search_page.fill_into_searchbar(
            f"field:question_title.en-US:{question_details['aaq_subject']}")
        assert (question_details["aaq_subject"] in sumo_pages.search_page.
                get_all_search_results_article_titles())

        sumo_pages.search_page.clear_the_searchbar()
        sumo_pages.search_page.fill_into_searchbar(
            f"field:question_content.en-US:{question_details['question_body']}")
        utilities.wait_for_given_timeout(2000)

        while sumo_pages.common_web_elements.is_next_pagination_item_visible():
            search_titles = sumo_pages.search_page.get_all_search_results_article_titles()
            if question_details['aaq_subject'] in search_titles:
                assert True
                break

            sumo_pages.common_web_elements.click_on_next_pagination_item()
            utilities.wait_for_given_timeout(2000)
        search_titles = sumo_pages.search_page.get_all_search_results_article_titles()
        assert question_details['aaq_subject'] in search_titles


#  C2874873, C2873851, C1358450
@pytest.mark.searchTests
def test_aaq_question_id_and_is_archived_fields_search(page:Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Searching archived questions using the question_is_archived:true and "
                            "verifying that the returned search results are only archived "
                            "questions"):
        sumo_pages.search_page.fill_into_searchbar("field:question_is_archived:true")
        sumo_pages.search_page.click_on_help_articles_only_doctype_filter()
        utilities.wait_for_given_timeout(2000)

        assert not sumo_pages.search_page.is_search_content_section_displayed()
        assert (SearchPageMessage.EMPTY_SEARCH_RESULTS_MESSAGE == sumo_pages.
                search_page.get_no_search_results_message())

    with check, allure.step("Clicking on the 'Community Discussions Only' doctype filter and "
                            "verifying that the returned search results are archived questions"):
        sumo_pages.search_page.click_on_community_discussions_only_doctype_filter()
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        assert sumo_pages.question_page.get_thread_locked_text(
        ) == QuestionPageMessages.ARCHIVED_THREAD_BANNER

    with check, allure.step("Navigating back and searching for the question_is_archived:false"
                            "and verifying that the returned search results are only unarchived "
                            "questions"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar("field:question_is_archived:false")
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        if sumo_pages.question_page.is_thread_locked_banner_displayed():
            assert sumo_pages.question_page.get_thread_locked_text() not in (
                [QuestionPageMessages.LOCKED_AND_ARCHIVED_BANNER,
                 QuestionPageMessages.ARCHIVED_THREAD_BANNER]
            )
        else:
            assert True

    question_id = utilities.number_extraction_from_string_endpoint("/questions/",
                                                                   utilities.get_page_url())
    question_title = sumo_pages.question_page.get_question_header()

    with check, allure.step("Navigating back and searching for the question_id and verifying that "
                            "the correct question is returned"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar(f"field:question_id:{question_id}")
        assert [question_title] == sumo_pages.search_page.get_all_search_results_article_titles()


# C2874062
@pytest.mark.searchTests
def test_aaq_question_is_locked_field_search(page:Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Searching for question_is_locked:false inside the searchobx and "
                            "verifying that the returned questions are locked"):
        sumo_pages.search_page.fill_into_searchbar("field:question_is_locked:false")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        print(sumo_pages.question_page.get_thread_locked_text())
        if sumo_pages.question_page.is_thread_locked_banner_displayed():
            assert sumo_pages.question_page.get_thread_locked_text() not in (
                [QuestionPageMessages.LOCKED_AND_ARCHIVED_BANNER,
                 QuestionPageMessages.LOCKED_THREAD_BANNER]
            )
        else:
            assert True

    with allure.step("Searching for question_is_locked:true inside the searchobx and verifying"
                     " that the returned questions are not locked"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar("field:question_is_locked:true")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        assert sumo_pages.question_page.get_thread_locked_text() in (
            [QuestionPageMessages.LOCKED_AND_ARCHIVED_BANNER,
             QuestionPageMessages.LOCKED_THREAD_BANNER])


# C2874061, C1358448, C1358449
@pytest.mark.searchTests
def test_aaq_question_has_solution_field_search(page:Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Searching for question_has_solution:false inside the searchobx and "
                            "verifying that the returned questions don't have a solution"):
        sumo_pages.search_page.fill_into_searchbar("field:question_has_solution:false")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        assert not sumo_pages.question_page.is_solution_section_displayed()

    with allure.step("Searching for question_has_solution:true inside the searchobx and verifying"
                     " that the returned questions have a solution"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar("field:question_has_solution:true")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        assert sumo_pages.question_page.is_solution_section_displayed()


# C2874874
@pytest.mark.searchTests
def test_aaq_question_product_id_field_search(page:Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Searching for question_product id 1 inside the searchobx and "
                            "verifying that the returned questions are filled under the Firefox"
                            "product"):
        sumo_pages.search_page.fill_into_searchbar("field:question_product_id:1")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        sumo_pages.question_page.click_on_question_details_button()
        assert sumo_pages.question_page.get_question_details_product() == "Firefox"

    with allure.step("Searching for question_product id 2 inside the searchobx and verifying"
                     " that the returned questions are filled under the Firefox for Android"
                     " product"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar("field:question_product_id:2")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        sumo_pages.question_page.click_on_question_details_button()
        assert sumo_pages.question_page.get_question_details_product() == "Firefox for Android"


# C2874875
@pytest.mark.searchTests
def test_aaq_question_topic_id_field_search(page:Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Searching for question_topic 383 inside the searchobx and "
                            "verifying that returned questions are filled against the"
                            " Accessibility topic"):
        sumo_pages.search_page.fill_into_searchbar("field:question_topic_id:383")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        sumo_pages.question_page.click_on_question_details_button()
        assert sumo_pages.question_page.get_question_details_topic() == "Accessibility"

    with allure.step("Searching for question_topic 410 inside the searchobx and verifying"
                     " that the returned questions are filled against the Accounts topic"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar("field:question_topic_id:410")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        sumo_pages.question_page.click_on_question_details_button()
        assert sumo_pages.question_page.get_question_details_topic() == "Accounts"


# C2874878
@pytest.mark.searchTests
def test_aaq_question_tag_id_field_search(page:Page, create_user_factory):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    utilities.start_existing_session(cookies=test_user)

    with check, allure.step("Searching for question_tag_id 2272 inside the searchobx and "
                            "verifying that the returned questions contain the accessibility tag"):
        sumo_pages.search_page.fill_into_searchbar("field:question_tag_ids:2772")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        sumo_pages.question_page.click_on_question_details_button()
        assert "accessibility" in sumo_pages.question_page.get_question_tag_options(True)

    with allure.step("Searching for question_tag_id 2273 inside the searchobx and verifying"
                     " that the returned questions contain the firefox tag"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar("field:question_tag_ids:2773")
        utilities.wait_for_given_timeout(2000)
        results = sumo_pages.search_page.get_all_search_results_handles()
        random.choice(results).click()
        sumo_pages.question_page.click_on_question_details_button()
        assert "firefox" in sumo_pages.question_page.get_question_tag_options(True)


# C1358452
@pytest.mark.searchTests
def test_aaq_question_votes_field_search(page:Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with check, allure.step("Searching for question_num_votes:0 and verifying that the search"
                            " results contain the queried number of question votes"):
        sumo_pages.search_page.fill_into_searchbar("field:question_num_votes:0")
        utilities.wait_for_given_timeout(2000)
        assert all("0" in search_result for search_result in sumo_pages.search_page.
                   get_text_of_question_votes())

    with allure.step("Searching for question_num_votes:3 inside the searchobx and verifying"
                     " that the returned questions contain the queried number of votes"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        sumo_pages.search_page.fill_into_searchbar("field:question_num_votes:3")
        utilities.wait_for_given_timeout(2000)
        assert all("3" in search_result for search_result in sumo_pages.
                   search_page.get_text_of_question_votes())


def _verify_search_results(page: Page, search_term: str, locale: str, search_result_title: str,
                           search_result_bolded_content: list[str], exact_phrase=False) -> bool:
    utilities = Utilities(page)
    in_title = utilities.search_result_check(search_result_title, search_term, locale,
                                             exact_phrase)
    in_content = False
    for content in search_result_bolded_content:
        if utilities.search_result_check(content, search_term, locale, exact_phrase):
            in_content = True
            break
    return in_title or in_content
