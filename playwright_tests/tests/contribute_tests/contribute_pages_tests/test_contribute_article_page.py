import allure
import pytest
import requests
from pytest_check import check

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


class TestContributeArticlePage(TestUtilities):
    # C2165414
    @pytest.mark.contributePagesTests
    def test_contribute_article_page_text(self):
        with allure.step("Accessing the Contribute with help Article page"):
            self.navigate_to_link(
                ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
            )

        with check, allure.step("Verifying that the page header is successfully displayed and "
                                "contains the correct strings"):
            assert self.sumo_pages.ways_to_contribute_pages._get_hero_main_header_text(
            ) == ContributeHelpArticlesMessages.HERO_PAGE_TITLE

        with check, allure.step("Verifying that the h2 is successfully displayed and contains "
                                "the correct strings"):
            assert self.sumo_pages.ways_to_contribute_pages._get_hero_second_header(
            ) == ContributeHelpArticlesMessages.HERO_SECOND_TITLE

        with check, allure.step("Verifying tha the paragraph under h2 is successfully displayed "
                                "and contains the correct strings"):
            assert self.sumo_pages.ways_to_contribute_pages._get_hero_text(
            ) == ContributeHelpArticlesMessages.HERO_TEXT

        with check, allure.step("Verifying that the 'How you can contribute_messages' header is "
                                "successfully displayed and contains the correct strings"):
            assert self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_header_text(
            ) == ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_HEADER

        # Need to add a check for the logged in state as well.
        # Excluding option four from the list since we are using a different locator

        card_titles = [
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_ONE_SIGNED_OUT,
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_TWO,
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_THREE,
            ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_FIVE,
        ]

        with check, allure.step("Verifying that the 'How you can contribute_messages' cards are "
                                "successfully expected"):
            assert self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_link_options(
            ) == card_titles

        with check, allure.step("Signing up with a FxA contributor account and Verifying that "
                                "the step 4 option is successfully displayed and the text "
                                "contains the expected string"):
            # We need to add here the check for when the user is signed in with a contributor
            # account
            assert self.sumo_pages.ways_to_contribute_pages._get_how_to_contribute_option_four(
            ) == ContributeHelpArticlesMessages.HOW_TO_CONTRIBUTE_OPTION_FOUR

        with check, allure.step("Verifying that the first line from the fact text is "
                                "successfully displayed and contains the expected string"):
            assert self.sumo_pages.ways_to_contribute_pages._get_first_fact_text(
            ) == ContributeHelpArticlesMessages.FACT_FIRST_LINE

        with check, allure.step("Verifying that the second line from the fact section text is "
                                "successfully displayed and contains the expected string"):
            assert self.sumo_pages.ways_to_contribute_pages._get_second_fact_text(
            ) == ContributeHelpArticlesMessages.FACT_SECOND_LINE

        with check, allure.step("Verifying that the 'Other ways to contribute_messages' header "
                                "is successfully displayed and contains the expected string"):
            assert self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_header(
            ) == ContributeHelpArticlesMessages.OTHER_WAYS_TO_CONTRIBUTE_HEADER

        other_ways_to_contribute_card_titles = [
            ContributeHelpArticlesMessages.ANSWER_QUESTIONS_IN_SUPPORT_FORUM_TITLE,
            ContributeHelpArticlesMessages.LOCALIZE_CONTENT_CARD_TITLE,
            ContributeHelpArticlesMessages.PROVIDE_SUPPORT_ON_SOCIAL_CHANNELS_CARD_TITLE,
            ContributeHelpArticlesMessages.RESPOND_TO_MOBILE_STORE_REVIEWS_CARD_TITLE,
        ]

        with check, allure.step("Verifying that the 'Other ways to contribute_messages' are "
                                "successfully displayed and in the correct order"):
            assert self.sumo_pages.ways_to_contribute_pages._get_other_ways_to_contribute_cards(
            ) == other_ways_to_contribute_card_titles

    # C2165414
    @pytest.mark.contributePagesTests
    def test_contribute_article_page_images_are_not_broken(self):
        with allure.step("Accessing the Contribute with help Article page"):
            self.navigate_to_link(
                ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
            )

        for link in self.sumo_pages.ways_to_contribute_pages._get_all_page_image_links():
            image_link = link.get_attribute("src")
            response = requests.get(image_link, stream=True)
            with check, allure.step(f"Verifying that {image_link} is not broken"):
                assert response.status_code < 400

    # C2165415
    @pytest.mark.contributePagesTests
    def test_contribute_article_page_breadcrumbs(self):
        with allure.step("Accessing the Contribute Forum page"):
            self.navigate_to_link(
                ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
            )

        breadcrumbs = [
            ContributeHelpArticlesMessages.FIRST_BREADCRUMB,
            ContributeHelpArticlesMessages.SECOND_BREADCRUMB,
            ContributeHelpArticlesMessages.THIRD_BREADCRUMB,
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
    # C2165418
    @pytest.mark.contributePagesTests
    def test_contribute_article_other_ways_to_contribute_redirect_to_the_correct_page(self):
        with allure.step("Accessing the Contribute Forum page"):
            self.navigate_to_link(
                ContributeHelpArticlesMessages.STAGE_CONTRIBUTE_HELP_ARTICLES_PAGE_URL
            )

        ways_to_contribute_links = [
            ContributeForumMessages.STAGE_CONTRIBUTE_FORUM_PAGE_URL,
            ContributeLocalizationMessages.STAGE_CONTRIBUTE_LOCALIZATION_PAGE_URL,
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
            with check, allure.step(f"Verifying that the {ways_to_contribute_links[counter]} "
                                    f"redirects to the correct page"):
                assert ways_to_contribute_links[counter] == self.get_page_url()
            self.navigate_back()
            counter += 1
