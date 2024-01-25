import pytest
import pytest_check as check
import requests

from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.contribute_messages.con_pages.con_forum_messages import (
    ContributeForumMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_help_articles_messages import (
    ContributeHelpArticlesMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_localization_messages import (
    ContributeLocalizationMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_mobile_support_messages import (
    ContributeMobileSupportMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_social_support_messages import (
    ContributeSocialSupportMessages)
from playwright_tests.messages.homepage_messages import HomepageMessages


class TestContributeLocalizationPage(TestUtilities):
    # C2176356
    @pytest.mark.contributePagesTests
    def test_contribute_localization_page_text(self):
        self.logger.info("Accessing the Contribute localization page")
        self.navigate_to_link(
            ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL
        )

        self.logger.info(
            "Verifying that the Contribute localization page contains the correct strings"
        )
        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_hero_main_header_text(),
            ContributeLocalizationMessages.HERO_PAGE_TITLE,
            f"Actual {self.sumo_pages.ways_to_contribute_pages._get_hero_main_header_text()}"
            f"Expected: {ContributeLocalizationMessages.HERO_PAGE_TITLE}",
        )

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_hero_second_header(),
            ContributeLocalizationMessages.HERO_SECOND_TITLE,
            f"Text is: "
            f"{self.sumo_pages.ways_to_contribute_pages._get_hero_second_header()}"
            f"Expected: {ContributeLocalizationMessages.HERO_SECOND_TITLE}",
        )

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_hero_text(),
            ContributeLocalizationMessages.HERO_TEXT,
            f"Text is: {self.sumo_pages.ways_to_contribute_pages._get_hero_text()}"
            f"Expected: {ContributeLocalizationMessages.HERO_TEXT}",
        )

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_header_text(),
            ContributeLocalizationMessages.HOW_TO_CONTRIBUTE_HEADER,
            f"Text is: "
            f"{self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_header_text()}"
            f"Expected is: {ContributeLocalizationMessages.HOW_TO_CONTRIBUTE_HEADER}",
        )

        # Need to add a check for the logged in state as well.
        # Excluding option four from the list since we are using a different locator

        card_titles = [
            ContributeLocalizationMessages.HOW_TO_CONTRIBUTE_OPTION_ONE_SIGNED_OUT,
            ContributeLocalizationMessages.HOW_TO_CONTRIBUTE_OPTION_TWO,
            ContributeLocalizationMessages.HOW_TO_CONTRIBUTE_OPTION_THREE,
            ContributeLocalizationMessages.HOW_TO_CONTRIBUTE_OPTION_FIVE,
        ]

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_link_options_text(),
            card_titles,
            "How you can contribute_messages steps are incorrect!",
        )

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_option_four_text(),
            ContributeLocalizationMessages.HOW_TO_CONTRIBUTE_OPTION_FOUR,
            f"Text is: "
            f"{self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_option_four_text()}"
            f"Expected is: "
            f"{ContributeLocalizationMessages.HOW_TO_CONTRIBUTE_OPTION_FOUR}",
        )

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_first_fact_text(),
            ContributeLocalizationMessages.FACT_FIRST_LINE,
            f"Text is: {self.sumo_pages.ways_to_contribute_pages._get_first_fact_text()}"
            f"Expected is: {ContributeLocalizationMessages.FACT_FIRST_LINE}",
        )

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_second_fact_text(),
            ContributeLocalizationMessages.FACT_SECOND_LINE,
            f"Text is: {self.sumo_pages.ways_to_contribute_pages._get_second_fact_text()}"
            f"Expected is: {ContributeLocalizationMessages.FACT_SECOND_LINE}",
        )

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_header(),
            ContributeLocalizationMessages.OTHER_WAYS_TO_CONTRIBUTE_HEADER,
            f"Text is: "
            f"{self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_header()}"
            f"Expected is: "
            f"{ContributeLocalizationMessages.OTHER_WAYS_TO_CONTRIBUTE_HEADER}",
        )

        other_ways_to_contribute_card_titles = [
            ContributeLocalizationMessages.ANSWER_QUESTIONS_IN_SUPPORT_FORUM_TITLE,
            ContributeLocalizationMessages.WRITE_ARTICLES_CARD_TITLE,
            ContributeLocalizationMessages.PROVIDE_SUPPORT_ON_SOCIAL_CHANNELS_CARD_TITLE,
            ContributeLocalizationMessages.RESPOND_TO_MOBILE_STORE_REVIEWS_CARD_TITLE,
        ]

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_card_title(),
            other_ways_to_contribute_card_titles,
            "Other ways to contribute_messages card titles are not the correct ones!",
        )

    # C2176356
    @pytest.mark.contributePagesTests
    def test_contribute_localization_page_images_are_not_broken(self):
        self.logger.info("Accessing the Contribute localization page")
        self.navigate_to_link(
            ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL
        )

        self.logger.info("Verifying that the Contribute localization page images are not broken")
        for link in self.sumo_pages.ways_to_contribute_pages._get_all_page_image_links():
            image_link = link.get_attribute("src")
            response = requests.get(image_link, stream=True)
            check.is_true(response.status_code < 400, f"The {image_link} image is broken")

    # C2176357
    @pytest.mark.contributePagesTests
    def test_contribute_localization_page_breadcrumbs(self):
        self.logger.info("Accessing the Contribute localization page")
        self.navigate_to_link(
            ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL
        )

        self.logger.info("Verifying that the correct breadcrumbs are displayed")
        breadcrumbs = [
            ContributeLocalizationMessages.FIRST_BREADCRUMB,
            ContributeLocalizationMessages.SECOND_BREADCRUMB,
            ContributeLocalizationMessages.THIRD_BREADCRUMB,
        ]

        check.equal(
            self.sumo_pages.ways_to_contribute_pages._get_text_of_all_breadcrumbs(),
            breadcrumbs,
            f"Breadcrumbs are: "
            f"{self.sumo_pages.ways_to_contribute_pages._get_text_of_all_breadcrumbs()}"
            f"Expected: {breadcrumbs}",
        )

        counter = 1
        for breadcrumb in self.sumo_pages.ways_to_contribute_pages._get_interactable_breadcrumbs():
            breadcrumb_to_click = (
                self.sumo_pages.ways_to_contribute_pages._get_interactable_breadcrumbs()[counter]
            )
            self.sumo_pages.ways_to_contribute_pages._click_on_breadcrumb(breadcrumb_to_click)

            if counter == 1:
                self.logger.info(
                    "Verifying that the Contribute breadcrumb redirects to the Contribute page"
                )
                check.equal(
                    self.get_page_url(),
                    ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL,
                    f"Expected to be on {ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL}"
                    f"We are actual on {self.get_page_url()}",
                )
                self.navigate_forward()
                counter -= 1
            elif counter == 0:
                self.logger.info("Verifying that the Home breadcrumb redirects to the Homepage")
                check.equal(
                    self.get_page_url(),
                    HomepageMessages.STAGE_HOMEPAGE_URL_EN_US,
                    f"Expected to be on {HomepageMessages.STAGE_HOMEPAGE_URL_EN_US}"
                    f"We are actual on {self.get_page_url()}",
                )

    # Need to add tests for "How you can contribute_messages" section

    # C2176360
    @pytest.mark.contributePagesTests
    def test_contribute_localization_other_ways_to_contribute_redirect_to_the_correct_page(self):
        self.logger.info("Accessing the Contribute Forum page")
        self.navigate_to_link(
            ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL
        )

        self.logger.info(
            "Verifying that the 'other ways to contribute_messages' "
            "cards are redirecting to the correct SUMO page"
        )
        ways_to_contribute_links = [
            ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL,
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL,
            ContributeSocialSupportMessages.STAGE_CONTRIBUTE_SOCIAL_SUPPORT_PAGE_URL,
            ContributeMobileSupportMessages.STAGE_CONTRIBUTE_MOBILE_SUPPORT_PAGE_URL,
        ]

        counter = 0
        for (
            element
        ) in self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_card_list():
            card = (
                self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_card_list()[
                    counter
                ]
            )
            self.sumo_pages.ways_to_contribute_pages._click_on_other_way_to_contribute_card(card)
            check.equal(
                ways_to_contribute_links[counter],
                self.get_page_url(),
                f"Expected the following URL: {ways_to_contribute_links[counter]}"
                f"Received: {self.get_page_url()}",
            )
            self.navigate_back()
            counter += 1
