import time

import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check

from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C890369
@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_product_solutions_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "Test question - do not delete"

    with allure.step("Navigating to the Firefox product solutions page and using the searchbar to "
                     "search for a particular kb Article"):
        utilities.navigate_to_link(utilities.general_test_data['product_solutions']['Firefox'])
        sumo_pages.search_page.fill_into_searchbar(text=test_article_name, is_aaq=True)

    with check, allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.fill_into_searchbar(text=test_question_name, is_aaq=True)

    with check, allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"


@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_product_support_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "Test question - do not delete"

    with allure.step("Navigating to the Firefox product support page and using the searchbar to "
                     "search for a particular kb Article"):
        utilities.navigate_to_link(utilities.general_test_data['product_support']['Firefox'])
        sumo_pages.search_page.fill_into_searchbar(test_article_name)

    with check, allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.fill_into_searchbar(test_question_name)

    with check, allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"


@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_explore_by_topic_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "Test question - do not delete"

    with allure.step("Navigating to the 'Browse' explore by topic page and using the searchbar to "
                     "search for a particular kb Article"):
        utilities.navigate_to_link("https://support.allizom.org/en-US/topics/browse")
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with check, allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with check, allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"


# C891284
@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_product_community_forum_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "Test question - do not delete"

    with allure.step("Navigating to the Firefox community forum page and using the searchbar to "
                     "search for a particular kb Article"):
        utilities.navigate_to_link("https://support.allizom.org/en-US/questions/firefox")
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with check, allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with check, allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"


@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_browse_all_forum_threads_by_topic_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "Test question - do not delete"

    with allure.step("Navigating to the 'Settings' browse all forum threads by topic page and "
                     "using the searchbar to search for a particular kb Article"):
        utilities.navigate_to_link("https://support.allizom.org/en-US/questions/topic/settings")
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with check, allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with check, allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"


@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_on_aaq_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "Test question - do not delete"

    with allure.step("Submiting a new Firefox AAQ question and using the searchbar to search for "
                     "a particular kb Article"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        utilities.navigate_to_link(utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        sumo_pages.aaq_flow.submit_an_aaq_question(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_name=utilities.
            aaq_question_test_data["valid_firefox_question"]["topic_value"],
            body=utilities.
            aaq_question_test_data["valid_firefox_question"]["question_body"],
            expected_locator=sumo_pages.question_page.questions_header
        )
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with check, allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with check, allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"
    sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)

    with allure.step("Deleting the posted question"):
        sumo_pages.aaq_flow.deleting_question_flow()


# C890835
@pytest.mark.smokeTest
@pytest.mark.searchTests
def test_searchbar_functionality_on_article_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_article_name = "DoNotDelete"
    test_question_name = "Test question - do not delete"

    with allure.step("Submitting a new KB article agains the Firefox product and using the "
                     "searchbar to search for a particular kb Article"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page)
        sumo_pages.kb_article_page.click_on_article_option()

        utilities.wait_for_given_timeout(2000)
        sumo_pages.search_page.fill_into_searchbar(test_article_name, is_sidebar=True)

    with check, allure.step("Verifying that the article is successfully returned"):
        assert test_article_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"

    with allure.step("Using the searchbar to search for a particular question"):
        sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)
        sumo_pages.search_page.fill_into_searchbar(test_question_name, is_sidebar=True)

    with check, allure.step("Verifying that the question is successfully returned"):
        assert test_question_name in sumo_pages.search_page.get_all_search_results_article_titles()

    with check, allure.step("Verifying that the filter by product is applied to the correct "
                            "product"):
        assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "Firefox"
    sumo_pages.search_page.clear_the_searchbar(is_sidebar=True)

    with allure.step("Deleting the posted article"):
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C1329220
@pytest.mark.searchTests
def test_popular_searches_homepage(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Clicking on all popular searches for the homepage searchbar"):
        for popular_search in sumo_pages.search_page.get_list_of_popular_searches():
            sumo_pages.search_page.click_on_a_popular_search(popular_search)
            with check, allure.step("Verifying that the correct text is added inside the search "
                                    "field"):
                assert sumo_pages.search_page.get_text_of_searchbar_field() == popular_search

            with check, allure.step("Verifying that 'All products' is highlighted inside the "
                                    "side-navbar"):
                assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"
            with check, allure.step("Verifying that search results contain the correct keyword"):
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
                with check, allure.step("Verifying that the correct text was added inside the "
                                        "search field"):
                    assert sumo_pages.search_page.get_text_of_searchbar_field() == popular_search

                with check, allure.step("Verifying that the correct product is listed in the side "
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

    with check, allure.step("Adding a search term inside the search bar which contains a stopword:"
                            " 'oricând' and verifying that it does not impact the search result"):
        sumo_pages.search_page.fill_into_searchbar(search_term)

        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            assert _verify_search_results(page, search_term.replace('oricând', ''),
                                          'romanian', title, content)


# C1329222
@pytest.mark.searchTests
def test_synonyms(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ['addon', 'add-on', 'add', 'how to add bookmarks', 'how to add themes',
                    'pop-ups', 'popups', 'pop ups']
    with check, allure.step("Adding a search term and validating the search results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)

                assert _verify_search_results(page, search_term, 'english', title, content)


# C1329223
@pytest.mark.searchTests
def test_brand_synonyms(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ['mozilla', 'modzilla', 'mozzila', 'mozzilla', 'mozila', 'ios', 'ipad',
                    'iphone', 'ipod']
    with check, allure.step("Adding a search term inside the search bar and validating search "
                            "results"):
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

    with check, allure.step("Verifying that the searchbar is empty"):
        assert sumo_pages.search_page.get_text_of_searchbar_field() == ''

    with check, allure.step("Navigating forward and verifying that the previously added search "
                            "term is displayed inside the searchbar"):
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

    with check, allure.step("Verifying that the user was redirected to the homepage and that the "
                            "searchbar is empty"):
        assert utilities.get_page_url() == HomepageMessages.STAGE_HOMEPAGE_URL_EN_US
        assert sumo_pages.search_page.get_text_of_searchbar_field() == ''

    with check, allure.step("Navigating back and verifying that the searchbar contains the "
                            "previously used search term"):
        utilities.navigate_back()
        assert sumo_pages.search_page.get_text_of_searchbar_field() == search_term


# C1329239
@pytest.mark.searchTests
def test_searchbar_search_update(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ['Mozilla', 'Mozilla themes', 'install']

    with check, allure.step("Adding a search term inside the search bar and validating search "
                            "results"):
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
            with check, allure.step("Verifying that the search results are filtered by the "
                                    "correct product and the search term is present"):
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
    with check, allure.step("Adding a search term inside the search bar and validating search "
                            "results"):
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

    with check, allure.step("Adding a search term inside the search bar and validating search "
                            "results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)
                assert _verify_search_results(page, search_term, 'english', title, content)


# C1350860, C1349859, C1352396, C1352398
@pytest.mark.searchTests
def test_conjunctions_and_disjunction_operators(page: Page):
    sumo_pages = SumoPages(page)
    search_terms = ["add-ons AND cache", "clear AND add-ons AND cache"]

    with (check, allure.step("Adding a search term inside the search bar and validating search "
                             "results")):
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


# C1350861, C1349864, C1352398
@pytest.mark.searchTests
@pytest.mark.parametrize("locale", ['en-US', 'ro'])
def test_or_operator(page: Page, locale):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_term = "crash OR Mozilla"

    if locale != 'en-US':
        utilities.navigate_to_link(f"https://support.allizom.org/{locale}")

    with check, allure.step("Adding a search term which contains the 'OR' inside the search term"):
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

    with (check, allure.step("Adding a search term which contains the 'NOT' inside the search "
                             "term")):
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

    with (check, allure.step("Adding a search term which contains the quotes inside the search "
                             "term")):
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

        with check, allure.step("Adding a search term with invalid exact phrase searching syntax"):
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
def test_keywords_field_and_content_operator(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
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

        with check, allure.step("Verifying that the article is successfully returned after "
                                "searching for its keyword"):
            assert sumo_pages.search_page.is_a_particular_article_visible(
                article_details['article_title'])

    with allure.step("Searching for an article using the keywords field operator and the NOT "
                     "operator"):
        sumo_pages.search_page.fill_into_searchbar(second_search_term_keyword)

        with check, allure.step("Verifying that the test article is not returned when a keyword "
                                "is placed after the 'NOT' operator"):
            assert not sumo_pages.search_page.is_a_particular_article_visible(
                article_details['article_title'])

        sumo_pages.search_page.fill_into_searchbar(third_search_term_keyword)

        with check, allure.step("Verifying that the test article is returned when a non-keyword "
                                "term is used after the NOT operator"):
            assert sumo_pages.search_page.is_a_particular_article_visible(
                article_details['article_title'])

    with allure.step("Searching for an article using the content field operator"):
        sumo_pages.search_page.fill_into_searchbar(search_term_content)
        with check, allure.step("Verifying that the test article is successfully displayed"):
            assert sumo_pages.search_page.is_a_particular_article_visible(
                article_details['article_title']
            )
        with check, allure.step("Verifying that the search term is successfully highlighted in "
                                "search results"):
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title
                )
                assert _verify_search_results(page, search_term_content, 'english', title,
                                              content)

    utilities.navigate_to_link(article_details['article_url'])
    sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C1352401
@pytest.mark.searchTests
def test_search_firefox_internal_pages(page: Page):
    sumo_pages = SumoPages(page)
    search_term = "field:content.en-US:about:config"

    with (allure.step("Searching for an internal firefox about page inside the content field")):
        sumo_pages.search_page.fill_into_searchbar(search_term)

        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            with check, allure.step("Verifying that the internal firefox page is returned in"
                                    " search results content"):
                assert _verify_search_results(page, search_term, 'english', title,
                                              content), (f"{search_term} is found in search result"
                                                         f" with title: {title} and bolded "
                                                         f"content: {content}")


# C1358442, C1358445, C1358443, C1358444, C1358446
@pytest.mark.searchTests
def test_field_operators_for_non_us_locales(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
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

    with check, allure.step("Verifying that the ro article is successfully returned"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ro_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the content field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:content.ro:" + ro_article_info['translation_body'])

    with check, allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ro_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the summary field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:summary.ro:" + ro_article_info['translation_summary']
        )

    with check, allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ro_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the slug field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            " field:slug.ro:" + ro_article_info['translation_slug']
        )

    with check, allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ro_article_info['translation_title']
        )

    with allure.step("Switching the locale to ja"):
        sumo_pages.footer_section.switch_to_a_locale('ja')

    with allure.step("Searching for the ja article using the title field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:title.ja:" + ja_article_info['translation_title'])

    with check, allure.step("Verifying that the ja article is successfully returned"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ja_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the content field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:content.ja:" + ja_article_info['translation_body'])

    with check, allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ja_article_info['translation_title']
        )

    with allure.step("Searching for the ja article using the summary field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            "field:summary.ja:" + ja_article_info['translation_summary']
        )

    with check, allure.step("Verifying that the ja article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ja_article_info['translation_title']
        )

    with allure.step("Searching for the ro article using the slug field operator"):
        sumo_pages.search_page.fill_into_searchbar(
            " field:slug.ja:" + ja_article_info['translation_slug']
        )

    with check, allure.step("Verifying that the ro article is successfully displayed"):
        assert sumo_pages.search_page.is_a_particular_article_visible(
            ja_article_info['translation_title']
        )

    with allure.step("Deleting both articles"):
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


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
