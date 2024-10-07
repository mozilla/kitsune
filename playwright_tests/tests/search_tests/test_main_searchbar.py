import time

import allure
import pytest
from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages
from pytest_check import check


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
                utilities.wait_for_given_timeout(2000)
                assert sumo_pages.search_page.get_text_of_searchbar_field() == popular_search

            with check, allure.step("Verifying that 'All products' is highlighted inside the "
                                    "side-navbar"):
                assert sumo_pages.search_page.get_the_highlighted_side_nav_item() == "All Products"
            with check, allure.step("Verifying that search results contain the correct keyword"):
                if not sumo_pages.search_page.get_all_search_results_article_titles():
                    assert False, (f"Search results contains 0 results for the {popular_search} "
                                   f"search term")
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
                    utilities.wait_for_given_timeout(2000)
                    assert sumo_pages.search_page.get_text_of_searchbar_field() == popular_search

                with check, allure.step("Verifying that the correct product is listed in the side "
                                        "navbar"):
                    assert sumo_pages.search_page.get_the_highlighted_side_nav_item(
                    ) == product.strip()
                    if not sumo_pages.search_page.get_all_search_results_article_titles():
                        assert False, (f"Search results contains 0 results for the"
                                       f" {popular_search} search term on the {product}"
                                       f" product!")

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
        utilities.wait_for_given_timeout(2000)
        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            assert _verify_search_results(page, search_term.replace('oricând', ''),
                                          'romanian', title, content)


# C1329222
@pytest.mark.searchTests
def test_synonyms(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_terms = ['addon', 'add-on', 'add', 'how to add bookmarks', 'how to add themes',
                    'pop-ups', 'popups', 'pop ups']
    with check, allure.step("Adding a search term and validating the search results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            utilities.wait_for_given_timeout(2000)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)

                assert _verify_search_results(page, search_term, 'english', title, content)

            sumo_pages.search_page.clear_the_searchbar()


# C1329223
@pytest.mark.searchTests
def test_brand_synonyms(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_terms = ['mozilla', 'modzilla', 'mozzila', 'mozzilla', 'mozila', 'ios', 'ipad',
                    'iphone', 'ipod']
    with check, allure.step("Adding a search term inside the search bar and validating search "
                            "results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            utilities.wait_for_given_timeout(2000)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)

                assert _verify_search_results(page, search_term, 'english', title, content)
            sumo_pages.search_page.clear_the_searchbar()


#  C1329234
@pytest.mark.searchTests
def test_searchbar_content_during_navigation(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_term = 'test'

    with allure.step("Typing inside the searchbar and navigating back"):
        sumo_pages.search_page.fill_into_searchbar(search_term)
        utilities.wait_for_given_timeout(2000)
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
        utilities.wait_for_given_timeout(2000)
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
    utilities = Utilities(page)
    search_terms = ['Mozilla', 'Mozilla themes', 'install']

    with check, allure.step("Adding a search term inside the search bar and validating search "
                            "results"):
        for search_term in search_terms:
            sumo_pages.search_page.fill_into_searchbar(search_term)
            utilities.wait_for_given_timeout(3000)
            for title in sumo_pages.search_page.get_all_search_results_article_titles():
                content = sumo_pages.search_page.get_all_search_results_article_bolded_content(
                    title)
                assert _verify_search_results(page, search_term, 'english', title, content)
            sumo_pages.search_page.clear_the_searchbar()


# C1329243
@pytest.mark.searchTests
def test_search_from_products_page(page: Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    search_term = 'Mozilla'

    with allure.step("Clicking on each product card from the SUMO homepage"):
        card_titles = sumo_pages.homepage.get_text_of_product_card_titles()
        for product_card in card_titles:
            with check, allure.step("Verifying that the search results are filtered by the "
                                    "correct product and the search term is present"):
                sumo_pages.homepage.click_on_product_card_by_title(product_card)
                sumo_pages.search_page.clear_the_searchbar()
                sumo_pages.search_page.fill_into_searchbar(search_term)
                utilities.wait_for_given_timeout(2000)
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
    utilities = Utilities(page)
    search_term = "Firefox Focus"
    with check, allure.step("Adding a search term inside the search bar and validating search "
                            "results"):
        sumo_pages.search_page.fill_into_searchbar(search_term)
        sumo_pages.search_page.click_on_a_particular_side_nav_item('Firefox for Android')
        utilities.wait_for_given_timeout(2000)
        for title in sumo_pages.search_page.get_all_search_results_article_titles():
            content = sumo_pages.search_page.get_all_search_results_article_bolded_content(title)
            assert _verify_search_results(page, search_term, 'english', title, content)

        with allure.step("Switching the product filter to something that returns 0 results"):
            sumo_pages.search_page.click_on_a_particular_side_nav_item('Firefox Relay')
            time.sleep(2)
            assert not sumo_pages.search_page.is_search_content_section_displayed()


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
