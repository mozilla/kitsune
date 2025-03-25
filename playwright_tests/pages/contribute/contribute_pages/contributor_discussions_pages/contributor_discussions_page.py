from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the general "Contributor Discussions" page.
"""


class ContributorDiscussionPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.contributor_discussions_page_title = page.locator("div#forums h1")

    def get_contributor_discussions_page_title(self) -> str:
        return super()._get_text_of_element(self.contributor_discussions_page_title)
