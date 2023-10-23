from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage
from selenium_tests.messages.my_profile_pages_messages.edit_my_profile_page_messages import (
    EditMyProfilePageMessages,
)


class MyProfileEdit(BasePage):
    # Access denied section
    __access_denied_main_header = (By.XPATH, "//article[@id='error-page']/h1")
    __access_denied_subheading_message = (By.XPATH, "//div[@class='center-on-mobile']/p")

    # Navbar section
    __my_profile_user_navbar_options = (By.XPATH, "//ul[@id='user-nav']/li/a")
    __my_profile_user_navbar_selected_element = (By.XPATH, "//a[@class='selected']")

    # Edit profile page
    __edit_my_profile_edit_input_form = (By.XPATH, "//article[@id='edit-profile']/form")
    __edit_my_profile_main_header = (By.XPATH, "//h1[@class='sumo-page-heading']")
    __manage_firefox_account_button = (By.XPATH, "//a[contains(text(),'Manage account')]")
    __username_input_field = (By.XPATH, "//input[@id='id_username']")
    __username_error_message = (
        By.XPATH,
        "//input[@id='id_username']/following-sibling::span[contains(@class, "
        "'form-error is-visible')]",
    )
    __display_name_input_field = (By.XPATH, "//input[@id='id_name']")
    __biography_textarea_field = (By.XPATH, "//textarea[@id='id_bio']")
    __make_email_visible_to_logged_in_users_checkbox = (
        By.XPATH,
        "//label[@for='id_public_email']",
    )
    __website_input_field = (By.XPATH, "//input[@id='id_website']")
    __twitter_username_field = (By.XPATH, "//input[@id='id_twitter']")
    __community_portal_username_field = (By.XPATH, "//input[@id='id_community_mozilla_org']")
    __people_directory_username_field = (By.XPATH, "//input[@id='id_people_mozilla_org']")
    __matrix_nickname_field = (By.XPATH, "//input[@id='id_matrix_handle']")
    __country_dropdown = (By.XPATH, "//select[@id='id_country']")
    __city_field = (By.XPATH, "//input[@id='id_city']")
    __timezone_dropdown = (By.XPATH, "//select[@id='id_timezone']")
    __preferred_locale_dropdown = (By.XPATH, "//select[@id='id_locale']")
    __involved_with_mozilla_from_month = (By.XPATH, "//select[@id='id_involved_from_month']")
    __involved_with_mozilla_from_year = (By.XPATH, "//select[@id='id_involved_from_year']")
    __cancel_button = (By.XPATH, "//button[contains(text(),'Cancel')]")
    __update_my_profile_button = (By.XPATH, "//button[contains(text(),'Update My Profile')]")
    __close_account_and_delete_all_profile_information_link = (
        By.XPATH,
        "//p[@class='delete-account-link']/a",
    )
    __all_input_edit_profile_input_fields = (
        By.XPATH,
        "//form[not(contains(@action, "
        "'/en-US/users/close_account'))]/div[@class='field']/input["
        "not(contains(@id, 'id_username'))]",
    )

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_access_denied_header_text(self) -> str:
        return super()._get_text_of_element(self.__access_denied_main_header)

    def get_access_denied_subheading_text(self) -> str:
        return super()._get_text_of_element(self.__access_denied_subheading_message)

    def get_value_of_all_input_fields(self) -> list[str]:
        return super()._get_values_of_web_elements_attributes(
            self.__all_input_edit_profile_input_fields
        )

    def get_timezone_select_value(self) -> str:
        return super()._get_select_chosen_option(self.__timezone_dropdown)

    def get_preferred_locale_select_value(self) -> str:
        return super()._get_select_chosen_option(self.__preferred_locale_dropdown)

    def get_involved_with_mozilla_month_select_value(self) -> str:
        return super()._get_select_chosen_option(self.__involved_with_mozilla_from_month)

    def get_involved_with_mozilla_year_select_value(self) -> str:
        return super()._get_select_chosen_option(self.__involved_with_mozilla_from_year)

    def get_value_of_all_fields(self) -> list[str]:
        values = [
            self.get_value_of_all_input_fields(),
            self.get_timezone_select_value(),
            self.get_preferred_locale_select_value(),
            self.get_involved_with_mozilla_month_select_value(),
            self.get_involved_with_mozilla_year_select_value(),
        ]
        return values

    def get_username_input_field_value(self) -> str:
        return super()._get_value_of_web_element_attribute(self.__username_input_field)

    def get_username_error_message_text(self) -> str:
        return super()._get_text_of_element(self.__username_error_message)

    def get_display_name_input_field_value(self) -> str:
        return super()._get_value_of_web_element_attribute(self.__display_name_input_field)

    def get_website_input_field_value(self) -> str:
        return super()._get_value_of_web_element_attribute(self.__website_input_field)

    def get_twitter_input_field_value(self) -> str:
        return super()._get_value_of_web_element_attribute(self.__twitter_username_field)

    def get_community_portal_field_value(self) -> str:
        return super()._get_value_of_web_element_attribute(self.__community_portal_username_field)

    def get_people_directory_field_value(self) -> str:
        return super()._get_value_of_web_element_attribute(self.__people_directory_username_field)

    def get_matrix_username_field_value(self) -> str:
        return super()._get_value_of_web_element_attribute(self.__matrix_nickname_field)

    def get_city_field_value(self) -> str:
        return super()._get_value_of_web_element_attribute(self.__city_field)

    def send_text_to_username_field(self, text: str):
        super()._type(self.__username_input_field, text)

    def send_text_to_display_name_field(self, text: str):
        super()._type(self.__display_name_input_field, text)

    def send_text_to_biography_field(self, text: str):
        super()._type(self.__biography_textarea_field, text)

    def send_text_to_website_field(self, text: str):
        super()._type(self.__website_input_field, text)

    def send_text_to_twitter_username_field(self, text: str):
        super()._type(self.__twitter_username_field, text)

    def send_text_to_community_portal_field(self, text: str):
        super()._type(self.__community_portal_username_field, text)

    def send_text_to_people_directory_username(self, text: str):
        super()._type(self.__people_directory_username_field, text)

    def send_text_to_matrix_nickname_field(self, text: str):
        super()._type(self.__matrix_nickname_field, text)

    def sent_text_to_city_field(self, text: str):
        super()._type(self.__city_field, text)

    def select_country_dropdown_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__country_dropdown, option_value)

    def select_timezone_dropdown_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__timezone_dropdown, option_value)

    def select_preferred_language_dropdown_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__preferred_locale_dropdown, option_value)

    def select_involved_with_mozilla_from_month_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__involved_with_mozilla_from_month, option_value)

    def select_involved_with_mozilla_from_year_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__involved_with_mozilla_from_year, option_value)

    def clear_all_input_fields(self):
        for element in super()._find_elements(self.__all_input_edit_profile_input_fields):
            element.clear()

    def clear_biography_textarea_field(self):
        super()._find_element(self.__biography_textarea_field).clear()

    def clear_username_field(self):
        super()._find_element(self.__username_input_field).clear()

    def clear_display_name_field(self):
        super()._find_element(self.__display_name_input_field).clear()

    def clear_website_field(self):
        super()._find_element(self.__website_input_field).clear()

    def clear_twitter_field(self):
        super()._find_element(self.__twitter_username_field).clear()

    def clear_community_portal_field(self):
        super()._find_element(self.__community_portal_username_field).clear()

    def clear_people_directory_field(self):
        super()._find_element(self.__people_directory_username_field).clear()

    def clear_matrix_field(self):
        super()._find_element(self.__matrix_nickname_field).clear()

    def clear_country_dropdown_field(self):
        super()._select_option_by_value(self.__country_dropdown, "")

    def clear_city_field(self):
        super()._find_element(self.__city_field).clear()

    def clear_involved_from_month_select_field(self):
        super()._select_option_by_value(self.__involved_with_mozilla_from_month, "0")

    def clear_involved_from_year_select_field(self):
        super()._select_option_by_value(self.__involved_with_mozilla_from_year, "0")

    def click_cancel_button(self):
        super()._click(self.__cancel_button)

    def click_update_my_profile_button(self):
        super()._click(self.__update_my_profile_button)

    def click_close_account_option(self):
        super()._click(self.__close_account_and_delete_all_profile_information_link)

    def click_manage_firefox_account_button(self):
        super()._click(self.__manage_firefox_account_button)

    def click_make_email_visible_checkbox(self):
        super()._click(self.__make_email_visible_to_logged_in_users_checkbox)

    def is_make_email_visible_checkbox_selected(self) -> bool:
        checkbox_background_color = super()._get_css_value_of_pseudo_html_element(
            'label[for="id_public_email"]', ":before", "background-color"
        )
        if (
            checkbox_background_color
            == EditMyProfilePageMessages.MAKE_EMAIL_ADDRESS_VISIBLE_PSEUDO_ELEMENT_CHECKBOX_COLOR
        ):
            return True
        else:
            return False

    def is_my_profile_edit_form_displayed(self) -> bool:
        return super()._is_element_displayed(self.__edit_my_profile_edit_input_form)
