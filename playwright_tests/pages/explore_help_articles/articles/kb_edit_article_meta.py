from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class KBArticleEditMetadata(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the edit article metadata page."""
        self.edit_article_metadata_error = page.locator("ul[class='errorlist']")
        self.kb_article_restrict_visibility_field = page.locator(
            "input#id_restrict_to_groups-ts-control")
        self.title_input_field = page.locator("input#id_title")
        self.slug_input_field = page.locator("input#id_slug")
        self.category_select_field = page.locator("select#id_category")
        self.obsolete_checkbox = page.locator("input#id_is_archived")
        self.allow_discussion_checkbox = page.locator("input#id_allow_discussion")
        self.needs_change_checkbox = page.locator("input#id_needs_change")
        self.obsolete_checkbox_label = page.locator(
            "div.checkbox label[for='id_is_archived']")
        self.allow_discussion_checkbox_label = page.locator(
            "div.checkbox label[for='id_allow_discussion']")
        self.needs_change_checkbox_label = page.locator(
            "div.checkbox label[for='id_needs_change']")
        self.needs_change_textarea = page.locator("textarea#id_needs_change_comment")
        self.related_documents_field = page.locator("input#search-related-ts-control")
        self.related_documents_search_result = lambda search_term : page.locator(
            f'//div[@id="search-related-ts-dropdown"]/div[normalize-space(.)="{search_term}"]'
        )
        self.remove_related_documents_button = lambda related_document: page.locator(
            f'//div[@class="item" and text()="{related_document}"]/a')
        self.no_results_found_related_documents_message = page.locator(
            "div#search-related-ts-dropdown div.no-results")
        self.save_changes_button = page.get_by_role("button", name="Save", exact=True)
        self.delete_group = lambda chosen_group: page.locator(
            f"//input[@id='id_restrict_to_groups-selectized']/../div[text()='{chosen_group}']/a")
        self.delete_a_group = lambda group_name: page.locator(
            f"//div[@class='item' and text()='{group_name}']/a")
        self.restrict_visibility_dropdown = page.locator("div#id_restrict_to_groups-ts-dropdown")
        self.restrict_visibility_dropdown_option = lambda group_name: page.locator(
            "//div[@id='id_restrict_to_groups-ts-dropdown']"
            f"//div[contains(@class,'option') and normalize-space(.)='{group_name}']")
        self.selected_restricted_visibility_groups = page.locator(
            "//input[@id='id_restrict_to_groups-ts-control']/../div[@class='item']")
        self.selected_restricted_visibility_group = lambda group_name: page.locator(
            "//input[@id='id_restrict_to_groups-ts-control']/../div[@class='item']"
            f"[normalize-space(text())='{group_name}']")
        self.relevant_product_checkbox = lambda product_name: page.locator(
            f"//section[@id='relevant-products']//label[normalize-space(text())='{product_name}']")
        self.clear_selected_products_link = page.locator("a#relevant-products-clear-selected")
        self.clear_selected_topics_link = page.locator("a#relevant-topics-clear-selected")

    """Actions against the edit article metadata page locators."""
    def delete_a_chosen_restricted_visibility_group(self, chosen_group: str):
        self._click(self.delete_group(chosen_group))

    def add_and_select_restrict_visibility_group_metadata(self, group_name: str):
        self._fill(self.kb_article_restrict_visibility_field, group_name)
        self._wait_for_locator(self.restrict_visibility_dropdown_option(group_name),
                               raise_exception=True)
        self._click(self.restrict_visibility_dropdown_option(group_name))

    def search_for_a_restricted_visibility_group(self, group_name: str):
        """Type a group name into the restrict visibility field and wait for the widget
        dropdown, so that assertions against its options are not made against a dropdown
        which hasn't rendered yet.

        Args:
            group_name (str): The group name.
        """
        self._fill(self.kb_article_restrict_visibility_field, group_name)
        self._wait_for_locator(self.restrict_visibility_dropdown)

    def delete_a_restricted_visibility_group_metadata(self, groups: [str, list[str]]):
        if isinstance(groups, str):
            self._click(self.delete_a_group(groups))
        else:
            for group in groups:
                self._click(self.delete_a_group(group))

    def add_text_to_title_field(self, text: str):
        self._clear_field(self.title_input_field)
        self._fill(self.title_input_field, text)

    def add_text_to_slug_field(self, text: str):
        self._clear_field(self.slug_input_field)
        self._fill(self.slug_input_field, text)

    def select_category(self, option: str):
        self._select_option_by_label(self.category_select_field, option)

    def get_selected_category_value(self) -> str:
        return self._get_element_input_value(self.category_select_field)

    def check_product_checkbox(self, product_name: str):
        self._click(self.relevant_product_checkbox(product_name))

    def clear_selected_products(self):
        """Clear the currently selected products.

        The 'Clear' link is rendered only while at least one product is selected.
        """
        if self._is_element_visible(self.clear_selected_products_link):
            self._click(self.clear_selected_products_link)

    def clear_selected_topics(self):
        """Clear the currently selected topics.

        The 'Clear' link is rendered only while at least one topic is selected.
        """
        if self._is_element_visible(self.clear_selected_topics_link):
            self._click(self.clear_selected_topics_link)

    def is_obsolete_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.obsolete_checkbox)

    def is_obsolete_checkbox_displayed(self) -> bool:
        return self._is_element_visible(self.obsolete_checkbox)

    def click_on_obsolete_checkbox(self):
        self._click(self.obsolete_checkbox_label)

    def is_allow_discussion_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.allow_discussion_checkbox)

    def click_on_allow_discussion_on_article_checkbox(self):
        self._click(self.allow_discussion_checkbox_label)

    def is_needs_change_checkbox(self) -> bool:
        return self._is_checkbox_checked(self.needs_change_checkbox)

    def is_needs_change_checkbox_displayed(self) -> bool:
        return self._is_element_visible(self.needs_change_checkbox)

    def click_needs_change_checkbox(self):
        self._click(self.needs_change_checkbox_label)

    def fill_needs_change_textarea(self, text: str):
        self._fill(self.needs_change_textarea, text)

    def add_related_documents(self, document_name: str, submit: bool = True):
        self._fill(self.related_documents_field, document_name)
        if submit:
            self._wait_for_locator(self.related_documents_search_result(document_name), 5000)
            self._click(self.related_documents_search_result(document_name))

    def remove_related_document(self, document_name: str):
        self._click(self.remove_related_documents_button(document_name))

    def click_on_save_changes_button(self):
        self._click(self.save_changes_button)
