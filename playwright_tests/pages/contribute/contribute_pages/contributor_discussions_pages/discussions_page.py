import re
from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the {x} discussions page.
"""


class DiscussionsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.discussions_page_title = page.locator("article#threads h1")
        self.contributor_discussions_side_nav_selected_option = page.locator(
            "nav#for-contributors-sidebar a.selected")

    def get_contributor_discussions_page_title(self) -> str:
        return super()._get_text_of_element(self.discussions_page_title)

    def get_contributor_discussions_side_nav_selected_option(self) -> str:
        option = super()._get_text_of_element(
            self.contributor_discussions_side_nav_selected_option)
        return re.sub(r'\s+', ' ', option).strip()
