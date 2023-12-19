from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBArticlePage(BasePage):
    # KB article page content locators.
    __kb_article_heading = "//h1[@class='sumo-page-heading']"

    # Editing Tools options locators.
    __editing_tools_show_history_option = "//a[contains(text(), 'Show History')]"

    def __init__(self, page: Page):
        super().__init__(page)

    # KB Article page content actions.
    def get_text_of_article_title(self) -> str:
        return super()._get_text_of_element(self.__kb_article_heading)

    # KB Article editing tools section actions.
    def click_on_show_history_option(self):
        super()._click(self.__editing_tools_show_history_option)
