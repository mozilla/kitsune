from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the general "Contributor Discussions" page.
"""


class ContributorDiscussionPage(BasePage):
    __contributor_discussions_page_title = "//div[@id='forums']/h1"

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_contributor_discussions_page_title(self) -> str:
        return super()._get_text_of_element(self.__contributor_discussions_page_title)
