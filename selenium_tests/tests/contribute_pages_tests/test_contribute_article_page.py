import pytest
import requests
import pytest_check as check

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.contribute_pages_messages.contribute_forum_page_messages import (
    ContributeForumMessages,
)
from selenium_tests.messages.contribute_pages_messages.contribute_help_articles_page_messages import (
    ContributeHelpArticlesMessages,
)
from selenium_tests.messages.contribute_pages_messages.contribute_localization_page_messages import (
    ContributeLocalizationMessages,
)
from selenium_tests.messages.contribute_pages_messages.contribute_mobile_store_support_page_messages import (
    ContributeMobileStoreSupportMessages,
)
from selenium_tests.messages.contribute_pages_messages.contribute_page_messages import (
    ContributePageMessages,
)
from selenium_tests.messages.contribute_pages_messages.contribute_social_support_messages import (
    ContributeSocialSupportMessages,
)
from selenium_tests.messages.homepage_messages import HomepageMessages


class TestContributeArticlePage(TestUtilities):
    # C2176351
    @pytest.mark.smokeTest
    def test_contribute_article_page_text(self):
        self.logger.info("Accessing the Contribute Article page")
        self.pages.ways_to_contribute_pages.navigate_to(
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
        )

        self.logger.info("Verifying that the Contribute Article page contains the correct strings")

        check.equal(
            self.pages.ways_to_contribute_pages.get_hero_main_header_text(),
            ContributeHelpArticlesMessages.HERO_PAGE_TITLE,
            f"Text is: {self.pages.ways_to_contribute_pages.get_hero_main_header_text()}"
            f"Expected: {ContributeHelpArticlesMessages.HERO_PAGE_TITLE}",
        )

        check.equal(
            self.pages.ways_to_contribute_pages.get_hero_second_header_text(),
            ContributeHelpArticlesMessages.HERO_SECOND_TITLE,
            f"Text is: {self.pages.ways_to_contribute_pages.get_hero_second_header_text()}"
            f"Expected: {ContributeHelpArticlesMessages.HERO_PAGE_TITLE}",
        )

        check.equal(
            self.pages.ways_to_contribute_pages.get_hero_text(),
            ContributeHelpArticlesMessages.HERO_TEXT,
            f"Text is: {self.pages.ways_to_contribute_pages.get_hero_text()}"
            f"Expected: {ContributeHelpArticlesMessages.HERO_TEXT}",
        )

        check.equal(
            self.pages.ways_to_contribute_pages.get_how_to_contribute_header_text(),
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_HEADER,
            f"Text is: {self.pages.ways_to_contribute_pages.get_how_to_contribute_header_text()}"
            f"Expected is: {ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_HEADER}",
        )

        # Need to add a check for the logged in state as well.
        # Excluding option four from the list since we are using a different locator

        card_titles = [
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_ONE_SIGNED_OUT,
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_TWO,
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_THREE,
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_FIVE,
        ]

        check.equal(
            self.pages.ways_to_contribute_pages.get_how_to_contribute_link_options_text(),
            card_titles,
            "How you can contribute steps are incorrect!",
        )

        check.equal(
            self.pages.ways_to_contribute_pages.get_how_to_contribute_option_four_text(),
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_FOUR,
            f"Text is: {self.pages.ways_to_contribute_pages.get_how_to_contribute_option_four_text()}"
            f"Expected is: {ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_FOUR}",
        )

        check.equal(
            self.pages.ways_to_contribute_pages.get_first_fact_text(),
            ContributeHelpArticlesMessages.FACT_FIRST_LINE,
            f"Text is: {self.pages.ways_to_contribute_pages.get_first_fact_text()}"
            f"Expected is: {ContributeHelpArticlesMessages.FACT_FIRST_LINE}",
        )

        check.equal(
            self.pages.ways_to_contribute_pages.get_second_fact_text(),
            ContributeHelpArticlesMessages.FACT_SECOND_LINE,
            f"Text is: {self.pages.ways_to_contribute_pages.get_second_fact_text()}"
            f"Expected is: {ContributeHelpArticlesMessages.FACT_SECOND_LINE}",
        )

        check.equal(
            self.pages.ways_to_contribute_pages.get_other_ways_to_contribute_header_text(),
            ContributeHelpArticlesMessages.OTHER_WAYS_TO_CONTRIBUTE_HEADER,
            f"Text is: {self.pages.ways_to_contribute_pages.get_other_ways_to_contribute_header_text()}"
            f"Expected is: {ContributeHelpArticlesMessages.OTHER_WAYS_TO_CONTRIBUTE_HEADER}",
        )

        other_ways_to_contribute_card_titles = [
            ContributeHelpArticlesMessages.ANSWER_QUESTIONS_IN_SUPPORT_FORUM_TITLE,
            ContributeHelpArticlesMessages.LOCALIZE_CONTENT_CARD_TITLE,
            ContributeHelpArticlesMessages.PROVIDE_SUPPORT_ON_SOCIAL_CHANNELS_CARD_TITLE,
            ContributeHelpArticlesMessages.RESPOND_TO_MOBILE_STORE_REVIEWS_CARD_TITLE,
        ]

        check.equal(
            self.pages.ways_to_contribute_pages.get_other_ways_to_contribute_card_titles_text(),
            other_ways_to_contribute_card_titles,
            "Other ways to contribute card titles are not the correct ones!",
        )

    # C2176351
    @pytest.mark.smokeTest
    def test_contribute_article_page_images_are_not_broken(self):
        self.logger.info("Accessing the Contribute Article page")
        self.pages.ways_to_contribute_pages.navigate_to(
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
        )

        self.logger.info("Verifying that the Contribute Article page images are not broken")

        for link in self.pages.ways_to_contribute_pages.get_all_page_image_links():
            image_link = link.get_attribute("src")
            response = requests.get(image_link, stream=True)
            check.is_true(response.status_code < 400, f"The {image_link} image is broken")

    # C2176352
    @pytest.mark.smokeTest
    def test_contribute_article_page_breadcrumbs(self):
        self.logger.info("Accessing the Contribute Article page")
        self.pages.ways_to_contribute_pages.navigate_to(
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
        )

        self.logger.info("Verifying that the correct breadcrumbs are displayed")
        breadcrumbs = [
            ContributeHelpArticlesMessages.FIRST_BREADCRUMB,
            ContributeHelpArticlesMessages.SECOND_BREADCRUMB,
            ContributeHelpArticlesMessages.THIRD_BREADCRUMB,
        ]

        check.equal(
            self.pages.ways_to_contribute_pages.get_text_of_all_breadcrumbs(),
            breadcrumbs,
            f"Breadcrumbs are: {self.pages.ways_to_contribute_pages.get_text_of_all_breadcrumbs()}"
            f"Expected: {breadcrumbs}",
        )

        counter = 1
        for breadcrumb in self.pages.ways_to_contribute_pages.get_all_interactable_breadcrumbs():
            breadcrumb_to_click = (
                self.pages.ways_to_contribute_pages.get_all_interactable_breadcrumbs()[counter]
            )
            self.pages.ways_to_contribute_pages.click_on_breadcrumb(breadcrumb_to_click)

            if counter == 1:
                self.logger.info(
                    "Verifying that the Contribute breadcrumb redirects to the Contribute page"
                )
                check.equal(
                    self.pages.contribute_page.current_url,
                    ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL,
                    f"Expected to be on {ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL}"
                    f"We are actual on {self.pages.contribute_page.current_url}",
                )
                self.pages.contribute_page.navigate_forward()
                counter -= 1
            elif counter == 0:
                self.logger.info("Verifying that the Home breadcrumb redirects to the Homepage")
                check.equal(
                    self.pages.homepage.current_url,
                    HomepageMessages.STAGE_HOMEPAGE_URL,
                    f"Expected to be on {HomepageMessages.STAGE_HOMEPAGE_URL}"
                    f"We are actual on {self.pages.homepage.current_url}",
                )

    # Need to add tests for "How you can contribute" section

    # C2176355
    @pytest.mark.smokeTest
    def test_contribute_article_other_ways_to_contribute_redirect_to_the_correct_page(self):
        self.logger.info("Accessing the Contribute Article page")
        self.pages.ways_to_contribute_pages.navigate_to(
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
        )

        self.logger.info(
            "Verifying that the 'other ways to contribute' cards are redirecting to the correct SUMO page"
        )

        ways_to_contribute_links = [
            ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL,
            ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL,
            ContributeSocialSupportMessages.STAGE_CONTRIBUTE_SOCIAL_SUPPORT_PAGE_URL,
            ContributeMobileStoreSupportMessages.STAGE_CONTRIBUTE_MOBILE_SUPPORT_PAGE_URL,
        ]

        counter = 0
        for (
            element
        ) in self.pages.ways_to_contribute_pages.get_all_other_ways_to_contribute_card_list():
            card = (
                self.pages.ways_to_contribute_pages.get_all_other_ways_to_contribute_card_list()[
                    counter
                ]
            )
            self.pages.ways_to_contribute_pages.click_on_other_way_to_contribute_card(card)
            check.equal(
                ways_to_contribute_links[counter],
                self.pages.ways_to_contribute_pages.current_url,
                f"Expected the following URL: {ways_to_contribute_links[counter]}"
                f"Received: {self.pages.ways_to_contribute_pages.current_url}",
            )
            self.pages.contribute_page.navigate_back()
            counter += 1
