from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class NewMessagePage(BasePage):

    # New message page locators.
    __new_message_page_header = "//h1[@class='sumo-page-heading']"
    __new_message_to_input_field = "//input[@id='token-input-id_to']"
    __new_message_textarea_input_field = "//textarea[@id='id_message']"
    __new_message_textarea_remaining_characters = "//div[@id='remaining-characters']"
    __new_message_cancel_button = "//a[contains(text(),'Cancel')]"
    __new_message_send_button = "//button[@name='send']"
    __new_message_preview_section = "//section[@id='preview']"
    __new_message_preview_section_content = "//div[@class='message']"
    __new_message_search_for_a_user_option = "//div[@class='token-input-dropdown-facebook']"
    __new_message_search_results_bolded_characters = "//div[@class='name_search']/b"
    __new_message_search_results_text = "//div[@class='name_search']"
    __sent_message_page_to_user_text = "//li[@class='token-input-token-facebook']/p"
    __sent_message_page_to_user_delete_button = ("//span[@class='token-input-delete-token"
                                                 "-facebook']")

    #  Preview Section
    __new_message_preview_username = "//div[contains(@class, 'user from')]/a"
    __new_message_preview_time = "//div[contains(@class, 'user from')]/time"
    __new_message_preview_data_first_paragraph_content = "//div[@class='message']/p[1]"
    __new_message_preview_data_first_paragraph_strong_content = ("//div[@class='message']/p["
                                                                 "1]/strong")
    __new_message_preview_data_first_paragraph_italic_content = "//div[@class='message']/p[1]/em"
    __new_message_numbered_list_items = "//div[@class='message']/ol/li"
    __new_message_bulleted_list_items = "//div[@class='message']/ul/li"
    __new_message_preview_external_link = "//a[contains(text(),'Test external link')]"
    __new_message_preview_internal_link = "//a[contains(text(),'Test internal Link')]"
    __new_message_preview_button = "//input[@id='preview-btn']"

    def __init__(self, page: Page):
        super().__init__(page)

    # New message page actions.
    def _get_text_of_test_data_first_paragraph_text(self) -> str:
        return super()._get_text_of_element(
            self.__new_message_preview_data_first_paragraph_content)

    def _get_text_of_test_data_first_p_strong_text(self) -> str:
        return super()._get_text_of_element(
            self.__new_message_preview_data_first_paragraph_strong_content)

    def _get_text_of_test_data_first_p_italic_text(self) -> str:
        return super()._get_text_of_element(
            self.__new_message_preview_data_first_paragraph_italic_content)

    def _get_text_of_numbered_list_items(self) -> list[str]:
        return super()._get_text_of_elements(self.__new_message_numbered_list_items)

    def _get_text_of_bulleted_list_items(self) -> list[str]:
        return super()._get_text_of_elements(self.__new_message_bulleted_list_items)

    def _get_text_of_message_preview_username(self) -> str:
        return super()._get_text_of_element(self.__new_message_preview_username)

    def _get_user_to_text(self) -> str:
        return super()._get_text_of_element(self.__sent_message_page_to_user_text)

    def _get_new_message_page_header_text(self) -> str:
        return super()._get_text_of_element(self.__new_message_page_header)

    # def _get_search_for_a_user_dropdown_text(self) -> str:
    #     return super()._get_text_of_element(self.__search_for_a_user_option)

    def _get_characters_remaining_text(self) -> str:
        return super()._get_text_of_element(self.__new_message_textarea_remaining_characters)

    def _get_characters_remaining_text_element(self) -> Locator:
        return super()._get_element_locator(self.__new_message_textarea_remaining_characters)

    def _get_text_of_new_message_preview_section(self) -> str:
        return super()._get_text_of_element(self.__new_message_preview_section_content)

    def _get_text_of_search_result_bolded_character(self) -> str:
        return super()._get_text_of_element(self.__new_message_search_results_bolded_characters)

    def _get_tet_of_search_results_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__new_message_search_results_text)

    def _click_on_username_to_delete_button(self):
        super()._click(self.__sent_message_page_to_user_delete_button)

    def _click_on_new_message_cancel_button(self):
        super()._click(self.__new_message_cancel_button)

    def _click_on_new_message_preview_button(self):
        super()._click(self.__new_message_preview_button)

    def _click_on_new_message_send_button(self):
        super()._click(self.__new_message_send_button)

    def _click_on_a_searched_user(self, username: str):
        xpath = f"//div[@class='name_search']/b[contains(text(), '{username}')]"
        super()._click(xpath)

    def _click_on_preview_internal_link(self):
        super()._click(self.__new_message_preview_internal_link)

    def _type_into_new_message_to_input_field(self, text: str):
        super()._type(self.__new_message_to_input_field, text, 0)

    def _fill_into_new_message_body_textarea(self, text: str):
        super()._fill(self.__new_message_textarea_input_field, text)

    def _type_into_new_message_body_textarea(self, text: str):
        super()._type(self.__new_message_textarea_input_field, text, 0)

    def _message_preview_section_element(self) -> Locator:
        return super()._get_element_locator(self.__new_message_preview_section)

    def _is_message_preview_time_displayed(self) -> bool:
        return super()._is_element_visible(self.__new_message_preview_time)

    def _new_message_preview_internal_link_test_data_element(self) -> Locator:
        return super()._get_element_locator(self.__new_message_preview_internal_link)

    def _new_message_preview_external_link_test_data_element(self) -> Locator:
        return super()._get_element_locator(self.__new_message_preview_external_link)
