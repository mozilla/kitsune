from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileEdit(BasePage):
    # Access denied section
    ACCESS_DENIED_LOCATORS = {
        "access_denied_main_header": "//article[@id='error-page']/h1",
        "access_denied_subheading_message": "//div[@class='center-on-mobile']/p"
    }

    # Navbar section
    NAVBAR_LOCATORS = {
        "my_profile_user_navbar_options": "//ul[@id='user-nav']/li/a",
        "my_profile_user_navbar_selected_element": "//a[@class='selected']"
    }

    # Edit profile page
    EDIT_PROFILE_PAGE_LOCATORS = {
        "edit_my_profile_edit_input_form": "//article[@id='edit-profile']/form",
        "edit_my_profile_main_header": "//h1[@class='sumo-page-heading']",
        "manage_firefox_account_button": "//a[contains(text(),'Manage account')]",
        "username_input_field": "//input[@id='id_username']",
        "username_error_message": "//input[@id='id_username']/following-sibling::span[contains("
                                  "@class, 'form-error is-visible')]",
        "display_name_input_field": "//input[@id='id_name']",
        "biography_textarea_field": "//textarea[@id='id_bio']",
        "make_email_visible_to_logged_in_users_checkbox": "//label[@for='id_public_email']",
        "website_input_field": "//input[@id='id_website']",
        "twitter_username_field": "//input[@id='id_twitter']",
        "community_portal_username_field": "//input[@id='id_community_mozilla_org']",
        "people_directory_username_field": "//input[@id='id_people_mozilla_org']",
        "matrix_nickname_field": "//input[@id='id_matrix_handle']",
        "country_dropdown": "//select[@id='id_country']",
        "city_field": "//input[@id='id_city']",
        "timezone_dropdown": "#id_timezone",
        "preferred_locale_dropdown": "//select[@id='id_locale']",
        "involved_with_mozilla_from_month": "//select[@id='id_involved_from_month']",
        "involved_with_mozilla_from_year": "//select[@id='id_involved_from_year']",
        "cancel_button": "//button[contains(text(),'Cancel')]",
        "update_my_profile_button": "//button[contains(text(),'Update My Profile')]",
        "close_account_and_delete_all_profile_information_link": "//p[@class='delete-account-"
                                                                 "link']/a",
        "all_input_edit_profile_input_fields": "//form[not(contains(@action, "
                                               "'/en-US/users/close_account'))]/div["
                                               "@class='field']/input[not(contains(@id, "
                                               "'id_username'))]"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    def get_access_denied_header_text(self) -> str:
        """Return the text of the access denied header"""
        return self._get_text_of_element(self.ACCESS_DENIED_LOCATORS["access_denied_main_header"])

    def get_access_denied_subheading_text(self) -> str:
        """Return the text of the access denied subheading message"""
        return self._get_text_of_element(self.ACCESS_DENIED_LOCATORS["access_denied_subheading_"
                                                                     "message"])

    def get_value_of_all_input_fields(self) -> list[str]:
        """Return the value of all input fields"""
        elements = self._get_element_handles(
            self.EDIT_PROFILE_PAGE_LOCATORS["all_input_edit_profile_input_fields"])
        return [el.input_value() for el in elements]

    def get_timezone_select_value(self) -> str:
        """Return the selected value of the timezone dropdown"""
        return self._get_element_inner_text_from_page("#id_timezone [selected]")

    def get_preferred_locale_select_value(self) -> str:
        """Return the selected value of the preferred locale dropdown"""
        return self._get_element_inner_text_from_page('#id_locale [selected]')

    def get_involved_with_mozilla_month_select_value(self) -> str:
        """Return the selected value of the involved with mozilla month dropdown"""
        return self._get_text_of_element(self.EDIT_PROFILE_PAGE_LOCATORS["involved_with_mozilla_"
                                                                         "from_month"])

    def get_involved_with_mozilla_year_select_value(self) -> str:
        """Return the selected value of the involved with mozilla year dropdown"""
        return self._get_text_of_element(self.EDIT_PROFILE_PAGE_LOCATORS["involved_with_mozilla_"
                                                                         "from_year"])

    def get_value_of_all_fields(self) -> list[str]:
        """Return the value of all fields"""
        return [
            self.get_value_of_all_input_fields(),
            self.get_timezone_select_value(),
            self.get_preferred_locale_select_value(),
            self.get_involved_with_mozilla_month_select_value(),
            self.get_involved_with_mozilla_year_select_value(),
        ]

    def get_username_input_field_value(self) -> str:
        """Return the value of the username input field"""
        return self._get_element_input_value(self.EDIT_PROFILE_PAGE_LOCATORS["username_input_"
                                                                             "field"])

    def get_username_error_message_text(self) -> str:
        """Return the text of the username error message"""
        return self._get_text_of_element(self.EDIT_PROFILE_PAGE_LOCATORS["username_error_message"])

    def get_display_name_input_field_value(self) -> str:
        """Return the value of the display name input field"""
        return self._get_element_input_value(self.EDIT_PROFILE_PAGE_LOCATORS["display_name_input_"
                                                                             "field"])

    def get_website_input_field_value(self) -> str:
        """Return the value of the website input field"""
        return self._get_element_input_value(self.EDIT_PROFILE_PAGE_LOCATORS["website_input_"
                                                                             "field"])

    def get_twitter_input_field_value(self) -> str:
        """Return the value of the twitter input field"""
        return self._get_element_input_value(self.EDIT_PROFILE_PAGE_LOCATORS["twitter_username_"
                                                                             "field"])

    def get_community_portal_field_value(self) -> str:
        """Return the value of the community portal input field"""
        return self._get_element_input_value(self.EDIT_PROFILE_PAGE_LOCATORS["community_portal_"
                                                                             "username_field"])

    def get_people_directory_field_value(self) -> str:
        """Return the value of the people directory input field"""
        return self._get_element_input_value(self.EDIT_PROFILE_PAGE_LOCATORS["people_directory_"
                                                                             "username_field"])

    def get_matrix_username_field_value(self) -> str:
        """Return the value of the matrix nickname input field"""
        return self._get_element_input_value(self.EDIT_PROFILE_PAGE_LOCATORS["matrix_nickname_"
                                                                             "field"])

    def get_city_field_value(self) -> str:
        """Return the value of the city input field"""
        return self._get_element_input_value(self.EDIT_PROFILE_PAGE_LOCATORS["city_field"])

    def send_text_to_username_field(self, text: str):
        """Send text to the username input field"""
        self._fill(self.EDIT_PROFILE_PAGE_LOCATORS["username_input_field"], text)

    def send_text_to_display_name_field(self, text: str):
        """Send text to the display name input field"""
        self._fill(self.EDIT_PROFILE_PAGE_LOCATORS["display_name_input_field"], text)

    def send_text_to_biography_field(self, text: str):
        """Send text to the biography textarea field"""
        self._fill(self.EDIT_PROFILE_PAGE_LOCATORS["biography_textarea_field"], text)

    def send_text_to_website_field(self, text: str):
        """Send text to the website input field"""
        self._fill(self.EDIT_PROFILE_PAGE_LOCATORS["website_input_field"], text)

    def send_text_to_twitter_username_field(self, text: str):
        """Send text to the twitter input field"""
        self._fill(self.EDIT_PROFILE_PAGE_LOCATORS["twitter_username_field"], text)

    def send_text_to_community_portal_field(self, text: str):
        """Send text to the community portal input field"""
        self._fill(self.EDIT_PROFILE_PAGE_LOCATORS["community_portal_username_field"], text)

    def send_text_to_people_directory_username(self, text: str):
        """Send text to the people directory input field"""
        self._fill(self.EDIT_PROFILE_PAGE_LOCATORS["people_directory_username_field"], text)

    def send_text_to_matrix_nickname(self, text: str):
        """Send text to the matrix nickname input field"""
        self.page.locator(self.EDIT_PROFILE_PAGE_LOCATORS["matrix_nickname_field"]).fill(text)

    def sent_text_to_city_field(self, text: str):
        """Send text to the city input field"""
        self._fill(self.EDIT_PROFILE_PAGE_LOCATORS["city_field"], text)

    def select_country_dropdown_option_by_value(self, option_value: str):
        """Select an option from the country dropdown"""
        self._select_option_by_value(self.EDIT_PROFILE_PAGE_LOCATORS["country_dropdown"],
                                     option_value)

    def select_timezone_dropdown_option_by_value(self, option_value: str):
        """Select an option from the timezone dropdown"""
        self._select_option_by_value(self.EDIT_PROFILE_PAGE_LOCATORS["timezone_dropdown"],
                                     option_value)

    def select_preferred_language_dropdown_option_by_value(self, option_value: str):
        """Select an option from the preferred locale dropdown"""
        self._select_option_by_value(self.EDIT_PROFILE_PAGE_LOCATORS["preferred_locale_dropdown"],
                                     option_value)

    def select_involved_from_month_option_by_value(self, option_value: str):
        """Select an option from the involved with mozilla month dropdown"""
        self._select_option_by_value(self.EDIT_PROFILE_PAGE_LOCATORS["involved_with_mozilla_"
                                                                     "from_month"], option_value)

    def select_involved_from_year_option_by_value(self, option_value: str):
        """Select an option from the involved with mozilla year dropdown"""
        self._select_option_by_value(self.EDIT_PROFILE_PAGE_LOCATORS["involved_with_mozilla_"
                                                                     "from_year"], option_value)

    def clear_all_input_fields(self, only_profile_info=False):
        """Clear all input fields

        Args:
            only_profile_info (bool): Clear only the profile info fields ignoring the username and
                display name fields
        """
        for input_element in self._get_element_handles(
                self.EDIT_PROFILE_PAGE_LOCATORS["all_input_edit_profile_input_fields"]):
            if only_profile_info:
                element_id = self._get_element_attribute_value(input_element, "id")
                if element_id == "id_username" or element_id == "id_name":
                    continue
            input_element.fill("")

    def clear_biography_textarea_field(self):
        """Clear the biography textarea field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["biography_textarea_field"])

    def clear_username_field(self):
        """Clear the username input field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["username_input_field"])

    def clear_display_name_field(self):
        """Clear the display name input field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["display_name_input_field"])

    def clear_website_field(self):
        """Clear the website input field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["website_input_field"])

    def clear_twitter_field(self):
        """Clear the twitter input field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["twitter_username_field"])

    def clear_community_portal_field(self):
        """Clear the community portal input field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["community_portal_username_field"])

    def clear_people_directory_field(self):
        """Clear the people directory input field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["people_directory_username_field"])

    def clear_matrix_field(self):
        """Clear the matrix nickname input field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["matrix_nickname_field"])

    def clear_country_dropdown_field(self):
        """Clear the country dropdown field"""
        self._select_option_by_value(self.EDIT_PROFILE_PAGE_LOCATORS["country_dropdown"], "")

    def clear_city_field(self):
        """Clear the city input field"""
        self._clear_field(self.EDIT_PROFILE_PAGE_LOCATORS["city_field"])

    def clear_involved_from_month_select_field(self):
        """Clear the involved with mozilla month dropdown"""
        self._select_option_by_value(self.EDIT_PROFILE_PAGE_LOCATORS["involved_with_mozilla_"
                                                                     "from_month"], "0")

    def clear_involved_from_year_select_field(self):
        """Clear the involved with mozilla year dropdown"""
        self._select_option_by_value(self.EDIT_PROFILE_PAGE_LOCATORS["involved_with_mozilla_"
                                                                     "from_year"], "0")

    def click_cancel_button(self):
        """Click the cancel button"""
        self._click(self.EDIT_PROFILE_PAGE_LOCATORS["cancel_button"])

    def click_update_my_profile_button(self, expected_url=None, expected_locator=None):
        """Click the update my profile button"""
        self._click(self.EDIT_PROFILE_PAGE_LOCATORS["update_my_profile_button"],
                    expected_url=expected_url, expected_locator=expected_locator)

    def click_close_account_option(self):
        """Click the close account and delete all profile information link"""
        self._click(self.EDIT_PROFILE_PAGE_LOCATORS["close_account_and_delete_all_profile_"
                                                    "information_link"])

    def click_manage_firefox_account_button(self):
        """Click the manage firefox account button"""
        self._click(self.EDIT_PROFILE_PAGE_LOCATORS["manage_firefox_account_button"])

    def click_make_email_visible_checkbox(self, check: bool):
        """Click the make email visible checkbox"""
        self._checkbox_interaction(self.EDIT_PROFILE_PAGE_LOCATORS["make_email_visible_to_logged_"
                                                                   "in_users_checkbox"], check)

    def is_make_email_visible_checkbox_selected(self) -> bool:
        """Return True if the make email visible checkbox is selected"""
        return self._is_checkbox_checked(
            self.EDIT_PROFILE_PAGE_LOCATORS["make_email_visible_to_logged_in_users_checkbox"])

    def get_my_profile_edit_form_locator(self) -> Locator:
        """Return the locator of the edit profile form"""
        return self._get_element_locator(self.EDIT_PROFILE_PAGE_LOCATORS["edit_my_profile_edit_"
                                                                         "input_form"])
