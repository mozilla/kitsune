from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileEdit(BasePage):
    # Access denied section
    __access_denied_main_header = "//article[@id='error-page']/h1"
    __access_denied_subheading_message = "//div[@class='center-on-mobile']/p"

    # Navbar section
    __my_profile_user_navbar_options = "//ul[@id='user-nav']/li/a"
    __my_profile_user_navbar_selected_element = "//a[@class='selected']"

    # Edit profile page
    __edit_my_profile_edit_input_form = "//article[@id='edit-profile']/form"
    __edit_my_profile_main_header = "//h1[@class='sumo-page-heading']"
    __manage_firefox_account_button = "//a[contains(text(),'Manage account')]"
    __username_input_field = "//input[@id='id_username']"
    __username_error_message = ("//input[@id='id_username']/following-sibling::span[contains("
                                "@class, 'form-error is-visible')]")
    __display_name_input_field = "//input[@id='id_name']"
    __biography_textarea_field = "//textarea[@id='id_bio']"
    __make_email_visible_to_logged_in_users_checkbox = "//label[@for='id_public_email']"
    __website_input_field = "//input[@id='id_website']"
    __twitter_username_field = "//input[@id='id_twitter']"
    __community_portal_username_field = "//input[@id='id_community_mozilla_org']"
    __people_directory_username_field = "//input[@id='id_people_mozilla_org']"
    __matrix_nickname_field = "//input[@id='id_matrix_handle']"
    __country_dropdown = "//select[@id='id_country']"
    __city_field = "//input[@id='id_city']"
    __timezone_dropdown = "#id_timezone"
    __preferred_locale_dropdown = "//select[@id='id_locale']"
    __involved_with_mozilla_from_month = "//select[@id='id_involved_from_month']"
    __involved_with_mozilla_from_year = "//select[@id='id_involved_from_year']"
    __cancel_button = "//button[contains(text(),'Cancel')]"
    __update_my_profile_button = "//button[contains(text(),'Update My Profile')]"
    __close_account_and_delete_all_profile_information_link = "//p[@class='delete-account-link']/a"
    __all_input_edit_profile_input_fields = ("//form[not(contains(@action, "
                                             "'/en-US/users/close_account'))]/div["
                                             "@class='field']/input[not(contains(@id, "
                                             "'id_username'))]")

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_access_denied_header_text(self) -> str:
        return super()._get_text_of_element(self.__access_denied_main_header)

    def _get_access_denied_subheading_text(self) -> str:
        return super()._get_text_of_element(self.__access_denied_subheading_message)

    def _get_value_of_all_input_fields(self) -> list[str]:
        elements = super()._get_element_handles(self.__all_input_edit_profile_input_fields)
        values = []
        for el in elements:
            values.append(el.input_value())

        return values

    def _get_timezone_select_value(self) -> str:
        return super()._get_element_inner_text_from_page("#id_timezone [selected]")

    def _get_preferred_locale_select_value(self) -> str:
        return super()._get_element_inner_text_from_page('#id_locale [selected]')

    # Above not working trying to find a different solution

    def _get_involved_with_mozilla_month_select_value(self) -> str:
        return super()._get_text_of_element(self.__involved_with_mozilla_from_month)
        # return super()._get_select_chosen_option(self.__involved_with_mozilla_from_month)

    def _get_involved_with_mozilla_year_select_value(self) -> str:
        return super()._get_text_of_element(self.__involved_with_mozilla_from_year)
        # return super()._get_select_chosen_option(self.__involved_with_mozilla_from_year)

    def _get_value_of_all_fields(self) -> list[str]:
        values = [
            self._get_value_of_all_input_fields(),
            self._get_timezone_select_value(),
            self._get_preferred_locale_select_value(),
            self._get_involved_with_mozilla_month_select_value(),
            self._get_involved_with_mozilla_year_select_value(),
        ]
        return values

    def _get_username_input_field_value(self) -> str:
        return super()._get_element_input_value(self.__username_input_field)

    def _get_username_error_message_text(self) -> str:
        return super()._get_text_of_element(self.__username_error_message)

    def _get_display_name_input_field_value(self) -> str:
        return super()._get_element_input_value(self.__display_name_input_field)

    def _get_website_input_field_value(self) -> str:
        return super()._get_element_input_value(self.__website_input_field)

    def _get_twitter_input_field_value(self) -> str:
        return super()._get_element_input_value(self.__twitter_username_field)

    def _get_community_portal_field_value(self) -> str:
        return super()._get_element_input_value(self.__community_portal_username_field)

    def _get_people_directory_field_value(self) -> str:
        return super()._get_element_input_value(self.__people_directory_username_field)

    def _get_matrix_username_field_value(self) -> str:
        return super()._get_element_input_value(self.__matrix_nickname_field)

    def _get_city_field_value(self) -> str:
        return super()._get_element_input_value(self.__city_field)

    def _send_text_to_username_field(self, text: str):
        super()._fill(self.__username_input_field, text)

    def _send_text_to_display_name_field(self, text: str):
        super()._fill(self.__display_name_input_field, text)

    def _send_text_to_biography_field(self, text: str):
        super()._fill(self.__biography_textarea_field, text)

    def _send_text_to_website_field(self, text: str):
        super()._fill(self.__website_input_field, text)

    def _send_text_to_twitter_username_field(self, text: str):
        super()._fill(self.__twitter_username_field, text)

    def _send_text_to_community_portal_field(self, text: str):
        super()._fill(self.__community_portal_username_field, text)

    def _send_text_to_people_directory_username(self, text: str):
        super()._fill(self.__people_directory_username_field, text)

    def _send_text_to_matrix_nickname(self, text: str):
        self._page.locator(self.__matrix_nickname_field).fill(text)

    def _sent_text_to_city_field(self, text: str):
        super()._fill(self.__city_field, text)

    def _select_country_dropdown_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__country_dropdown, option_value)

    def _select_timezone_dropdown_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__timezone_dropdown, option_value)

    def _select_preferred_language_dropdown_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__preferred_locale_dropdown, option_value)

    def _select_involved_from_month_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__involved_with_mozilla_from_month, option_value)

    def _select_involved_from_year_option_by_value(self, option_value: str):
        super()._select_option_by_value(self.__involved_with_mozilla_from_year, option_value)

    def _clear_all_input_fields(self):
        for element in super()._get_element_handles(self.__all_input_edit_profile_input_fields):
            element.fill("")

    def _clear_biography_textarea_field(self):
        super()._clear_field(self.__biography_textarea_field)

    def _clear_username_field(self):
        super()._clear_field(self.__username_input_field)

    def _clear_display_name_field(self):
        super()._clear_field(self.__display_name_input_field)

    def _clear_website_field(self):
        super()._clear_field(self.__website_input_field)

    def _clear_twitter_field(self):
        super()._clear_field(self.__twitter_username_field)

    def _clear_community_portal_field(self):
        super()._clear_field(self.__community_portal_username_field)

    def _clear_people_directory_field(self):
        super()._clear_field(self.__people_directory_username_field)

    def _clear_matrix_field(self):
        super()._clear_field(self.__matrix_nickname_field)

    def _clear_country_dropdown_field(self):
        super()._select_option_by_value(self.__country_dropdown, "")

    def _clear_city_field(self):
        super()._clear_field(self.__city_field)

    def _clear_involved_from_month_select_field(self):
        super()._select_option_by_value(self.__involved_with_mozilla_from_month, "0")

    def _clear_involved_from_year_select_field(self):
        super()._select_option_by_value(self.__involved_with_mozilla_from_year, "0")

    def _click_cancel_button(self):
        super()._click(self.__cancel_button)

    def _click_update_my_profile_button(self):
        super()._click(self.__update_my_profile_button)

    def _click_close_account_option(self):
        super()._click(self.__close_account_and_delete_all_profile_information_link)

    def _click_manage_firefox_account_button(self):
        super()._click_without_wait(self.__manage_firefox_account_button)

    def _click_make_email_visible_checkbox(self):
        super()._click(self.__make_email_visible_to_logged_in_users_checkbox)

    def _is_make_email_visible_checkbox_selected(self) -> bool:
        return super()._is_checkbox_checked(self.__make_email_visible_to_logged_in_users_checkbox)

    def _is_my_profile_edit_form_displayed(self) -> Locator:
        return super()._get_element_locator(self.__edit_my_profile_edit_input_form)
