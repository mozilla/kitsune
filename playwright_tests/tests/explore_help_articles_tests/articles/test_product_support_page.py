import allure
import pytest
from pytest_check import check
from typing import Union
from playwright.sync_api import expect, Page, Locator
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.explore_help_articles.products_support_page_messages import (
    ProductSupportPageMessages)
from playwright_tests.messages.ask_a_question_messages.product_solutions_messages import (
    ProductSolutionsMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# C890926, C890931, C2091563
@pytest.mark.productSupportPage
def test_product_support_page_join_community_section(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Navigating to products page via top-navbar"):
        sumo_pages.top_navbar.click_on_explore_our_help_articles_view_all_option()

    with allure.step("Clicking on all product cards"):
        cards = sumo_pages.products_page.get_all_product_support_titles()
        cards.append("Guides")
        for card in cards:
            if card in utilities.general_test_data['product_support'] or card == "Guides":
                if card != "Guides":
                    sumo_pages.products_page.click_on_a_particular_product_support_card(card)
                else:
                    with allure.step("Signing in with an contributor account"):
                        utilities.start_existing_session(utilities.username_extraction_from_email(
                            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
                        ))

                    with allure.step("Navigating to the 'Contributors Support' product page"):
                        sumo_pages.top_navbar.click_on_guides_option()

                with check, allure.step("Verifying that the correct 'Join Our Community' "
                                        "section header is displayed"):
                    assert (sumo_pages.product_support_page.get_join_our_community_header_text()
                            ) == ProductSupportPageMessages.JOIN_OUR_COMMUNITY_SECTION_HEADER

                with check, allure.step("Verifying that the correct 'Join Our Community "
                                        "section content is displayed'"):
                    assert (sumo_pages.product_support_page.get_join_our_community_content_text()
                            ) == ProductSupportPageMessages.JOIN_OUR_COMMUNITY_SECTION_CONTENT

                with allure.step("Clicking on the 'Learn more' option from the 'Join Our "
                                 "Community' section"):
                    sumo_pages.product_support_page.click_join_our_community_learn_more_link()

                with allure.step("Verify that we are redirected to the contribute messages page"):
                    expect(page).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)

                with allure.step("Navigate back, clicking on the 'Home' breadcrumb and "
                                 "verifying that we are redirected to the homepage"):
                    utilities.navigate_back()
                    sumo_pages.product_support_page.click_on_product_support_home_breadcrumb()
                    expect(page).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

                with allure.step("Navigating to products page via top-navbar"):
                    sumo_pages.top_navbar.click_on_explore_our_help_articles_view_all_option()


# C890929, C891335, C891336
@pytest.mark.productSupportPage
def test_product_support_page_frequent_topics_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    with allure.step("Navigating to products page via top-navbar"):
        sumo_pages.top_navbar.click_on_explore_our_help_articles_view_all_option()

    with allure.step("Clicking on all product cards"):
        cards = sumo_pages.products_page.get_all_product_support_titles()
        cards.append("Guides")
        for card in cards:
            if card in utilities.general_test_data['product_support'] or card == "Guides":
                if card != "Guides":
                    sumo_pages.products_page.click_on_a_particular_product_support_card(card)
                else:
                    with allure.step("Signing in with an contributor account"):
                        utilities.start_existing_session(utilities.username_extraction_from_email(
                            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
                        ))

                    with allure.step("Navigating to the 'Contributors Support' product page"):
                        sumo_pages.top_navbar.click_on_guides_option()

                with check, allure.step("Verifying that the correct page header is displayed"):
                    if card == "Guides":
                        assert (sumo_pages.product_support_page.get_product_support_title_text()
                                ) == "Contributors" + (ProductSupportPageMessages.
                                                       PRODUCT_SUPPORT_PAGE_TITLE)
                    else:
                        assert (sumo_pages.product_support_page.get_product_support_title_text()
                                ) == card + ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_TITLE

                if sumo_pages.product_support_page.is_frequent_topics_section_displayed():
                    with check, allure.step("Verifying the correct topics header is displayed"):
                        assert (sumo_pages.product_support_page.get_frequent_topics_title_text()
                                ) == (ProductSupportPageMessages
                                      .PRODUCT_SUPPORT_PAGE_FREQUENT_TOPICS_TITLE)

                    with check, allure.step("Verifying that the correct topics subheader is "
                                            "displayed"):
                        assert sumo_pages.product_support_page.get_frequent_topics_subtitle_text(
                        ) == (ProductSupportPageMessages.
                              PRODUCT_SUPPORT_PAGE_FREQUENT_TOPICS_SUBTITLE)

                    assert _verify_card_redirect(
                        page, sumo_pages.product_support_page.get_all_frequent_topics_cards(),
                        is_topic=True
                    )
                else:
                    print(f"{card} has no frequent topics displayed!!!")
            with allure.step("Navigating back"):
                utilities.navigate_back()


#  T5696580, C891335, C891336
@pytest.mark.productSupportPage
def test_product_support_page_featured_articles_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Navigating to products page via top-navbar"):
        sumo_pages.top_navbar.click_on_explore_our_help_articles_view_all_option()

    with allure.step("Clicking on all product cards"):
        cards = sumo_pages.products_page.get_all_product_support_titles()
        cards.append("Guides")
        for card in cards:
            if card in utilities.general_test_data['product_support'] or card == "Guides":
                if card != "Guides":
                    sumo_pages.products_page.click_on_a_particular_product_support_card(card)
                else:
                    with allure.step("Signing in with an contributor account"):
                        utilities.start_existing_session(utilities.username_extraction_from_email(
                            utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
                        ))

                    with allure.step("Navigating to the 'Contributors Support' product page"):
                        sumo_pages.top_navbar.click_on_guides_option()

                with check, allure.step("Verifying that the correct page header is displayed"):
                    if card != "Guides":
                        assert (sumo_pages.product_support_page.get_product_support_title_text()
                                ) == card + ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_TITLE
                    else:
                        assert (sumo_pages.product_support_page.get_product_support_title_text()
                                ) == "Contributors" + (ProductSupportPageMessages.
                                                       PRODUCT_SUPPORT_PAGE_TITLE)

                if sumo_pages.product_support_page.is_featured_articles_section_displayed():
                    with check, allure.step("Verifying the correct featured articles header "
                                            "is displayed"):
                        assert (sumo_pages.product_support_page
                                .get_featured_articles_header_text()
                                ) == (ProductSupportPageMessages
                                      .PRODUCT_SUPPORT_PAGE_FREQUENT_ARTICLES_TITLE)
                    assert _verify_card_redirect(
                        page, (sumo_pages.product_support_page.get_feature_articles_count()),
                        is_article=True)
                else:
                    print(f"{card} has no featured articles displayed!!!")

            with allure.step("Navigating back"):
                utilities.navigate_back()


# C890932
@pytest.mark.productSupportPage
def test_still_need_help_button_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Navigating to products page via top-navbar"):
        sumo_pages.top_navbar.click_on_explore_our_help_articles_view_all_option()

    with allure.step("Clicking on all product cards"):
        cards = sumo_pages.products_page.get_all_product_support_titles()
        cards.append("Guides")
        for card in cards:
            if card in utilities.general_test_data['product_support'] or card == "Guides":
                if card != "Guides":
                    sumo_pages.products_page.click_on_a_particular_product_support_card(card)
                else:
                    continue  # to be removed once https://github.com/mozilla/sumo/issues/2006
                    # is fixed
                    # with allure.step("Signing in with an contributor account"):
                    #     utilities.start_existing_session(utilities.username_extraction_from_email
                    #     (
                    #         utilities.user_secrets_accounts["TEST_ACCOUNT_13"]
                    #     ))
                    #
                    # with allure.step("Navigating to the 'Contributors Support' product page"):
                    #     sumo_pages.top_navbar.click_on_guides_option()
                    #
                    # with allure.step("Verifying that the still need help CTA is no displayed"):
                    #     assert not (sumo_pages.product_support_page
                    #                 .is_still_need_help_widget_displayed())

                with check, allure.step("Verifying that the correct page header is displayed"):
                    assert (sumo_pages.product_support_page.get_product_support_title_text()
                            ) == card + ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_TITLE

                with check, allure.step("Verifying that the correct still need help title is "
                                        "displayed"):
                    assert (sumo_pages.product_support_page.get_still_need_help_widget_title()
                            ) == ProductSupportPageMessages.STILL_NEED_HELP_WIDGET_TITLE
                if card in utilities.general_test_data['premium_products']:
                    with check, allure.step("Verifying that the correct still need help "
                                            "content is displayed"):
                        assert (sumo_pages.product_support_page
                                .get_still_need_help_widget_content()
                                ) == (ProductSupportPageMessages
                                      .STILL_NEED_HELP_WIDGET_CONTENT_PREMIUM)

                    with check, allure.step("Verifying that the correct still need help "
                                            "button text is displayed"):
                        assert (sumo_pages.product_support_page
                                .get_still_need_help_widget_button_text()
                                ) == (ProductSupportPageMessages
                                      .STILL_NEED_HELP_WIDGET_BUTTON_TEXT_PREMIUM)
                    with allure.step("Clicking on the still need help widget button"):
                        sumo_pages.product_support_page.click_still_need_help_widget_button()
                else:
                    with check, allure.step("Verifying that the correct still need help "
                                            "content is displayed"):
                        assert (sumo_pages.product_support_page
                                .get_still_need_help_widget_content()
                                ) == (ProductSupportPageMessages
                                      .STILL_NEED_HELP_WIDGET_CONTENT_FREEMIUM)

                    with check, allure.step("Verifying that the correct still need help "
                                            "button text is displayed"):
                        assert (sumo_pages.product_support_page
                                .get_still_need_help_widget_button_text()
                                ) == (ProductSupportPageMessages
                                      .STILL_NEED_HELP_WIDGET_BUTTON_TEXT_FREEMIUM)

                    with allure.step("Clicking on the still need help widget button"):
                        sumo_pages.product_support_page.click_still_need_help_widget_button()

                with allure.step("Verifying that we are redirected to the correct product "
                                 "solutions page"):
                    expect(page).to_have_url(
                        utilities.general_test_data['product_solutions'][card]
                    )

                with check, allure.step("Verifying that we are on the correct milestone"):
                    assert sumo_pages.product_solutions_page.get_current_milestone_text(
                    ) == ProductSolutionsMessages.CURRENT_MILESTONE_TEXT

                with allure.step("Navigating to products page via top-navbar"):
                    sumo_pages.top_navbar.click_on_explore_our_help_articles_view_all_option()


def _verify_card_redirect(page: Page, cards: Union[int, list[Locator]], is_topic=False,
                          is_article=False) -> bool:
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    if is_topic:
        for card in cards:
            sumo_pages.product_support_page.click_on_a_particular_frequent_topic_card(card)
            if sumo_pages.product_topics_page.get_page_title() != card:
                return False
            utilities.navigate_back()
    if is_article:
        count = 1
        while count <= cards:
            featured_article_names = (sumo_pages.product_support_page.
                                      get_list_of_featured_articles_headers())
            sumo_pages.product_support_page.click_on_a_particular_feature_article_card(
                featured_article_names[count - 1])
            if featured_article_names[count - 1] != (sumo_pages.
                                                     kb_article_page.get_text_of_article_title()):
                return False
            count += 1
            utilities.navigate_back()
    return True
