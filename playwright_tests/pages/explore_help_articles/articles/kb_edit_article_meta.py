from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBArticleEditMetadata(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the edit article metadata page."""
        self.edit_article_metadata_error = page.locator("ul[class='errorlist']")
        self.edit_article_metadata_page_header = page.locator("h1[class='sumo-page-heading']")
        self.restrict_visibility_input_field = page.locator(
            "input#id_restrict_to_groups-ts-control")
        self.restricted_visibility_chosen_groups = page.locator(
            "input#id_restrict_to_groups-ts-control ~ div[class='item']")
        self.clear_all_selected_groups_button = page.locator("div[class='clear-button']")
        self.kb_article_restrict_visibility_field = page.locator(
            "input#id_restrict_to_groups-ts-control")
        self.title_input_field = page.locator("input#id_title")
        self.slug_input_field = page.locator("input#id_slug")
        self.category_select_field = page.locator("select#id_category")
        self.obsolete_checkbox = page.locator("input#id_is_archived")
        self.allow_discussion_checkbox = page.locator("input#id_allow_discussion")
        self.needs_change_checkbox = page.locator("input#id_needs_change")
        self.needs_change_textarea = page.locator("textarea#id_needs_change_comment")
        self.related_documents_field = page.locator("input#search-related-ts-control")
        self.related_documents_search_result = lambda search_term : page.locator(
            f'//div[@id="search-related-ts-dropdown"]/div[normalize-space(.)="{search_term}"]'
        )
        self.related_documents_search_results = page.locator(
            "div#search-related-ts-dropdown div")
        self.added_related_documents = page.locator("div.ts-control div.item")
        self.remove_related_documents_button = lambda related_document: page.locator(
            f'//div[@class="item" and text()="{related_document}"]/a')
        self.no_results_found_related_documents_message = page.locator(
            "div#search-related-ts-dropdown div.no-results")
        self.save_changes_button = page.get_by_role("button", name="Save", exact=True)
        self.delete_group = lambda chosen_group: page.locator(
            f"//input[@id='id_restrict_to_groups-selectized']/../div[text()='{chosen_group}']/a")
        self.restrict_group = lambda group_name: page.locator(
            f"//div[@class='option active']/span[text()='{group_name}']")
        self.delete_a_group = lambda group_name: page.locator(
            f"//div[@class='item' and text()='{group_name}']/a")
        self.relevant_product_checkbox = lambda product_name: page.locator(
            f"//section[@id='relevant-products']//label[normalize-space(text())='{product_name}']")

    """Actions against the edit article metadata page locators."""
    def get_error_message(self) -> str:
        return self._get_text_of_element(self.edit_article_metadata_error)

    def get_edit_article_metadata_page_header(self) -> str:
        return self._get_element_text_content(self.edit_article_metadata_page_header)

    def delete_a_chosen_restricted_visibility_group(self, chosen_group: str):
        self._click(self.delete_group(chosen_group))

    def add_and_select_restrict_visibility_group_metadata(self, group_name: str):
        self._fill(self.kb_article_restrict_visibility_field, group_name)
        self._click(self.restrict_group(group_name))

    def delete_a_restricted_visibility_group_metadata(self, groups: [str, list[str]]):
        if isinstance(groups, str):
            self._click(self.delete_a_group(groups))
        else:
            for group in groups:
                self._click(self.delete_a_group(group))

    def get_text_of_title_input_field(self) -> str:
        return self._get_element_input_value(self.title_input_field)

    def add_text_to_title_field(self, text: str):
        self._clear_field(self.title_input_field)
        self._fill(self.title_input_field, text)

    def get_slug_input_field(self) -> str:
        return self._get_element_input_value(self.slug_input_field)

    def add_text_to_slug_field(self, text: str):
        self._clear_field(self.slug_input_field)
        self._fill(self.slug_input_field, text)

    def select_category(self, option: str):
        self._select_option_by_label(self.category_select_field, option)

    def check_product_checkbox(self, product_name: str):
        self._click(self.relevant_product_checkbox(product_name))

    def is_obsolete_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.obsolete_checkbox)

    def is_obsolete_checkbox_displayed(self) -> bool:
        return self._is_element_visible(self.obsolete_checkbox)

    def click_on_obsolete_checkbox(self):
        self._click(self.obsolete_checkbox)

    def is_allow_discussion_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.allow_discussion_checkbox)

    def click_on_allow_discussion_on_article_checkbox(self):
        self._click(self.allow_discussion_checkbox)

    def is_needs_change_checkbox(self) -> bool:
        return self._is_checkbox_checked(self.needs_change_checkbox)

    def is_needs_change_checkbox_displayed(self) -> bool:
        return self._is_element_visible(self.needs_change_checkbox)

    def click_needs_change_checkbox(self):
        self._click(self.needs_change_checkbox)

    def fill_needs_change_textarea(self, text: str):
        self._fill(self.needs_change_textarea, text)

    def add_related_documents(self, document_name: str, submit: bool = True):
        self._fill(self.related_documents_field, document_name)
        if submit:
            self._wait_for_locator(self.related_documents_search_result(document_name), 5000)
            self._click(self.related_documents_search_result(document_name))

    def is_no_related_documents_displayed(self) -> bool:
        return self._is_element_visible(self.no_results_found_related_documents_message)

    def get_related_documents_search_options(self) -> list[str]:
        return self._get_text_of_elements(self.related_documents_search_results)

    def get_related_documents(self) -> list[str]:
        return [text.replace("\n×", "").strip() for text in self._get_text_of_elements(
            self.added_related_documents)]

    def remove_related_document(self, document_name: str):
        self._click(self.remove_related_documents_button(document_name))

    def click_on_save_changes_button(self):
        self._click(self.save_changes_button)
