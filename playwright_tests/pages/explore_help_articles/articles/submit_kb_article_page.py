from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class SubmitKBArticlePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.kb_article_for_contributors_sidebar = page.locator("nav#for-contributors-sidebar")

        """Locators belonging to the new kb article form."""
        self.kb_article_knowledge_bases_field = page.locator("input#id_audiences-ts-control")
        self.kb_article_form_title = page.locator("input#id_title")
        self.kb_article_form_slug = page.locator("input#id_slug")
        self.kb_article_category_select = page.locator("select#id_category")
        self.kb_article_is_localizable_checkbox = page.locator("input#id_is_localizable")
        self.kb_article_allow_discussions_on_article = page.locator(
            "label[for='id_allow_discussion']")
        self.kb_article_allow_translations = page.locator("label[for='id_is_localizable']")
        self.kb_article_search_for_related_documents = page.locator("search-related-ts-control")
        self.kb_article_keyword_input = page.locator("input#id_keywords")
        self.kb_article_search_result_summary_textarea = page.locator("textarea#id_summary")

        """Locators belonging to the new kb article content form locators."""
        self.kb_article_content_textarea = page.locator("textarea#id_content")
        self.kb_article_insert_media = page.locator("button[class*='btn-media']")
        self.kb_article_insert_media_modal_images = page.locator("div#media-modal img")
        self.kb_article_insert_media_modal_insert_button = page.get_by_role(
            "button").filter(has_text="Insert Image")
        self.kb_article_toggle_syntax_highlighting = page.locator(
            "//div[@id='editor_wrapper']/following-sibling::a"
        )
        self.kb_article_expiry_date = page.locator("input#id_expires")
        self.kb_article_preview_content_button = page.locator(
            "div[class*='submit'] button[class*='btn-preview']")
        self.kb_article_preview_image = page.locator("div#doc-content img")
        self.kb_article_submit_for_preview_button = page.locator(
            "div[class*='submit'] button[class*='submit']")
        self.kb_article_preview_content = page.locator("div#doc-content")
        self.kb_article_showfor_panel = page.locator("section#showfor-panel")
        self.kb_submit_changes_input_field = page.locator("input#id_comment")
        self.kb_submit_changes_button = page.locator("button#submit-document-form")
        self.kb_title_error = page.locator(
            "//input[@id='id_title']//preceding-sibling::ul[@class='errorlist']/li")
        self.kb_slug_error = page.locator(
            "//input[@id='id_slug']//preceding-sibling::ul[@class='errorlist']/li")
        self.all_kb_errors = page.locator("ul[class='errorlist'] li")
        self.knowledge_base_option = lambda name: page.locator(
            "//div[@id='id_audiences-ts-dropdown']"
            f"//div[contains(@class,'option') and normalize-space(.)='{name}']")
        self.non_matching_knowledge_base_option = lambda name: page.locator(
            "//div[@id='id_audiences-ts-dropdown']"
            f"//div[contains(@class,'option') and not(contains(normalize-space(.),'{name}'))]")
        self.selected_knowledge_base = lambda name: page.locator(
            "//input[@id='id_audiences-ts-control']/../div[@class='item']"
            f"[normalize-space(text())='{name}']")
        self.relevant_to_product_checkbox = lambda product_name: page.locator(
            "//div[@id='id_products']//input[@id='id_products_{option_to_click}']/..")
        self.relevant_product = lambda product_name: page.locator(
            f"//section[@id='relevant-products']//label[normalize-space(text())='{product_name}']")
        self.parent_topic_checkbox = lambda parent_topic_name: page.locator(
            f"//section[@id='relevant-topics']//label[normalize-space("
            f"text())='{parent_topic_name}']")
        self.child_topic_checkbox = lambda parent_topic, child_topic_checkbox: page.locator(
            f"//section[@id='relevant-topics']//label[normalize-space(text())='{parent_topic}']/"
            f"../../..//label[normalize-space(text())='{child_topic_checkbox}']")

    """Actions against the page error locators."""
    def get_all_kb_errors(self) -> list[str]:
        return self._get_text_of_elements(self.all_kb_errors)

    """Actions against the new KB form locators."""
    def add_and_select_knowledge_base(self, name: str):
        """Add a knowledge base to the article.

        Args:
            name (str): The knowledge base name.
        """
        # The widget opens its dropdown on focus, so focus it before typing.
        self._click(self.kb_article_knowledge_bases_field)
        self._fill(self.kb_article_knowledge_bases_field, name)
        # TomSelect filters the dropdown 300ms after typing and re-renders the options, so an
        # option found in the unfiltered list can move before the click lands. Wait for the
        # filtered list, and retry the click until the knowledge base is selected.
        self._wait_for_locator(self.knowledge_base_option(name), timeout=10000,
                               raise_exception=True)
        self._wait_for_locator_to_be_hidden(self.non_matching_knowledge_base_option(name).first)
        self._click(self.knowledge_base_option(name),
                    expected_locator=self.selected_knowledge_base(name))

    def is_knowledge_base_selected(self, name: str) -> bool:
        return self._is_element_visible(self.selected_knowledge_base(name))

    def remove_selected_knowledge_base(self, name: str):
        """Remove a knowledge base from the article.

        Args:
            name (str): The knowledge base name.
        """
        self._click(self.selected_knowledge_base(name).locator("a.remove"))

    def add_text_to_article_form_title_field(self, text: str):
        # Clearing the field first from auto-population
        self._clear_field(self.kb_article_form_title)
        self._fill(self.kb_article_form_title, text)

    def add_text_to_article_slug_field(self, text: str):
        # Clearing the field first from auto-population
        self._clear_field(self.kb_article_form_slug)
        self._fill(self.kb_article_form_slug, text)

    def add_text_to_related_documents_field(self, text: str):
        self._fill(self.kb_article_search_for_related_documents, text)

    def add_text_to_keywords_field(self, text: str):
        self._fill(self.kb_article_keyword_input, text)

    def add_text_to_search_result_summary_field(self, text: str):
        self._fill(self.kb_article_search_result_summary_textarea, text)

    def add_text_to_expiry_date_field(self, text: str):
        self._type(self.kb_article_expiry_date, text, 0)

    def add_text_to_changes_description_field(self, text: str):
        self._fill(self.kb_submit_changes_input_field, text)

    def add_text_to_content_textarea(self, text: str):
        self._fill(self.kb_article_content_textarea, text)

    def is_content_textarea_displayed(self) -> bool:
        self._wait_for_locator(self.kb_article_content_textarea)
        return self._is_element_visible(self.kb_article_content_textarea)

    def click_on_insert_media_button(self):
        self._click(self.kb_article_insert_media)

    def click_on_toggle_syntax_highlight_option(self):
        self._click(self.kb_article_toggle_syntax_highlighting)

    def click_on_preview_content_button(self):
        self._click(self.kb_article_preview_content_button)

    def click_on_submit_for_review_button(self):
        self._click(self.kb_article_submit_for_preview_button)

    def click_on_changes_submit_button(self):
        self._click(self.kb_submit_changes_button)

    def click_on_a_particular_product(self, product_name: str):
        self._click(self.relevant_product(product_name))

    def click_on_a_particular_parent_topic_checkbox(self, parent_topic_name: str):
        self._click(self.parent_topic_checkbox(parent_topic_name))

    def click_on_a_particular_child_topic_checkbox(self, parent_topic: str,
                                                   child_topic_checkbox: str):
        self._click(self.child_topic_checkbox(parent_topic, child_topic_checkbox))

    def click_on_insert_media_textarea_option(self):
        self._click(self.kb_article_insert_media)

    def click_on_first_image_from_media_panel(self):
        self._click_on_first_item(self.kb_article_insert_media_modal_images)

    def click_on_insert_media_modal_button(self):
        self._click(self.kb_article_insert_media_modal_insert_button)

    def select_category_option_by_text(self, option: str):
        self._select_option_by_label(self.kb_article_category_select, option)

    def check_allow_discussion_on_article_checkbox(self):
        self._click(self.kb_article_allow_discussions_on_article)

    def is_allow_discussion_on_article_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.kb_article_allow_discussions_on_article)

    def check_allow_translations_checkbox(self):
        self._click(self.kb_article_allow_translations)

    def get_article_page_url(self) -> str:
        return self._get_current_page_url()
