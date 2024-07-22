import re
from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage

"""
    This class contains the locators and actions for the {x} discussions page.
"""


class DiscussionsPage(BasePage):
    __discussions_page_title = "//article[@id='threads']/h1"
    __contributor_discussions_side_nav_selected_option = ("//nav[@id='for-contributors-sidebar']//"
                                                          "a[@class='selected']")

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_contributor_discussions_page_title(self) -> str:
        return super()._get_text_of_element(self.__discussions_page_title)

    def _get_contributor_discussions_side_nav_selected_option(self) -> str:
        option = super()._get_text_of_element(
            self.__contributor_discussions_side_nav_selected_option)
        return re.sub(r'\s+', ' ', option).strip()
