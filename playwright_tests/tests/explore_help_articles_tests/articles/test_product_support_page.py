import pytest_check as check
import pytest
from playwright.sync_api import expect
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.explore_help_articles.products_support_page_messages import (
    ProductSupportPageMessages)
from playwright_tests.messages.ask_a_question_messages.product_solutions_messages import (
    ProductSolutionsMessages)


class TestPostedQuestions(TestUtilities):

    # Causing some weird failures in GH runners. Need to investigate before re-enabling.

    # C890926, C890931, C2091563
    @pytest.mark.skip
    def test_product_support_page(self):
        self.logger.info("Navigating to products page via top-navbar")
        self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()

        self.logger.info("Clicking on all product cards")
        for card in self.sumo_pages.products_page._get_all_product_support_titles():
            if card in self.general_test_data['product_support']:
                self.sumo_pages.products_page._click_on_a_particular_product_support_card(card)

                self.logger.info("Verifying that the correct page header is displayed")
                check.equal(
                    self.sumo_pages.product_support_page._get_product_support_title_text(),
                    card + ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_TITLE
                )

                self.logger.info("Verifying that the correct topics header is displayed")
                check.equal(
                    self.sumo_pages.product_support_page._get_frequent_topics_title_text(),
                    ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_FREQUENT_TOPICS_TITLE
                )

                self.logger.info("Verifying that the correct topics subheader is displayed")
                check.equal(
                    self.sumo_pages.product_support_page._get_frequent_topics_subtitle_text(),
                    ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_FREQUENT_TOPICS_SUBTITLE
                )

                self.logger.info("Verifying that the correct still need help title is displayed")
                check.equal(
                    self.sumo_pages.product_support_page._get_still_need_help_widget_title(),
                    ProductSupportPageMessages.STILL_NEED_HELP_WIDGET_TITLE
                )

                if card in super().general_test_data['premium_products']:
                    self.logger.info(
                        "Verifying that the correct still need help content is displayed")
                    check.equal(
                        self.sumo_pages.product_support_page.
                        _get_still_need_help_widget_content(),
                        ProductSupportPageMessages.STILL_NEED_HELP_WIDGET_CONTENT_PREMIUM
                    )

                    self.logger.info("Verifying that the correct still need help button text is "
                                     "displayed")
                    check.equal(
                        self.sumo_pages.product_support_page
                        ._get_still_need_help_widget_button_text(),
                        ProductSupportPageMessages.STILL_NEED_HELP_WIDGET_BUTTON_TEXT_PREMIUM
                    )
                else:
                    self.logger.info("Verifying that the correct still need help content is "
                                     "displayed")
                    check.equal(
                        self.sumo_pages.product_support_page.
                        _get_still_need_help_widget_content(),
                        ProductSupportPageMessages.STILL_NEED_HELP_WIDGET_CONTENT_FREEMIUM
                    )

                    self.logger.info("Verifying that the correct still need help button text is "
                                     "displayed")
                    check.equal(
                        self.sumo_pages.product_support_page
                        ._get_still_need_help_widget_button_text(),
                        ProductSupportPageMessages.STILL_NEED_HELP_WIDGET_BUTTON_TEXT_FREEMIUM
                    )

                # Firefox Focus and Thunderbird don't have frequent articles section
                if card != "Firefox Focus" and card != "Thunderbird":
                    self.logger.info("Verifying the correct featured articles header is displayed")
                    check.equal(
                        self.sumo_pages.product_support_page._get_featured_articles_header_text(),
                        ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_FREQUENT_ARTICLES_TITLE
                    )

                self.logger.info("Verifying that the correct 'Join Our Community' section header "
                                 "is displayed")
                check.equal(
                    self.sumo_pages.product_support_page._get_join_our_community_header_text(),
                    ProductSupportPageMessages.JOIN_OUR_COMMUNITY_SECTION_HEADER
                )

                self.logger.info("Verifying that the correct 'Join Our Community section content "
                                 "is displayed'")
                check.equal(
                    self.sumo_pages.product_support_page._get_join_our_community_content_text(),
                    ProductSupportPageMessages.JOIN_OUR_COMMUNITY_SECTION_CONTENT
                )

                self.logger.info("Clicking on the 'Learn more' option from the 'Join Our "
                                 "Community' section")
                self.sumo_pages.product_support_page._click_join_our_community_learn_more_link()

                self.logger.info("Verify that we are redirected to the contribute messages page")
                expect(
                    self.page
                ).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)

                self.logger.info("Navigate back")
                self.navigate_back()

                self.logger.info("Clicking on the 'Home' breadcrumb")
                self.sumo_pages.product_support_page._click_on_product_support_home_breadcrumb()

                self.logger.info("Verifying that we are redirected to the homepage")
                expect(
                    self.page
                ).to_have_url(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US)

                self.logger.info("Navigating to products page via top-navbar")
                self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()

    # C890929
    @pytest.mark.skip
    def test_product_support_page_frequent_topics_redirect(self):
        self.logger.info("Navigating to products page via top-navbar")
        self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()

        self.logger.info("Clicking on all product cards")

        for card in self.sumo_pages.products_page._get_all_product_support_titles():
            if card in self.general_test_data['product_support']:
                self.sumo_pages.products_page._click_on_a_particular_product_support_card(card)

                self.logger.info("Verifying that the correct page header is displayed")
                check.equal(
                    self.sumo_pages.product_support_page._get_product_support_title_text(),
                    card + ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_TITLE
                )

                if self.sumo_pages.product_support_page._is_frequent_topics_section_displayed:
                    for topic in (self.sumo_pages.product_support_page.
                                  _get_all_frequent_topics_cards()):
                        (self.sumo_pages.product_support_page
                         ._click_on_a_particular_frequent_topic_card(topic))
                        check.equal(
                            self.sumo_pages.product_topics_page._get_page_title(),
                            topic,
                            f"Incorrect topic page title. "
                            f"Expected: {topic} "
                            f"Received: {self.sumo_pages.product_topics_page._get_page_title()}"
                        )
                        self.navigate_back()
                else:
                    self.logger.info(f"{card} has no frequent topics displayed!!!")

                self.navigate_back()

    @pytest.mark.skip
    def test_product_support_page_featured_articles_redirect(self):
        self.logger.info("Navigating to products page via top-navbar")
        self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()

        self.logger.info("Clicking on all product cards")

        for card in self.sumo_pages.products_page._get_all_product_support_titles():
            if card in self.general_test_data['product_support']:
                self.sumo_pages.products_page._click_on_a_particular_product_support_card(card)

                self.logger.info("Verifying that the correct page header is displayed")
                check.equal(
                    self.sumo_pages.product_support_page._get_product_support_title_text(),
                    card + ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_TITLE
                )

                if self.sumo_pages.product_support_page._is_featured_articles_section_displayed:
                    featured_article_cards_count = (self.sumo_pages.product_support_page
                                                    ._get_feature_articles_count())
                    count = 1
                    while count <= featured_article_cards_count:
                        featured_article_names = (self.sumo_pages.product_support_page.
                                                  _get_list_of_featured_articles_headers())
                        # Skipping check for now because the Firefox Monitor article redirects to
                        # a different one
                        if featured_article_names[count - 1] == "Firefox Monitor":
                            continue
                        (self.sumo_pages.product_support_page.
                            _click_on_a_particular_feature_article_card(
                                featured_article_names[count - 1]))

                        self.logger.info("Verifying the accessed article title is the correct one")
                        check.equal(
                            featured_article_names[count - 1],
                            self.sumo_pages.kb_article_page._get_text_of_article_title(),
                            f"Expected: {featured_article_names[count - 1]} "
                            f"Received:"
                            f" {self.sumo_pages.kb_article_page._get_text_of_article_title()}"
                        )
                        count += 1
                        self.navigate_back()
                else:
                    self.logger.info(f"{card} has no featured articles displayed!!!")

                self.navigate_back()

    # C890932
    @pytest.mark.skip
    def test_still_need_help_button_redirect(self):
        self.logger.info("Navigating to products page via top-navbar")
        self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()

        self.logger.info("Clicking on all product cards")

        for card in self.sumo_pages.products_page._get_all_product_support_titles():
            if card in self.general_test_data['product_support']:
                self.sumo_pages.products_page._click_on_a_particular_product_support_card(card)

                self.logger.info("Verifying that the correct page header is displayed")
                check.equal(
                    self.sumo_pages.product_support_page._get_product_support_title_text(),
                    card + ProductSupportPageMessages.PRODUCT_SUPPORT_PAGE_TITLE
                )

                self.sumo_pages.product_support_page._click_still_need_help_widget_button()

                self.logger.info("Verifying that we are redirected to the correct product "
                                 "solutions page")
                expect(
                    self.page
                ).to_have_url(
                    super().general_test_data['product_solutions'][card]
                )

                self.logger.info("Verifying that we are on the correct milestone")
                check.equal(
                    self.sumo_pages.product_solutions_page._get_current_milestone_text(),
                    ProductSolutionsMessages.CURRENT_MILESTONE_TEXT,
                    f"Incorrect current milestone displayed "
                    f"Expected: {ProductSolutionsMessages.CURRENT_MILESTONE_TEXT} "
                    f"Received: "
                    f"{self.sumo_pages.product_solutions_page._get_current_milestone_text()}"
                )

                self.logger.info("Navigating to products page via top-navbar")
                self.sumo_pages.top_navbar._click_on_explore_our_help_articles_option()
