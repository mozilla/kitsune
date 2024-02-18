from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page


class KBArticleEditMetadata(BasePage):
    # Edit article metadata page locators.
    __edit_article_metadata_page_header = "//h1[@class='sumo-page-heading']"
    __restrict_visibility_input_field = "//input[@id='id_restrict_to_groups-selectized']"
    __restricted_visibility_chosen_groups = ("//input[@id='id_restrict_to_groups-selectized"
                                             "']/../div[@class='item']")
    __clear_all_selected_groups_button = "//a[@class='clear']"
    __title_input_field = "//input[@id='id_title']"
    __slug_input_field = "//input[@id='id_slug']"
    __category_select_field = "//select[@id='id_category']"
    __obsolete_checkbox = "//input[@id='id_is_archived']"
    __allow_discussion_checkbox = "//input[@id='id_allow_discussion']"
    __needs_change_checkbox = "//input[@id='id_needs_change']"
    __save_changes_button = "//button[text()='Save']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Edit article metadata page actions.
    def _get_edit_article_metadata_page_header(self) -> str:
        return super()._get_element_text_content(self.__edit_article_metadata_page_header)

    def _delete_a_chosen_restricted_visibility_group(self, chosen_group: str):
        xpath = (f"//input[@id='id_restrict_to_groups-selectized']/../div[text()='{chosen_group}']"
                 f"/a")
        super()._click(xpath)

    def _clear_all_restricted_visibility_group_selections(self):
        super()._click(self.__clear_all_selected_groups_button)

    def _get_text_of_title_input_field(self):
        return super()._get_text_of_element(self.__title_input_field)

    def _add_text_to_title_field(self, text: str):
        super()._clear_field(self.__title_input_field)
        super()._fill(self.__title_input_field, text)

    def _get_slug_input_field(self) -> str:
        return super()._get_text_of_element(self.__slug_input_field)

    def _add_text_to_slug_field(self, text: str):
        super()._clear_field(self.__slug_input_field)
        super()._fill(self.__slug_input_field, text)

    def _select_category(self, option: str):
        super()._select_option_by_label(self.__category_select_field, option)

    def _is_relevant_checkbox_checked(self, option: str) -> bool:
        xpath = f"//div[@id='id_products']//label[text()='\n {option}']/input"
        return super()._is_checkbox_checked(xpath)

    def _check_a_particular_checkbox(self, option: str):
        xpath = f"//div[@id='id_products']//label[text()='\n {option}']/input"
        super()._click(xpath)

    def _click_on_a_particular_topics_foldout_section(self, option: str):
        xpath = f"//section[@id='accordion']//button[text()='{option}']"
        super()._click(xpath)

    def _is_a_particular_topic_checkbox_checked(self, option: str) -> bool:
        xpath = (f"//ul[@id='expand-mzpcdetailsh-0' and @aria-hidden='false']//label"
                 f"[text()='{option}']/../input")
        return super()._is_checkbox_checked(xpath)

    def _check_a_particular_topic_checkbox(self, option: str):
        xpath = (f"//ul[@id='expand-mzpcdetailsh-0' and @aria-hidden='false']//label"
                 f"[text()='{option}']")
        super()._click(xpath)

    def _is_obsolete_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__obsolete_checkbox)

    def _click_on_obsolete_checkbox(self):
        super()._click(self.__obsolete_checkbox)

    def _is_allow_discussion_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__allow_discussion_checkbox)

    def _click_on_allow_discussion_on_article_checkbox(self):
        super()._click(self.__allow_discussion_checkbox)

    def _is_needs_change_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__needs_change_checkbox)

    def _click_needs_change_checkbox(self):
        super()._click(self.__needs_change_checkbox)

    def _click_on_save_changes_button(self):
        super()._click(self.__save_changes_button)
