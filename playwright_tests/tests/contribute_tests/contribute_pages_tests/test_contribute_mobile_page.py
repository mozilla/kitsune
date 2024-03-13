import allure
import pytest
from pytest_check import check
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


class TestContributeMobilePage(TestUtilities):
    #  C2176366
    @pytest.mark.contributePagesTests
    def test_contribute_mobile_page_text(self):
        with allure.step("Accessing the Contribute Mobile Store page"):
            self.navigate_to_link(
                ContributeMobileSupportMessages.STAGE_CONTRIBUTE_MOBILE_SUPPORT_PAGE_URL
            )

        with check, allure.step("Verifying that the Contribute Mobile Store page contains the "
                                "correct strings"):
            assert self.sumo_pages.ways_to_contribute_pages._get_hero_main_header_text(
            ) == ContributeMobileSupportMessages.HERO_PAGE_TITLE
            assert self.sumo_pages.ways_to_contribute_pages._get_hero_second_header(
            ) == ContributeMobileSupportMessages.HERO_SECOND_TITLE
            assert self.sumo_pages.ways_to_contribute_pages._get_hero_text(
            ) == ContributeMobileSupportMessages.HERO_TEXT
            assert self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_header_text(
            ) == ContributeMobileSupportMessages.HOW_TO_CONTRIBUTE_HEADER

            # Need to add a check for the logged in state as well.
            # Excluding option four from the list since we are using a different locator

            card_titles = [
                ContributeMobileSupportMessages.HOW_TO_CONTRIBUTE_OPTION_ONE_SIGNED_OUT,
                ContributeMobileSupportMessages.HOW_TO_CONTRIBUTE_OPTION_TWO,
                ContributeMobileSupportMessages.HOW_TO_CONTRIBUTE_OPTION_THREE,
                ContributeMobileSupportMessages.HOW_TO_CONTRIBUTE_OPTION_FIVE,
            ]
            assert self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_link_options(
            ) == card_titles
            assert self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_option_four(
            ) == ContributeMobileSupportMessages.HOW_TO_CONTRIBUTE_OPTION_FOUR
            assert self.sumo_pages.ways_to_contribute_pages._get_first_fact_text(
            ) == ContributeMobileSupportMessages.FACT_FIRST_LINE
            assert self.sumo_pages.ways_to_contribute_pages._get_second_fact_text(
            ) == ContributeMobileSupportMessages.FACT_SECOND_LINE
            assert self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_header(
            ) == ContributeMobileSupportMessages.OTHER_WAYS_TO_CONTRIBUTE_HEADER

            other_ways_to_contribute_card_titles = [
                ContributeMobileSupportMessages.ANSWER_QUESTIONS_IN_SUPPORT_FORUM_TITLE_CARD_TITLE,
                ContributeMobileSupportMessages.WRITE_HELP_ARTICLES_CARD_TITLE,
                ContributeMobileSupportMessages.LOCALIZE_CONTENT_CARD_TITLE,
                ContributeMobileSupportMessages.PROVIDE_SUPPORT_ON_SOCIAL_CHANNELS_CARD_TITLE,
            ]
            assert self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_cards(
            ) == other_ways_to_contribute_card_titles

    # C2176366
    @pytest.mark.contributePagesTests
    def test_contribute_mobile_page_images_are_not_broken(self):
        with allure.step("Accessing the Contribute Mobile store page"):
            self.navigate_to_link(
                ContributeMobileSupportMessages.STAGE_CONTRIBUTE_MOBILE_SUPPORT_PAGE_URL
            )

        for link in self.sumo_pages.ways_to_contribute_pages._get_all_page_image_links():
            image_link = link.get_attribute("src")
            response = requests.get(image_link, stream=True)
            with check, allure.step(f"Verifying that the {image_link} image is not broken"):
                assert response.status_code < 400

    # C2176367
    @pytest.mark.contributePagesTests
    def test_contribute_mobile_page_breadcrumbs(self):
        with allure.step("Accessing the Contribute Mobile Store page"):
            self.navigate_to_link(
                ContributeMobileSupportMessages.STAGE_CONTRIBUTE_MOBILE_SUPPORT_PAGE_URL
            )

        breadcrumbs = [
            ContributeMobileSupportMessages.FIRST_BREADCRUMB,
            ContributeMobileSupportMessages.SECOND_BREADCRUMB,
            ContributeMobileSupportMessages.THIRD_BREADCRUMB,
        ]

        with check, allure.step("Verifying that the correct breadcrumbs are displayed"):
            assert self.sumo_pages.ways_to_contribute_pages._get_text_of_all_breadcrumbs(
            ) == breadcrumbs

        counter = 1
        for breadcrumb in self.sumo_pages.ways_to_contribute_pages._get_interactable_breadcrumbs():
            breadcrumb_to_click = (
                self.sumo_pages.ways_to_contribute_pages._get_interactable_breadcrumbs()[counter]
            )
            self.sumo_pages.ways_to_contribute_pages._click_on_breadcrumb(breadcrumb_to_click)

            if counter == 1:
                with check, allure.step("Verifying that the Contribute breadcrumb redirects to "
                                        "the Contribute page"):
                    assert self.get_page_url() == ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL
                self.navigate_forward()
                counter -= 1
            elif counter == 0:
                with check, allure.step("Verifying that the Home breadcrumb redirects to the "
                                        "Homepage"):
                    assert self.get_page_url() == HomepageMessages.STAGE_HOMEPAGE_URL_EN_US

    # Need to add tests for "How you can contribute_messages" section

    # C2176370
    @pytest.mark.contributePagesTests
    def test_contribute_mobile_other_ways_to_contribute_redirect_to_the_correct_page(self):
        with allure.step("Accessing the Contribute Mobile Store page"):
            self.navigate_to_link(
                ContributeMobileSupportMessages.STAGE_CONTRIBUTE_MOBILE_SUPPORT_PAGE_URL
            )

        ways_to_contribute_links = [
            ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL,
            ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL,
            ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL,
            ContributeSocialSupportMessages.STAGE_CONTRIBUTE_SOCIAL_SUPPORT_PAGE_URL,
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
            with check, allure.step("Verifying that the 'other ways to contribute_messages' "
                                    "cards are redirecting to the correct SUMO page"):
                assert ways_to_contribute_links[counter] == self.get_page_url()
            self.navigate_back()
            counter += 1
