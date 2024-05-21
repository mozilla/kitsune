from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class KBArticlePage(BasePage):
    __kb_article_heading = "//h1[@class='sumo-page-heading']"
    __kb_article_breadcrumbs_list = "//ol[@id='breadcrumbs']//a"
    __kb_article_restricted_banner = "//div[contains(@class,'warning-box')]"
    __kb_article_content = "//section[@id='doc-content']"
    __kb_article_content_approved_content = "//section[@id='doc-content']/p"
    __kb_article_contributors = "//div[@class='document--contributors-list text-body-xs']/a"
    __learn_more_kb_article_option = "//a[text()='Learn More']"

    # Editing Tools options
    __editing_tools_article_option = "//a[text()='Article']"
    __editing_tools_edit_article_option = "//li/a[text()='Edit Article']"
    __editing_tools_edit_article_metadata_option = "//a[text()='Edit Article Metadata']"
    __editing_tools_translate_article = "//a[text()='Translate Article']"
    __editing_tools_discussion_option = "//ul[@class='sidebar-nav--list']//a[text()='Discussion']"
    __editing_tools_show_translations = "//a[text()='Show Translations']"
    __editing_tools_what_links_here = "//a[text()='What Links Here']"
    __editing_tools_show_history_option = "//a[contains(text(), 'Show History')]"

    def __init__(self, page: Page):
        super().__init__(page)

    # KB Article page content actions.
    def _click_on_a_particular_breadcrumb(self, breadcrumb_name: str):
        super()._click(f"//ol[@id='breadcrumbs']//a[text()='{breadcrumb_name}']")

    def _get_text_of_all_breadcrumbs(self) -> list[str]:
        return super()._get_text_of_elements(self.__kb_article_breadcrumbs_list)

    def _get_text_of_article_title(self) -> str:
        return super()._get_text_of_element(self.__kb_article_heading)

    def _get_restricted_visibility_banner_text(self) -> str:
        return super()._get_text_of_element(self.__kb_article_restricted_banner)

    def _is_restricted_visibility_banner_text_displayed(self) -> bool:
        return super()._is_element_visible(self.__kb_article_restricted_banner)

    def _get_list_of_kb_article_contributors(self) -> list[str]:
        return super()._get_text_of_elements(self.__kb_article_contributors)

    def _click_on_a_particular_article_contributor(self, username: str):
        super()._click(f"//div[@class='document--contributors-list text-body-xs']/"
                       f"a[text()='{username}']")

    def _get_text_of_kb_article_content_approved(self) -> str:
        return super()._get_text_of_element(self.__kb_article_content_approved_content)

    def _get_text_of_kb_article_content(self) -> str:
        return super()._get_text_of_element(self.__kb_article_content)

    def _click_on_what_links_here_option(self):
        super()._click(self.__editing_tools_what_links_here)

    def _get_what_links_here_locator(self):
        return super()._get_element_locator(self.__editing_tools_what_links_here)

    # KB Article editing tools section actions.
    def _click_on_show_history_option(self):
        super()._click(self.__editing_tools_show_history_option)

    def _get_show_history_option_locator(self):
        return super()._get_element_locator(self.__editing_tools_show_history_option)

    def _click_on_edit_article_option(self):
        super()._click(self.__editing_tools_edit_article_option)

    def _get_edit_article_option_locator(self):
        return super()._get_element_locator(self.__editing_tools_edit_article_option)

    def _click_on_edit_article_metadata(self):
        super()._click(self.__editing_tools_edit_article_metadata_option)

    def _get_edit_article_metadata_locator(self):
        return super()._get_element_locator(self.__editing_tools_edit_article_metadata_option)

    def _get_translate_article_option_locator(self):
        return super()._get_element_locator(self.__editing_tools_translate_article)

    def _get_show_translations_option_locator(self):
        return super()._get_element_locator(self.__editing_tools_show_translations)

    def _click_on_article_option(self):
        super()._click(self.__editing_tools_article_option)

    def _get_article_option_locator(self) -> Locator:
        return super()._get_element_locator(self.__editing_tools_article_option)

    def _editing_tools_discussion_locator(self) -> Locator:
        return super()._get_element_locator(self.__editing_tools_discussion_option)

    def _click_on_editing_tools_discussion_option(self):
        super()._click(self.__editing_tools_discussion_option)

    def _click_on_volunteer_learn_more_option(self):
        super()._click(self.__learn_more_kb_article_option)
