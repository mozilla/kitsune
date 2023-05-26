import pytest
import pytest_check as check
import requests

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.contribute_pages_messages.\
    contribute_forum_page_messages import (
        ContributeForumMessages,
    )
from selenium_tests.messages.contribute_pages_messages.\
    contribute_help_articles_page_messages import (
        ContributeHelpArticlesMessages,
    )
from selenium_tests.messages.contribute_pages_messages.\
    contribute_localization_page_messages import (
        ContributeLocalizationMessages,
    )
from selenium_tests.messages.contribute_pages_messages.\
    contribute_mobile_store_support_page_messages import (
        ContributeMobileStoreSupportMessages,
    )
from selenium_tests.messages.contribute_pages_messages.\
    contribute_page_messages import (
        ContributePageMessages,
    )
from selenium_tests.messages.contribute_pages_messages.\
    contribute_social_support_messages import (
        ContributeSocialSupportMessages,
    )
from selenium_tests.messages.homepage_messages import HomepageMessages


class TestContributePage(TestUtilities):
    # C2165413
    @pytest.mark.smokeTest
    def test_contribute_page_text(self):
        self.logger.info("Clicking on the Contribute top-navbar option")
        self.pages.top_navbar.click_on_contribute_top_navbar_option()

        self.logger.info("Verify that the contribute page contains the correct strings")

        check.equal(
            self.pages.contribute_page.get_page_hero_main_header_text(),
            ContributePageMessages.HERO_MAIN_PAGE_TITLE,
            f"Text is: {self.pages.contribute_page.get_page_hero_main_header_text()}"
            f"Expected: {ContributePageMessages.HERO_MAIN_PAGE_TITLE}",
        )

        check.equal(
            self.pages.contribute_page.get_page_hero_main_subtext(),
            ContributePageMessages.HERO_HELP_MILLION_OF_USERS_TEXT,
            f"Text is: {self.pages.contribute_page.get_page_hero_main_subtext()}"
            f"Expected: {ContributePageMessages.HERO_HELP_MILLION_OF_USERS_TEXT}",
        )

        check.equal(
            self.pages.contribute_page.get_page_hero_need_help_header_text(),
            ContributePageMessages.HERO_NEED_YOUR_HELP_TITLE,
            f"Text is: {self.pages.contribute_page.get_page_hero_need_help_header_text()}"
            f"Expected: {ContributePageMessages.HERO_NEED_YOUR_HELP_TITLE}",
        )

        check.equal(
            self.pages.contribute_page.get_page_hero_need_help_subtext(),
            ContributePageMessages.HERO_NEED_YOUR_HELP_PARAGRAPH,
            f"Text is: {self.pages.contribute_page.get_page_hero_need_help_subtext()}."
            f"Expected: {ContributePageMessages.HERO_NEED_YOUR_HELP_PARAGRAPH}",
        )

        check.equal(
            self.pages.contribute_page.get_way_to_contribute_header_text(),
            ContributePageMessages.PICK_A_WAY_TO_CONTRIBUTE_HEADER,
            f"Text is: {self.pages.contribute_page.get_way_to_contribute_header_text()}"
            f"Expected: {ContributePageMessages.PICK_A_WAY_TO_CONTRIBUTE_HEADER}",
        )

        card_titles = [
            ContributePageMessages.ANSWER_QUESTIONS_CARD_TITLE,
            ContributePageMessages.WRITE_ARTICLES_CARD_TITLE,
            ContributePageMessages.LOCALIZE_CONTENT_CARD_TITLE,
            ContributePageMessages.PROVIDE_SUPPORT_ON_SOCIAL_CHANNELS_CARD_TITLE,
            ContributePageMessages.RESPOND_TO_MOBILE_STORE_REVIEWS_CARD_TITLE,
        ]

        check.equal(
            card_titles,
            self.pages.contribute_page.get_way_to_contribute_card_titles_text(),
            "Pick a way to contribute card titles are not the correct ones",
        )

        check.equal(
            self.pages.contribute_page.get_about_us_header_text(),
            ContributePageMessages.ABOUT_US_HEADER,
            f"Text is: {self.pages.contribute_page.get_about_us_header_text()}"
            f"Expected: {ContributePageMessages.ABOUT_US_HEADER}",
        )

        check.equal(
            self.pages.contribute_page.get_about_us_subtext(),
            ContributePageMessages.ABOUT_US_CONTENT,
            f"Text is: {self.pages.contribute_page.get_about_us_subtext()}"
            f"Expected: {ContributePageMessages.ABOUT_US_CONTENT}",
        )

    # C2165413
    @pytest.mark.smokeTest
    def test_contribute_page_images_are_not_broken(self):
        self.logger.info("Clicking on the Contribute top-navbar option")

        self.pages.top_navbar.click_on_contribute_top_navbar_option()

        self.logger.info("Verifying that the Contribute page images are not broken")

        for link in self.pages.contribute_page.get_all_page_links():
            image_link = link.get_attribute("src")
            response = requests.get(image_link, stream=True)
            check.is_true(response.status_code < 400, f"The {image_link} image is broken")

    # C1949333
    @pytest.mark.smokeTest
    def test_contribute_page_breadcrumbs(self):
        self.logger.info("Clicking on the Contribute top-navbar option")

        self.pages.top_navbar.click_on_contribute_top_navbar_option()

        self.logger.info("Verifying that the correct breadcrumbs are displayed")

        breadcrumbs = [
            ContributePageMessages.FIRST_BREADCRUMB,
            ContributePageMessages.SECOND_BREADCRUMB,
        ]

        check.equal(
            self.pages.contribute_page.get_breadcrumbs_text(),
            breadcrumbs,
            f"Breadcrumbs are: {self.pages.contribute_page.get_breadcrumbs_text()}"
            f"Expected to be: {breadcrumbs}",
        )

        self.logger.info("Verifying that the home breadcrumb redirects to the homepage")

        self.pages.contribute_page.click_on_home_breadcrumb()

        assert self.pages.homepage.current_url == HomepageMessages.STAGE_HOMEPAGE_URL, (
            f"{HomepageMessages.STAGE_HOMEPAGE_URL} page was expected to be displayed"
            f"{self.pages.homepage.current_url} is displayed instead"
        )

    # C1949335,C1949336,C1949337,C1949338,C1949339,C1949355
    @pytest.mark.smokeTest
    def test_way_to_contribute_redirects_to_correct_page(self):
        self.logger.info("Clicking on the Contribute top-navbar option")

        self.pages.top_navbar.click_on_contribute_top_navbar_option()

        self.logger.info(
            "Verifying that the 'way to contribute' cards are redirecting to the correct SUMO page"
        )

        ways_to_contribute_links = [
            ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL,
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL,
            ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL,
            ContributeSocialSupportMessages.STAGE_CONTRIBUTE_SOCIAL_SUPPORT_PAGE_URL,
            ContributeMobileStoreSupportMessages.STAGE_CONTRIBUTE_MOBILE_SUPPORT_PAGE_URL,
        ]
        counter = 0
        for element in self.pages.contribute_page.get_list_of_contribute_cards():
            card = self.pages.contribute_page.get_list_of_contribute_cards()[counter]
            self.pages.contribute_page.click_on_way_to_contribute_card(card)
            check.equal(
                ways_to_contribute_links[counter],
                self.pages.contribute_page.current_url,
                f"Expected the following URL: {ways_to_contribute_links[counter]}"
                f"Received: {self.pages.contribute_page.current_url}",
            )
            self.pages.contribute_page.navigate_back()
            counter += 1
