from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBArticlePage(BasePage):
    __kb_article_heading = "//h1[@class='sumo-page-heading']"

    # Editing Tools options
    __editing_tools_show_history_option = "//a[contains(text(), 'Show History')]"

    def __init__(self, page: Page):
        super().__init__(page)

    def get_text_of_article_title(self) -> str:
        return super()._get_text_of_element(self.__kb_article_heading)

    def click_on_show_history_option(self):
        super()._click(self.__editing_tools_show_history_option)
