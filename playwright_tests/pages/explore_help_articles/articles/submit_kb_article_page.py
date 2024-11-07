from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class SubmitKBArticlePage(BasePage):
    __kb_article_for_contributors_sidebar = "//nav[@id='for-contributors-sidebar']"
    # New KB article form locators.
    __kb_article_restrict_visibility_field = "//input[@id='id_restrict_to_groups-ts-control']"
    __kb_article_restrict_visibility_delete_all_groups = "//div[@class='clear-button']"
    __kb_article_form_title = "//input[@id='id_title']"
    __kb_article_form_slug = "//input[@id='id_slug']"
    __kb_article_category_select = "//select[@id='id_category']"
    __kb_article_is_localizable_checkbox = "//input[@id='id_is_localizable']"
    __kb_article_allow_discussions_on_article = "//label[@for='id_allow_discussion']"
    __kb_article_allow_translations = "//label[@for='id_is_localizable']"
    __kb_article_search_for_related_documents = "//input[@id='search-related']"
    __kb_article_keyword_input = "//input[@id='id_keywords']"
    __kb_article_search_result_summary_textarea = "//textarea[@id='id_summary']"
    # New KB article content locators.
    __kb_article_content_textarea = "//textarea[@id='id_content'][1]"
    __kb_article_insert_media = "//button[contains(@class, 'btn-media')]"
    __kb_article_insert_media_modal_images = "//div[@id='media-modal']//img"
    __kb_article_insert_media_modal_insert_button = "//button[contains(text(), 'Insert Media')]"
    __kb_article_toggle_syntax_highlighting = "//a[contains(text(), 'Toggle syntax highlight')]"
    __kb_article_expiry_date = "//input[@id='id_expires']"
    __kb_article_preview_content_button = (
        "//div[contains(@class, 'submit')]/button[contains(" "@class, 'btn-preview')]"
    )
    __kb_article_preview_image = "//div[@id='doc-content']//img"
    __kb_article_submit_for_preview_button = (
        "//div[contains(@class, 'submit')]/button[contains(" "@class,  'submit')]"
    )
    __kb_article_preview_content = "//div[@id='doc-content']"
    __kb_article_showfor_panel = "//section[@id='showfor-panel']"
    __kb_submit_changes_input_field = "//input[@id='id_comment']"
    __kb_submit_changes_button = "//button[@id='submit-document-form']"
    __kb_title_error = "//input[@id='id_title']//preceding-sibling::ul[@class='errorlist']/li"
    __kb_slug_error = "//input[@id='id_slug']//preceding-sibling::ul[@class='errorlist']/li"
    __all_kb_errors = "//ul[@class='errorlist']/li"

    def __init__(self, page: Page):
        super().__init__(page)

    # Page error actions.
    def get_all_kb_errors(self) -> list[str]:
        return self._get_text_of_elements(self.__all_kb_errors)

    def get_kb_title_error_locator(self) -> Locator:
        return self._get_element_locator(self.__kb_title_error)

    def get_kb_title_error_text(self) -> str:
        return self._get_text_of_element(self.__kb_title_error)

    def get_kb_slug_error(self) -> Locator:
        return self._get_element_locator(self.__kb_slug_error)

    def get_kb_slug_error_text(self) -> str:
        return self._get_text_of_element(self.__kb_slug_error)

    # For Contributors side navbar actions.
    def for_contributors_section(self) -> Locator:
        return self._get_element_locator(self.__kb_article_for_contributors_sidebar)

    # New KB form actions.
    def add_and_select_restrict_visibility_group(self, group_name: str):
        self._fill(self.__kb_article_restrict_visibility_field, group_name)
        self._click(f"//div[@class='option active']/span[text()='{group_name}']")

    def delete_a_restricted_visibility_group(self, group_name: str):
        self._click(f"//div[@class='item' and text()='{group_name}']/a")

    def delete_all_restricted_visibility_groups(self):
        self._click(self.__kb_article_restrict_visibility_delete_all_groups)

    def add_text_to_article_form_title_field(self, text: str):
        # Clearing the field first from auto-population
        self._clear_field(self.__kb_article_form_title)
        self._fill(self.__kb_article_form_title, text)

    def add_text_to_article_slug_field(self, text: str):
        # Clearing the field first from auto-population
        self._clear_field(self.__kb_article_form_slug)
        self._fill(self.__kb_article_form_slug, text)

    def add_text_to_related_documents_field(self, text: str):
        self._fill(self.__kb_article_search_for_related_documents, text)

    def add_text_to_keywords_field(self, text: str):
        self._fill(self.__kb_article_keyword_input, text)

    def add_text_to_search_result_summary_field(self, text: str):
        self._fill(self.__kb_article_search_result_summary_textarea, text)

    def add_text_to_expiry_date_field(self, text: str):
        self._type(self.__kb_article_expiry_date, text, 0)

    def add_text_to_changes_description_field(self, text: str):
        self._fill(self.__kb_submit_changes_input_field, text)

    def add_text_to_content_textarea(self, text: str):
        self._fill(self.__kb_article_content_textarea, text)

    def is_content_textarea_displayed(self) -> bool:
        self._wait_for_selector(self.__kb_article_content_textarea)
        return self._is_element_visible(self.__kb_article_content_textarea)

    def click_on_insert_media_button(self):
        self._click(self.__kb_article_insert_media)

    def click_on_toggle_syntax_highlight_option(self):
        self._click(self.__kb_article_toggle_syntax_highlighting)

    def click_on_preview_content_button(self):
        self._click(self.__kb_article_preview_content_button)

    def click_on_submit_for_review_button(self):
        self._click(self.__kb_article_submit_for_preview_button)

    def click_on_changes_submit_button(self):
        self._click(self.__kb_submit_changes_button)

    def is_showfor_panel_displayed(self) -> Locator:
        return self._get_element_locator(self.__kb_article_showfor_panel)

    def is_preview_content_section_displayed(self) -> Locator:
        return self._get_element_locator(self.__kb_article_preview_content)

    def get_text_of_label_for_relevant_to_checkbox(self, option_to_click) -> str:
        return self._get_text_of_element(
            f"//div[@id='id_products']//" f"input[@id='id_products_{option_to_click}']/.."
        )

    def click_on_a_particular_product(self, product_name: str):
        self._click(f"//section[@id='relevant-products']//label[normalize-space(text())"
                    f"='{product_name}']")

    def click_on_a_particular_parent_topic_checkbox(self, parent_topic_name: str):
        self._click(f"//section[@id='relevant-topics']//label[normalize-space(text())"
                    f"='{parent_topic_name}']")

    def click_on_a_particular_child_topic_checkbox(
        self, parent_topic: str, child_topic_checkbox: str
    ):
        self._click(f"//section[@id='relevant-topics']//label[normalize-space(text())='"
                    f"{parent_topic}']/../../..//label[normalize-space(text())='"
                    f"{child_topic_checkbox}']")

    def click_on_insert_media_textarea_option(self):
        self._click(self.__kb_article_insert_media)

    def click_on_first_image_from_media_panel(self):
        self._click_on_first_item(self.__kb_article_insert_media_modal_images)

    def click_on_insert_media_modal_button(self):
        self._click(self.__kb_article_insert_media_modal_insert_button)

    def select_category_option_by_text(self, option: str):
        self._select_option_by_label(self.__kb_article_category_select, option)

    def check_allow_discussion_on_article_checkbox(self):
        self._click(self.__kb_article_allow_discussions_on_article)

    def is_allow_discussion_on_article_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.__kb_article_allow_discussions_on_article)

    def check_allow_translations_checkbox(self):
        self._click(self.__kb_article_allow_translations)

    def get_article_page_url(self) -> str:
        return self._get_current_page_url()
