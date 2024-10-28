from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page


class KBArticleEditMetadata(BasePage):
    # Edit article metadata page locators.
    __edit_article_metadata_error = "//ul[@class='errorlist']"
    __edit_article_metadata_page_header = "//h1[@class='sumo-page-heading']"
    __restrict_visibility_input_field = "//input[@id='id_restrict_to_groups-selectized']"
    __restricted_visibility_chosen_groups = (
        "//input[@id='id_restrict_to_groups-selectized" "']/../div[@class='item']"
    )
    __clear_all_selected_groups_button = "//a[@class='clear']"
    __kb_article_restrict_visibility_field = "//input[@id='id_restrict_to_groups-selectized']"
    __kb_article_restrict_visibility_delete_all_groups = "//a[@title='Clear']"
    __title_input_field = "//input[@id='id_title']"
    __slug_input_field = "//input[@id='id_slug']"
    __category_select_field = "//select[@id='id_category']"
    __obsolete_checkbox = "//input[@id='id_is_archived']"
    __allow_discussion_checkbox = "//input[@id='id_allow_discussion']"
    __needs_change_checkbox = "//input[@id='id_needs_change']"
    __needs_change_textarea = "//textarea[@id='id_needs_change_comment']"
    __save_changes_button = "//button[text()='Save']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Edit article metadata page actions.
    def get_error_message(self) -> str:
        return self._get_text_of_element(self.__edit_article_metadata_error)

    def get_edit_article_metadata_page_header(self) -> str:
        return self._get_element_text_content(self.__edit_article_metadata_page_header)

    def delete_a_chosen_restricted_visibility_group(self, chosen_group: str):
        self._click(
            f"//input[@id='id_restrict_to_groups-selectized']/../"
            f"div[text()='{chosen_group}']/a"
        )

    def clear_all_restricted_visibility_group_selections(self):
        self._click(self.__clear_all_selected_groups_button)

    def is_clear_all_restricted_visibility_group_selection_visible(self) -> bool:
        return self._is_element_visible(self.__clear_all_selected_groups_button)

    def add_and_select_restrict_visibility_group_metadata(self, group_name: str):
        self._fill(self.__kb_article_restrict_visibility_field, group_name)
        self._click(f"//div[@class='option active']/span[text()='{group_name}']")

    def delete_a_restricted_visibility_group_metadata(self, group_name=""):
        if group_name != "":
            self._click(f"//div[@class='item' and text()='{group_name}']/a")
        else:
            self._click(self.__kb_article_restrict_visibility_delete_all_groups)

    def get_text_of_title_input_field(self) -> str:
        return self._get_element_input_value(self.__title_input_field)

    def add_text_to_title_field(self, text: str):
        self._clear_field(self.__title_input_field)
        self._fill(self.__title_input_field, text)

    def get_slug_input_field(self) -> str:
        return self._get_element_input_value(self.__slug_input_field)

    def add_text_to_slug_field(self, text: str):
        self._clear_field(self.__slug_input_field)
        self._fill(self.__slug_input_field, text)

    def select_category(self, option: str):
        self._select_option_by_label(self.__category_select_field, option)

    def check_product_checkbox(self, product_name: str):
        self._click(f"//section[@id='relevant-products']//label[normalize-space(text())"
                    f"='{product_name}']")

    def is_obsolete_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.__obsolete_checkbox)

    def click_on_obsolete_checkbox(self):
        self._click(self.__obsolete_checkbox)

    def is_allow_discussion_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.__allow_discussion_checkbox)

    def click_on_allow_discussion_on_article_checkbox(self):
        self._click(self.__allow_discussion_checkbox)

    def is_needs_change_checkbox(self) -> bool:
        return self._is_checkbox_checked(self.__needs_change_checkbox)

    def click_needs_change_checkbox(self):
        self._click(self.__needs_change_checkbox)

    def fill_needs_change_textarea(self, text: str):
        self._fill(self.__needs_change_textarea, text)

    def click_on_save_changes_button(self):
        self._click(self.__save_changes_button)
        self._wait_for_dom_load_to_finish()
