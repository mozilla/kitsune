from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class KBArticlePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # General page locators.
        self.article_breadcrumb = lambda breadcrumb_name: page.locator(
            "ol#breadcrumbs").get_by_role("link", name=f"{breadcrumb_name}")
        self.kb_article_heading = page.locator("h1.sumo-page-heading")
        self.kb_article_breadcrumbs_list = page.locator("ol#breadcrumbs").get_by_role("link")
        self.kb_article_restricted_banner = page.locator("div.warning-box")
        self.kb_article_content = page.locator("section#doc-content")
        self.kb_article_content_approved_content = page.locator("section#doc-content p")
        self.kb_article_contributors = page.locator("div[class='document--contributors-list "
                                                    "text-body-xs'] a")
        self.kb_article_contributor = lambda username: page.locator(
            "div[class='document--contributors-list text-body-xs']").get_by_role(
            "link", name=f'{username}', exact=True)
        self.learn_more_kb_article_option = page.get_by_role("link", name="Learn More")

        # Editing Tools options locators.
        self.editing_tools_article_option = page.get_by_role("link", name="Article",
                                                             exact=True)
        self.editing_tools_edit_article_option = page.get_by_role("link", name="Edit Article",
                                                                  exact=True)
        self.editing_tools_edit_article_metadata_option = page.get_by_role(
            "link", name="Edit Article Metadata")
        self.editing_tools_translate_article = page.get_by_role(
            "link", name="Translate Article", exact=True)
        self.editing_tools_discussion_option = page.locator("ul.sidebar-nav--list").get_by_role(
            "link", name="Discussion", exact=True)
        self.editing_tools_show_translations = page.get_by_role(
            "link", name="Show Translations", exact=True)
        self.editing_tools_what_links_here = page.get_by_role("link", name="What Links Here",
                                                              exact=True)
        self.editing_tools_show_history_option = page.get_by_role("link", name="Show History",
                                                                  exact=True)

    # KB Article page content actions.
    def click_on_a_particular_breadcrumb(self, breadcrumb_name: str):
        self._click(self.article_breadcrumb(breadcrumb_name))

    def get_text_of_all_article_breadcrumbs(self) -> list[str]:
        return self._get_text_of_elements(self.kb_article_breadcrumbs_list)

    def get_text_of_article_title(self) -> str:
        return self._get_text_of_element(self.kb_article_heading)

    def get_restricted_visibility_banner_text(self) -> str:
        return self._get_text_of_element(self.kb_article_restricted_banner)

    def is_restricted_visibility_banner_text_displayed(self) -> bool:
        return self._is_element_visible(self.kb_article_restricted_banner)

    def get_list_of_kb_article_contributors(self) -> list[str]:
        return self._get_text_of_elements(self.kb_article_contributors)

    def click_on_a_particular_article_contributor(self, username: str):
        self._click(self.kb_article_contributor(username))

    def get_text_of_kb_article_content_approved(self) -> str:
        return self._get_text_of_element(self.kb_article_content_approved_content)

    def get_text_of_kb_article_content(self) -> str:
        return self._get_text_of_element(self.kb_article_content)

    def click_on_what_links_here_option(self):
        self._click(self.editing_tools_what_links_here)

    def get_what_links_here_locator(self):
        return self.editing_tools_what_links_here

    # KB Article editing tools section actions.
    def click_on_show_history_option(self):
        self._click(self.editing_tools_show_history_option)

    def get_show_history_option_locator(self):
        return self.editing_tools_show_history_option

    def click_on_edit_article_option(self):
        self._click(self.editing_tools_edit_article_option)

    def get_edit_article_option_locator(self):
        return self.editing_tools_edit_article_option

    def click_on_edit_article_metadata(self):
        self._click(self.editing_tools_edit_article_metadata_option)

    def get_edit_article_metadata_locator(self):
        return self.editing_tools_edit_article_metadata_option

    def click_on_translate_article_option(self):
        self._click(self.editing_tools_translate_article)

    def get_translate_article_option_locator(self):
        return self.editing_tools_translate_article

    def get_show_translations_option_locator(self):
        return self.editing_tools_show_translations

    def click_on_article_option(self):
        self._click(self.editing_tools_article_option)

    def get_article_option_locator(self) -> Locator:
        return self.editing_tools_article_option

    def editing_tools_discussion_locator(self) -> Locator:
        return self.editing_tools_discussion_option

    def click_on_editing_tools_discussion_option(self):
        self._click(self.editing_tools_discussion_option)

    def click_on_volunteer_learn_more_option(self):
        self._click(self.learn_more_kb_article_option)

    def get_url(self) -> str:
        return self._get_current_page_url()
