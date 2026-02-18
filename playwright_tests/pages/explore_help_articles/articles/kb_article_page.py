from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBArticlePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """General locators belonging to the KB article page."""
        self.article_breadcrumb = lambda breadcrumb_name: page.locator(
            "ol#breadcrumbs").get_by_role("link", name=f"{breadcrumb_name}")
        self.kb_article_heading = page.locator("h1.sumo-page-heading")
        self.kb_article_breadcrumbs_list = page.locator("ol#breadcrumbs").get_by_role("link")
        self.kb_article_restricted_banner = page.locator("div.warning-box")
        self.kb_article_content = page.locator("section#doc-content")
        self.kb_article_content_image = lambda image_name: page.locator(
            f"//section[@id='doc-content']//img[@alt='{image_name}']")
        self.kb_article_content_approved_content = page.locator("section#doc-content p")
        self.kb_article_contributors = page.locator("div[class='document--contributors-list "
                                                    "text-body-xs'] a")
        self.kb_article_contributor = lambda username: page.locator(
            "div[class='document--contributors-list text-body-xs']").get_by_role(
            "link", name=f'{username}', exact=True)

        """Locators belonging to the article metadata."""
        self.kb_article_helpfulness_count = page.locator(
            "div#document_metadata span[class='helpful-count']")

        """Locators belonging to the editing tools options section."""
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

        """Locators belonging to the helpfulness widget section."""
        self.helpfulness_widget = page.locator("form[class='document-vote--form helpful']")
        self.helpful_button = page.locator("button[class='btn helpful-button']")
        self.unhelpful_button = page.locator("button[class='btn not-helpful-button']")
        self.helpfulness_option = lambda option: page.locator(f'//label[text()="{option}"]')
        self.comments_textarea_field = page.locator("//textarea[@name='comment']")
        self.helpfulness_widget_cancel_button = page.locator(
            "//div[@class='sumo-button-wrap align-full']/button[normalize-space(text())='Cancel']")
        self.helpfulness_widget_submit_button = page.locator(
            "//div[@class='sumo-button-wrap align-full']/button[normalize-space(text())='Submit']")
        self.survey_message = page.locator("div[class='survey-message']")

        """Locators belonging to the related articles section."""
        self.related_articles_section = page.locator("section#related-documents")
        self.related_article_cards = page.locator("section#related-documents h3.card--title a")
        self.related_article = lambda article_title: page.locator(
            f'//section[@id="related-documents"]//h3[@class="card--title"]/a[normalize-space('
            f'text())="{article_title}"]'
        )

    """Actions against the kb article page content locators."""
    def click_on_a_particular_breadcrumb(self, breadcrumb_name: str):
        self._click(self.article_breadcrumb(breadcrumb_name))

    def get_text_of_all_article_breadcrumbs(self) -> list[str]:
        return self._get_text_of_elements(self.kb_article_breadcrumbs_list)

    def get_text_of_kb_article_helpfulness_count_metadata(self) -> str:
        return self._get_text_of_element(self.kb_article_helpfulness_count)

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

    def is_article_content_image_displayed(self, image_title: str):
        return self._is_element_visible(self.kb_article_content_image(image_title))

    """Actions against the kb article editing tools section locators."""
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

    def click_on_editing_tools_discussion_option(self):
        self._click(self.editing_tools_discussion_option)

    def get_url(self) -> str:
        return self._get_current_page_url()

    """Actions against the helpfulness widget locators."""
    def is_helpfulness_widget_displayed(self) -> bool:
        return self._is_element_visible(self.helpfulness_widget)

    def wait_for_helpfulness_widget_to_be_hidden(self, timeout=7000):
        self._wait_for_locator_to_be_hidden(self.helpfulness_widget, timeout=timeout)

    def click_on_helpful_button(self):
        self._click(self.helpful_button)

    def click_on_unhelpful_button(self):
        self._click(self.unhelpful_button)

    def click_on_helpfulness_option(self, option: str):
        self._click(self.helpfulness_option(option))

    def fill_helpfulness_textarea_field(self, text: str):
        self._fill(self.comments_textarea_field, text)

    def click_on_helpfulness_cancel_button(self):
        self._click(self.helpfulness_widget_cancel_button)

    def click_on_helpfulness_submit_button(self):
        self._click(self.helpfulness_widget_submit_button)

    def get_survey_message_text(self) -> str:
        return self._get_text_of_element(self.survey_message)

    def is_related_articles_section_displayed(self) -> bool:
        return self._is_element_visible(self.related_articles_section)

    def get_list_of_related_articles(self) -> list[str]:
        return [article.strip() for article in self._get_text_of_elements(
            self.related_article_cards)]

    def click_on_related_article_card(self, article_title: str):
        self._click(self.related_article(article_title))
