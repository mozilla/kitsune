import pytest
import pytest_check as check

from playwright.sync_api import TimeoutError, expect, Error
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.AAQ_messages.aaq_widget import AAQWidgetMessages
from playwright_tests.messages.contribute_pages_messages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.kb_article.kb_article_page_messages import KBArticlePageMessages


class TestPopularTopicsPage(TestUtilities):

    # C890379
    @pytest.mark.productTopicsPage
    def test_popular_topics_navbar(self):
        self.logger.info("Navigating to product topics pages")
        for product_topic in super().general_test_data["product_topics"]:
            topic_url = super().general_test_data["product_topics"][product_topic]
            self.page.wait_for_timeout(400)
            self.navigate_to_link(topic_url)
            self.wait_for_url_to_be(topic_url)

            for option in self.sumo_pages.product_topics_page._get_navbar_links_text():
                self.logger.info(f"Clicking on {option} navbar option")
                option_url = (HomepageMessages.STAGE_HOMEPAGE_URL + self.sumo_pages.
                              product_topics_page._get_navbar_option_link(option))
                self.sumo_pages.product_topics_page._click_on_a_navbar_option(option)
                try:
                    self.wait_for_url_to_be(option_url)
                except (TimeoutError, Error):
                    self.logger.info("Failed click, retrying")
                    self.sumo_pages.product_topics_page._click_on_a_navbar_option(option)
                    self.wait_for_url_to_be(option_url)

                self.logger.info("Verifying that the correct option is displayed")
                check.equal(
                    self.sumo_pages.product_topics_page._get_page_title(),
                    option,
                    f"Incorrect topic: "
                    f"Expected: {option} "
                    f"Received: {self.sumo_pages.product_topics_page._get_page_title()}"
                )

                self.logger.info("Verifying that the correct navbar option is selected")
                check.equal(
                    self.sumo_pages.product_topics_page._get_selected_navbar_option(),
                    option,
                    f"Incorrect selected navbar option "
                    f"Expected: {option} "
                    f"Actual: {self.sumo_pages.product_topics_page._get_selected_navbar_option()}"
                )

    #  C2428991
    @pytest.mark.productTopicsPage
    def test_learn_more_redirect(self):
        self.logger.info("Navigating to product topics pages")
        for product_topic in super().general_test_data["product_topics"]:
            topic_url = super().general_test_data["product_topics"][product_topic]
            self.navigate_to_link(topic_url)
            self.wait_for_url_to_be(topic_url)

            self.logger.info("Clicking on the 'Learn More' button")
            self.sumo_pages.product_topics_page._click_on_learn_more_button()

            self.logger.info("Verifying that we are redirected to the contribute page")
            expect(
                self.page
            ).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)

    # C2188690
    @pytest.mark.productTopicsPage
    def test_aaq_redirect(self):
        self.logger.info("Navigating to product topics pages")
        sign_in_with_the_same_account = False
        for product_topic in super().general_test_data["product_topics"]:
            topic_url = super().general_test_data["product_topics"][product_topic]
            self.navigate_to_link(topic_url)
            self.wait_for_url_to_be(topic_url)

            self.logger.info("Verifying the subheading text")
            if product_topic in super().general_test_data["premium_products"]:
                check.equal(
                    self.sumo_pages.product_topics_page._get_aaq_subheading_text(),
                    AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT,
                    f"Incorrect aaq subheading "
                    f"Expected: {AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT} "
                    f"Received: {self.sumo_pages.product_topics_page._get_aaq_subheading_text()}"
                )
                self.logger.info("Clicking on the AAQ button")
                self.sumo_pages.product_topics_page._click_on_aaq_button()

                self.logger.info("Signing in to SUMO")
                self.sumo_pages.auth_flow_page.sign_in_flow(
                    username=super().user_special_chars,
                    account_password=super().user_secrets_pass,
                    sign_in_with_same_account=sign_in_with_the_same_account,
                )

                self.logger.info("Verifying that we are on the correct AAQ form page")

                expect(
                    self.page
                ).to_have_url(super().aaq_question_test_data["products_aaq_url"][product_topic])

                self.logger.info("Signing out")
                self.sumo_pages.top_navbar.click_on_sign_out_button()

                sign_in_with_the_same_account = True
            else:
                check.equal(
                    self.sumo_pages.product_topics_page._get_aaq_subheading_text(),
                    AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT,
                    f"Incorrect aaq subheading "
                    f"Expected: {AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT} "
                    f"Received: {self.sumo_pages.product_topics_page._get_aaq_subheading_text()}"
                )
                self.logger.info("Clicking on the AAQ button")
                self.sumo_pages.product_topics_page._click_on_aaq_button()

                self.logger.info("Verifying that we are on the 'Get community support article'")
                expect(
                    self.page
                ).to_have_url(KBArticlePageMessages.GET_COMMUNITY_SUPPORT_ARTICLE_LINK)
