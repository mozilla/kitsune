from selenium_tests.core.base_page import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


class NewMessagePage(BasePage):
    __new_message_page_header = (By.XPATH, "//h1[@class='sumo-page-heading']")
    __new_message_to_input_field = (By.XPATH, "//input[@id='token-input-id_to']")
    __new_message_textarea_input_field = (By.XPATH, "//textarea[@id='id_message']")
    __new_message_textarea_remaining_characters = (By.XPATH, "//div[@id='remaining-characters']")
    __new_message_cancel_button = (By.XPATH, "//a[contains(text(),'Cancel')]")
    __new_message_send_button = (By.XPATH, "//button[@name='send']")
    __new_message_preview_section = (By.XPATH, "//section[@id='preview']")
    __new_message_preview_section_content = (By.XPATH, "//div[@class='message']")
    __new_message_search_for_a_user_option = (
        By.XPATH,
        "//div[@class='token-input-dropdown-facebook']",
    )
    __new_message_search_results_bolded_characters = (By.XPATH, "//div[@class='name_search']/b")
    __new_message_search_results_text = (By.XPATH, "//div[@class='name_search']")
    __sent_message_page_to_user_text = (By.XPATH, "//li[@class='token-input-token-facebook']/p")
    __sent_message_page_to_user_delete_button = (
        By.XPATH,
        "//span[@class='token-input-delete-token-facebook']",
    )

    #  Preview Section
    __new_message_preview_username = (By.XPATH, "//div[contains(@class, 'user from')]/a")
    __new_message_preview_time = (By.XPATH, "//div[contains(@class, 'user from')]/time")
    __new_message_preview_data_first_paragraph_content = (By.XPATH, "//div[@class='message']/p[1]")
    __new_message_preview_data_first_paragraph_strong_content = (
        By.XPATH,
        "//div[@class='message']/p[1]/strong",
    )
    __new_message_preview_data_first_paragraph_italic_content = (
        By.XPATH,
        "//div[@class='message']/p[1]/em",
    )
    __new_message_numbered_list_items = (By.XPATH, "//div[@class='message']/ol/li")
    __new_message_bulleted_list_items = (By.XPATH, "//div[@class='message']/ul/li")
    __new_message_preview_external_link = (By.XPATH, "//a[contains(text(),'Test external link')]")
    __new_message_preview_internal_link = (By.XPATH, "//a[contains(text(),'Test internal Link')]")
    __new_message_preview_button = (By.XPATH, "//input[@id='preview-btn']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_text_of_test_data_first_paragraph_text(self) -> str:
        return super()._get_text_of_element(
            self.__new_message_preview_data_first_paragraph_content
        )

    def get_text_of_test_data_first_paragraph_strong_text(self) -> str:
        return super()._get_text_of_element(
            self.__new_message_preview_data_first_paragraph_strong_content
        )

    def get_text_of_test_data_first_paragraph_italic_text(self) -> str:
        return super()._get_text_of_element(
            self.__new_message_preview_data_first_paragraph_italic_content
        )

    def get_text_of_numbered_list_items(self) -> list[str]:
        return super()._get_text_of_elements(self.__new_message_numbered_list_items)

    def get_text_of_bulleted_list_items(self) -> list[str]:
        return super()._get_text_of_elements(self.__new_message_bulleted_list_items)

    def get_text_of_message_preview_username(self) -> str:
        return super()._get_text_of_element(self.__new_message_preview_username)

    def get_user_to_text(self) -> str:
        return super()._get_text_of_element(self.__sent_message_page_to_user_text)

    def get_new_message_page_header_text(self) -> str:
        return super()._get_text_of_element(self.__new_message_page_header)

    # def _get_search_for_a_user_dropdown_text(self) -> str:
    #     return super()._get_text_of_element(self.__search_for_a_user_option)

    def get_characters_remaining_text(self) -> str:
        return super()._get_text_of_element(self.__new_message_textarea_remaining_characters)

    def get_characters_remaining_text_color(self) -> str:
        return super()._get_value_of_css_property(
            self.__new_message_textarea_remaining_characters, "color"
        )

    def get_text_of_new_message_preview_section(self) -> str:
        return super()._get_text_of_element(self.__new_message_preview_section_content)

    def get_text_of_search_result_bolded_character(self) -> str:
        return super()._get_text_of_element(self.__new_message_search_results_bolded_characters)

    def get_tet_of_search_results_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__new_message_search_results_text)

    def click_on_username_to_delete_button(self):
        super()._click(self.__sent_message_page_to_user_delete_button)

    def click_on_new_message_cancel_button(self):
        super()._click(self.__new_message_cancel_button)

    def click_on_new_message_preview_button(self):
        super()._click(self.__new_message_preview_button)

    def click_on_new_message_send_button(self):
        super()._click(self.__new_message_send_button)

    def click_on_a_searched_user(self, username: str):
        xpath = (By.XPATH, f"//div[@class='name_search']/b[contains(text(), '{username}')]")
        super()._click(xpath)

    def click_on_preview_internal_link(self):
        super()._click(self.__new_message_preview_internal_link)

    def type_into_new_message_to_input_field(self, text: str):
        super()._type(self.__new_message_to_input_field, text)

    def type_into_new_message_body_textarea(self, text: str):
        super()._type(self.__new_message_textarea_input_field, text)

    def is_message_preview_section_displayed(self) -> bool:
        return super()._is_element_displayed(self.__new_message_preview_section)

    def is_message_preview_time_displayed(self) -> bool:
        return super()._is_element_displayed(self.__new_message_preview_time)

    def is_new_message_preview_internal_link_test_data_displayed(self) -> bool:
        return super()._is_element_displayed(self.__new_message_preview_internal_link)

    def is_new_message_preview_external_link_test_data_displayed(self) -> bool:
        return super()._is_element_displayed(self.__new_message_preview_external_link)
