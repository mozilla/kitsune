import pytest

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.contribute_page_messages import ContributePageMessages
from selenium_tests.messages.homepage_messages import HomepageMessages


class TestHomepage(TestUtilities):
    @pytest.mark.smokeTest
    def test_join_our_community_card_learn_more_redirects_to_contribute_page(self):
        self.logger.info("Clicking on the 'Learn More' option")

        self.pages.homepage.click_learn_more_option()

        self.logger.info("Verifying that we are redirected to the 'Contribute' page successfully")

        assert self.pages.contribute_page.current_url == ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL, "We are not on the Contribute page!"

    @pytest.mark.smokeTest
    def test_join_our_community_card_has_the_correct_content(self):
        self.logger.info("Verifying that the 'Join Our Community' card has the correct strings applied")

        assert self.pages.homepage.get_community_card_title() == HomepageMessages.JOIN_OUR_COMMUNITY_CARD_TITLE and \
               self.pages.homepage.get_community_card_description() == HomepageMessages.JOIN_OUR_COMMUNITY_CARD_DESCRIPTION, "Incorrect strings are displayed"




