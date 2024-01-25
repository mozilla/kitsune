import pytest
import pytest_check as check

from playwright.sync_api import expect, TimeoutError
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.aaq_widget import (
    AAQWidgetMessages)
from playwright_tests.messages.ask_a_question_messages.product_solutions_messages import (
    ProductSolutionsMessages)


class TestProductSolutionsPage(TestUtilities):

    # Currently fails due to https://github.com/mozilla/sumo/issues/1608
    #  C890370
    @pytest.mark.skip
    def test_featured_articles_redirect(self):
        self.logger.info("Accessing the contact support page via the top navbar Get Help > "
                         "Browse All products")
        self.sumo_pages.top_navbar._click_on_browse_all_products_option()

        self.logger.info("Clicking on all product cards")

        for card in self.sumo_pages.contact_support_page._get_all_product_card_titles():
            self.sumo_pages.contact_support_page._click_on_a_particular_card(card)

            check.equal(
                self.sumo_pages.product_solutions_page._get_product_solutions_heading(),
                card + ProductSolutionsMessages.PAGE_HEADER,
                f"Incorrect product solutions page displayed: "
                f"Expected: {card + ProductSolutionsMessages.PAGE_HEADER} "
                f"Actual:{self.sumo_pages.product_solutions_page._get_product_solutions_heading()}"
            )

            if self.sumo_pages.product_solutions_page._is_featured_article_section_displayed():
                for featured_article_card in (self.sumo_pages.product_solutions_page
                                              ._get_all_featured_articles_titles()):
                    self.sumo_pages.product_solutions_page._click_on_a_featured_article_card(
                        featured_article_card)
                    with self.page.context.expect_page() as tab:
                        feature_article_page = tab.value
                        print("Tab open")

                    article_text = (feature_article_page.
                                    locator("//h1[@class='sumo-page-heading']").inner_text())
                    check.equal(
                        article_text,
                        featured_article_card,
                        f"Incorrect article page title. "
                        f"Expected: {featured_article_card} "
                        f"Received: {article_text}"
                    )
                    feature_article_page.close()
            else:
                self.logger.info(f"{card} has no featured articles displayed!!!")

            self.navigate_back()

    #  C890375, C890379
    @pytest.mark.productSolutionsPage
    def test_popular_topics_redirect(self):
        self.logger.info("Accessing the contact support page via the top navbar Get Help > "
                         "Browse All products")
        self.sumo_pages.top_navbar._click_on_browse_all_products_option()

        self.logger.info("Clicking on all product cards")

        for card in self.sumo_pages.contact_support_page._get_all_product_card_titles():
            self.sumo_pages.contact_support_page._click_on_a_particular_card(card)

            check.equal(
                self.sumo_pages.product_solutions_page._get_product_solutions_heading(),
                card + ProductSolutionsMessages.PAGE_HEADER,
                f"Incorrect product solutions page displayed: "
                f"Expected: {card + ProductSolutionsMessages.PAGE_HEADER} "
                f"Actual:{self.sumo_pages.product_solutions_page._get_product_solutions_heading()}"
            )

            if self.sumo_pages.product_solutions_page._is_popular_topics_section_displayed:
                for topic in self.sumo_pages.product_solutions_page._get_popular_topics():
                    self.sumo_pages.product_solutions_page._click_on_a_popular_topic_card(topic)
                    try:
                        with self.page.context.expect_page() as tab:
                            feature_article_page = tab.value
                            print(f"Tab open for topic: {topic}")
                    except TimeoutError:
                        print("Trying to click on the popular topic again")
                        self.sumo_pages.product_solutions_page._click_on_a_popular_topic_card(
                            topic)
                        with self.page.context.expect_page() as tab:
                            feature_article_page = tab.value
                            print(f"Tab open for topic: {topic}")

                    popular_topic = (feature_article_page
                                     .locator("//h1[@class='topic-title sumo-page-heading']")
                                     .inner_text())
                    check.equal(
                        popular_topic,
                        topic,
                        f"Incorrect topic page title. "
                        f"Expected: {topic} "
                        f"Received: {popular_topic}"
                    )
                    feature_article_page.close()
            else:
                self.logger.info(f"{card} has no featured articles displayed!!!")

            self.navigate_back()

    # C890382
    @pytest.mark.productSolutionsPage
    def test_ask_now_widget_redirect(self):
        self.logger.info("Accessing the contact support page via the top navbar Get Help > "
                         "Browse All products")
        self.sumo_pages.top_navbar._click_on_browse_all_products_option()

        self.logger.info("Clicking on all product cards")

        for freemium_product in super().general_test_data["freemium_products"]:
            self.sumo_pages.contact_support_page._click_on_a_particular_card(freemium_product)

            self.logger.info("Verifying that the correct 'Still need help' subtext is displayed")
            check.equal(
                self.sumo_pages.product_solutions_page._get_aaq_subheading_text(),
                AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT,
                f"Incorrect AAQ widget displayed: "
                f"Expected: {AAQWidgetMessages.FREEMIUM_AAQ_SUBHEADING_TEXT_SIGNED_OUT} "
                f"Received: {self.sumo_pages.product_solutions_page._get_aaq_subheading_text()}"
            )

            self.logger.info("Verifying that the correct AAQ button text is displayed")
            check.equal(
                self.sumo_pages.product_solutions_page._get_aaq_widget_button_name(),
                AAQWidgetMessages.FREEMIUM_PRODUCTS_AAQ_WIDGET_BUTTON_TEXT,
                f"Incorrect AAQ button name. "
                f"Expected: {self.sumo_pages.product_solutions_page._get_aaq_widget_button_name()}"
                f" Actual: {AAQWidgetMessages.FREEMIUM_PRODUCTS_AAQ_WIDGET_BUTTON_TEXT}"
            )

            self.logger.info("Clicking on the AAQ button and verifying that the auth page is "
                             "displayed")
            self.sumo_pages.product_solutions_page._click_ask_now_button()

            self.logger.info("Signing in to SUMO")
            self.sumo_pages.auth_flow_page.sign_in_flow(
                username=super().user_special_chars,
                account_password=super().user_secrets_pass,
            )

            self.logger.info("Verifying that we are on the correct AAQ form page")

            expect(
                self.page
            ).to_have_url(super().aaq_question_test_data["products_aaq_url"][freemium_product],
                          timeout=30000)

            self.logger.info("Signing out")
            self.sumo_pages.top_navbar._click_on_sign_out_button()

            self.logger.info("Accessing the contact support page via the top navbar Get Help > "
                             "Browse All products")
            self.sumo_pages.top_navbar._click_on_browse_all_products_option()

    # C890382
    @pytest.mark.productSolutionsPage
    def test_contact_support_widget_redirect(self):
        self.logger.info("Accessing the contact support page via the top navbar Get Help > "
                         "Browse All products")
        self.sumo_pages.top_navbar._click_on_browse_all_products_option()

        self.logger.info("Clicking on all product cards")

        for premium_product in super().general_test_data["premium_products"]:
            self.sumo_pages.contact_support_page._click_on_a_particular_card(premium_product)

            self.logger.info("Verifying that the correct 'Still need help' subtext is displayed")
            check.equal(
                self.sumo_pages.product_solutions_page._get_aaq_subheading_text(),
                AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT,
                f"Incorrect AAQ widget displayed: "
                f"Expected: {AAQWidgetMessages.PREMIUM_AAQ_SUBHEADING_TEXT} "
                f"Received: {self.sumo_pages.product_solutions_page._get_aaq_subheading_text()}"
            )

            self.logger.info("Verifying that the correct AAQ button text is displayed")
            check.equal(
                self.sumo_pages.product_solutions_page._get_aaq_widget_button_name(),
                AAQWidgetMessages.PREMIUM_PRODUCTS_AAQ_WIDGET_BUTTON_TEXT,
                f"Incorrect AAQ button name. "
                f"Expected: {self.sumo_pages.product_solutions_page._get_aaq_widget_button_name()}"
                f" Actual: {AAQWidgetMessages.FREEMIUM_PRODUCTS_AAQ_WIDGET_BUTTON_TEXT}"
            )

            self.logger.info("Clicking on the AAQ button and verifying that the auth page is "
                             "displayed")
            self.sumo_pages.product_solutions_page._click_ask_now_button()

            self.logger.info("Signing in to SUMO")
            self.sumo_pages.auth_flow_page.sign_in_flow(
                username=super().user_special_chars,
                account_password=super().user_secrets_pass,
            )

            self.logger.info("Verifying that we are on the correct AAQ form page")

            expect(
                self.page
            ).to_have_url(super().aaq_question_test_data["products_aaq_url"][premium_product],
                          timeout=30000)

            self.logger.info("Signing out")
            self.sumo_pages.top_navbar._click_on_sign_out_button()

            self.logger.info("Accessing the contact support page via the top navbar Get Help > "
                             "Browse All products")
            self.sumo_pages.top_navbar._click_on_browse_all_products_option()
