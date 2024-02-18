from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class KBArticlePage(BasePage):
    __kb_article_heading = "//h1[@class='sumo-page-heading']"
    __kb_article_content = "//section[@id='doc-content']"
    __kb_article_content_approved_content = "//section[@id='doc-content']/p"
    __kb_article_contributors = "//div[@class='document--contributors-list text-body-xs']/a"

    # Editing Tools options
    __editing_tools_article_option = "//a[text()='Article']"
    __editing_tools_edit_article_option = "//li/a[text()='Edit Article']"
    __editing_tools_edit_article_metadata_option = "//a[text()='Edit Article Metadata']"
    __editing_tools_discussion_option = "//ul[@class='sidebar-nav--list']//a[text()='Discussion']"
    __editing_tools_show_history_option = "//a[contains(text(), 'Show History')]"

    def __init__(self, page: Page):
        super().__init__(page)

    # KB Article page content actions.
    def _get_text_of_article_title(self) -> str:
        return super()._get_text_of_element(self.__kb_article_heading)

    def _get_list_of_kb_article_contributors(self) -> list[str]:
        return super()._get_text_of_elements(self.__kb_article_contributors)

    def _click_on_a_particular_article_contributor(self, username: str):
        xpath = f"//div[@class='document--contributors-list text-body-xs']/a[text()='{username}']"
        super()._click(xpath)

    def _get_text_of_kb_article_content_approved(self) -> str:
        return super()._get_text_of_element(self.__kb_article_content_approved_content)

    def _get_text_of_kb_article_content(self) -> str:
        return super()._get_text_of_element(self.__kb_article_content)

    # KB Article editing tools section actions.
    def _click_on_show_history_option(self):
        super()._click(self.__editing_tools_show_history_option)

    def _click_on_edit_article_option(self):
        super()._click(self.__editing_tools_edit_article_option)

    def _click_on_edit_article_metadata(self):
        super()._click(self.__editing_tools_edit_article_metadata_option)

    def _click_on_article_option(self):
        super()._click(self.__editing_tools_article_option)

    def _editing_tools_discussion_locator(self) -> Locator:
        return super()._get_element_locator(self.__editing_tools_discussion_option)

    def _click_on_editing_tools_discussion_option(self):
        super()._click(self.__editing_tools_discussion_option)
