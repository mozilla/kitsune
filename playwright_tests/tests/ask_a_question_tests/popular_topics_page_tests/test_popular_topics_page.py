import allure
import pytest
from pytest_check import check

from playwright.sync_api import TimeoutError, expect, Error
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.aaq_widget import (
    AAQWidgetMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)


class TestPopularTopicsPage(TestUtilities):

    # C890379
    @pytest.mark.productTopicsPage
    def test_popular_topics_navbar(self):
        with allure.step("Navigating to product topics pages"):
            for product_topic in super().general_test_data["product_topics"]:
                topic_url = super().general_test_data["product_topics"][product_topic]
                self.page.wait_for_timeout(400)
                self.navigate_to_link(topic_url)
                self.wait_for_url_to_be(topic_url)

                for option in self.sumo_pages.product_topics_page._get_navbar_links_text():
                    with allure.step(f"Clicking on {option} navbar option"):
                        option_url = (HomepageMessages.STAGE_HOMEPAGE_URL + self.sumo_pages.
                                      product_topics_page._get_navbar_option_link(option))
                        self.sumo_pages.product_topics_page._click_on_a_navbar_option(option)
                        try:
                            self.wait_for_url_to_be(option_url)
                        except (TimeoutError, Error):
                            self.logger.info("Failed click, retrying")
                            self.sumo_pages.product_topics_page._click_on_a_navbar_option(option)
                            self.wait_for_url_to_be(option_url)

                    with check, allure.step("Verifying that the correct option is displayed"):
                        assert self.sumo_pages.product_topics_page._get_page_title() == option

                    with check, allure.step("Verifying that the correct nav option is selected"):
                        assert self.sumo_pages.product_topics_page._get_selected_navbar_option(
                        ) == option

    #  C2428991
    @pytest.mark.productTopicsPage
    def test_learn_more_redirect(self):
        with allure.step("Navigating to product topics pages"):
            for product_topic in super().general_test_data["product_topics"]:
                topic_url = super().general_test_data["product_topics"][product_topic]
                self.navigate_to_link(topic_url)
                self.wait_for_url_to_be(topic_url)

                with allure.step("Clicking on the 'Learn More' button"):
                    self.sumo_pages.product_topics_page._click_on_learn_more_button()

                with allure.step("Verifying that the user is redirected to the contribute "
                                 "messages page"):
                    expect(
                        self.page
                    ).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)

    # C2188690
    @pytest.mark.productTopicsPage
    def test_aaq_redirect(self):
        with allure.step("Navigating to product topics pages"):
            count = 0
            for product_topic in super().general_test_data["product_topics"]:
                topic_url = super().general_test_data["product_topics"][product_topic]
                self.navigate_to_link(topic_url)
                self.wait_for_url_to_be(topic_url)

                self.logger.info("Verifying the subheading text")
                if product_topic in super().general_test_data["premium_products"]:
                    with check, allure.step(f"Verifying that the correct subheading page for "
                                            f"{product_topic} is displayed"):
                        assert self.sumo_pages.product_topics_page._get_aaq_subheading_text(
                        ) == AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT

                    with allure.step("Clicking on the AAQ button"):
                        self.sumo_pages.product_topics_page._click_on_aaq_button()

                    with allure.step("Signing in to SUMO and verifying that we are on the "
                                     "correct AAQ form page"):
                        if count == 0:
                            self.sumo_pages.auth_flow_page.sign_in_flow(
                                username=super().user_special_chars,
                                account_password=super().user_secrets_pass
                            )
                            count += 1
                        else:
                            self.sumo_pages.auth_flow_page.login_with_existing_session()
                        expect(
                            self.page
                        ).to_have_url(super(
                        ).aaq_question_test_data["products_aaq_url"][product_topic], timeout=30000)

                    with allure.step("Signing out from SUMO"):
                        self.sumo_pages.top_navbar._click_on_sign_out_button()

                else:
                    assert self.sumo_pages.product_topics_page._get_aaq_subheading_text(
                    ) == AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT

                    with allure.step("Clicking on the AAQ button and verifying that we are on "
                                     "the 'Get community support article'"):
                        self.sumo_pages.product_topics_page._click_on_aaq_button()
                        expect(
                            self.page
                        ).to_have_url(KBArticlePageMessages.GET_COMMUNITY_SUPPORT_ARTICLE_LINK)
