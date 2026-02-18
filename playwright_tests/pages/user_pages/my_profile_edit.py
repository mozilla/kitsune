import re
from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MyProfileEdit(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the Access Denied section."""
        self.access_denied_main_header = page.locator("article#error-page h1")
        self.access_denied_subheading_message = page.locator("div[class='center-on-mobile'] p")

        """Locators belonging to the navbar section."""
        self.my_profile_user_navbar_options = page.locator("ul#user-nav li a")
        self.my_profile_user_navbar_selected_element = page.locator("a[class='selected']")

        """Locators belonging to the edit profile page."""
        self.edit_my_profile_edit_input_form = page.locator("article#edit-profile form")
        self.edit_my_profile_main_header = page.locator("h1[class='sumo-page-heading']")
        self.manage_firefox_account_button = page.get_by_role("link").filter(
            has_text="Manage account")
        self.username_input_field = page.locator("input#id_username")
        self.username_error_message = page.locator(
            "//input[@id='id_username']/following-sibling::span[contains(@class, 'form-error "
            "is-visible')]")
        self.display_name_input_field = page.locator("input#id_name")
        self.biography_textarea_field = page.locator("textarea#id_bio")
        self.make_email_visible_to_logged_in_users_checkbox = page.locator(
            "label[for='id_public_email']")
        self.website_input_field = page.locator("input#id_website")
        self.twitter_username_field = page.locator("input#id_twitter")
        self.community_portal_username_field = page.locator("input#id_community_mozilla_org")
        self.people_directory_username_field = page.locator("input#id_people_mozilla_org")
        self.matrix_nickname_field = page.locator("input#id_matrix_handle")
        self.country_dropdown = page.locator("select#id_country")
        self.city_field = page.locator("input#id_city")
        self.timezone_dropdown = page.locator("select#id_timezone")
        self.selected_timezone = page.locator("select#id_timezone option[selected]")
        self.preferred_locale_dropdown = page.locator("select#id_locale")
        self.selected_locale = page.locator("select#id_locale option[selected]")
        self.involved_with_mozilla_from_month = page.locator("select#id_involved_from_month")
        self.involved_with_mozilla_from_year = page.locator("select#id_involved_from_year")
        self.cancel_button = page.get_by_role("button").filter(has_text="Cancel")
        self.update_my_profile_button = page.get_by_role("button").filter(
            has_text="Update My Profile")

        """Locators belonging to the close account modal."""
        self.close_account_and_delete_all_profile_information_link = page.locator(
            "p.delete-account-link a")
        self.close_account_username_modal = page.locator("input#delete-profile-confirmation-input")
        self.close_account_username_modal_confirmation_code = page.locator(
            "//div[@id='delete-profile']//strong")
        self.close_account_delete_button = page.locator("button#delete-profile-button")
        self.close_modal_button = page.locator("button[class='mzp-c-modal-button-close']")

        self.all_input_edit_profile_input_fields = page.locator(
            "//form[not(contains(@action, '/en-US/users/close_account'))]/div[@class='field']/"
            "input[not(contains(@id, 'id_username'))]"
        )

    def get_access_denied_header_text(self) -> str:
        """Return the text of the access denied header"""
        return self._get_text_of_element(self.access_denied_main_header)

    def get_access_denied_subheading_text(self) -> str:
        """Return the text of the access denied subheading message"""
        return self._get_text_of_element(self.access_denied_subheading_message)

    def get_value_of_all_input_fields(self) -> list[str]:
        """Return the value of all input fields"""
        elements = self._get_element_handles(self.all_input_edit_profile_input_fields)
        return [el.input_value() for el in elements]

    def get_timezone_select_value(self) -> str:
        """Return the selected value of the timezone dropdown"""
        return self._get_text_of_element(self.selected_timezone)

    def get_preferred_locale_select_value(self) -> str:
        """Return the selected value of the preferred locale dropdown"""
        return self._get_text_of_element(self.selected_locale)

    def get_involved_with_mozilla_month_select_value(self) -> str:
        """Return the selected value of the involved with mozilla month dropdown"""
        return self._get_text_of_element(self.involved_with_mozilla_from_month)

    def get_involved_with_mozilla_year_select_value(self) -> str:
        """Return the selected value of the involved with mozilla year dropdown"""
        return self._get_text_of_element(self.involved_with_mozilla_from_year)

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
        return self._get_element_input_value(self.username_input_field)

    def get_username_error_message_text(self) -> str:
        """Return the text of the username error message"""
        return self._get_text_of_element(self.username_error_message)

    def get_display_name_input_field_value(self) -> str:
        """Return the value of the display name input field"""
        return self._get_element_input_value(self.display_name_input_field)

    def get_website_input_field_value(self) -> str:
        """Return the value of the website input field"""
        return self._get_element_input_value(self.website_input_field)

    def get_twitter_input_field_value(self) -> str:
        """Return the value of the twitter input field"""
        return self._get_element_input_value(self.twitter_username_field)

    def get_community_portal_field_value(self) -> str:
        """Return the value of the community portal input field"""
        return self._get_element_input_value(self.community_portal_username_field)

    def get_people_directory_field_value(self) -> str:
        """Return the value of the people directory input field"""
        return self._get_element_input_value(self.people_directory_username_field)

    def get_matrix_username_field_value(self) -> str:
        """Return the value of the matrix nickname input field"""
        return self._get_element_input_value(self.matrix_nickname_field)

    def get_city_field_value(self) -> str:
        """Return the value of the city input field"""
        return self._get_element_input_value(self.city_field)

    def send_text_to_username_field(self, text: str):
        """Send text to the username input field"""
        self._fill(self.username_input_field, text)

    def send_text_to_display_name_field(self, text: str):
        """Send text to the display name input field"""
        self._fill(self.display_name_input_field, text)

    def send_text_to_biography_field(self, text: str):
        """Send text to the biography textarea field"""
        self._fill(self.biography_textarea_field, text)

    def send_text_to_website_field(self, text: str):
        """Send text to the website input field"""
        self._fill(self.website_input_field, text)

    def send_text_to_twitter_username_field(self, text: str):
        """Send text to the twitter input field"""
        self._fill(self.twitter_username_field, text)

    def send_text_to_community_portal_field(self, text: str):
        """Send text to the community portal input field"""
        self._fill(self.community_portal_username_field, text)

    def send_text_to_people_directory_username(self, text: str):
        """Send text to the people directory input field"""
        self._fill(self.people_directory_username_field, text)

    def send_text_to_matrix_nickname(self, text: str):
        """Send text to the matrix nickname input field"""
        self.matrix_nickname_field.fill(text)

    def sent_text_to_city_field(self, text: str):
        """Send text to the city input field"""
        self._fill(self.city_field, text)

    def select_country_dropdown_option_by_value(self, option_value: str):
        """Select an option from the country dropdown"""
        self._select_option_by_value(self.country_dropdown, option_value)

    def select_timezone_dropdown_option_by_value(self, option_value: str):
        """Select an option from the timezone dropdown"""
        self._select_option_by_value(self.timezone_dropdown, option_value)

    def select_preferred_language_dropdown_option_by_value(self, option_value: str):
        """Select an option from the preferred locale dropdown"""
        self._select_option_by_value(self.preferred_locale_dropdown, option_value)

    def select_involved_from_month_option_by_value(self, option_value: str):
        """Select an option from the involved with mozilla month dropdown"""
        self._select_option_by_value(self.involved_with_mozilla_from_month, option_value)

    def select_involved_from_year_option_by_value(self, option_value: str):
        """Select an option from the involved with mozilla year dropdown"""
        self._select_option_by_value(self.involved_with_mozilla_from_year, option_value)

    def clear_all_input_fields(self, only_profile_info=False):
        """Clear all input fields

        Args:
            only_profile_info (bool): Clear only the profile info fields ignoring the username and
                display name fields
        """
        for input_element in self._get_element_handles(self.all_input_edit_profile_input_fields):
            if only_profile_info:
                element_id = self._get_element_attribute_value(input_element, "id")
                if element_id == "id_username" or element_id == "id_name":
                    continue
            input_element.fill("")

    def clear_biography_textarea_field(self):
        """Clear the biography textarea field"""
        self._clear_field(self.biography_textarea_field)

    def clear_username_field(self):
        """Clear the username input field"""
        self._clear_field(self.username_input_field)

    def clear_display_name_field(self):
        """Clear the display name input field"""
        self._clear_field(self.display_name_input_field)

    def clear_website_field(self):
        """Clear the website input field"""
        self._clear_field(self.website_input_field)

    def clear_twitter_field(self):
        """Clear the twitter input field"""
        self._clear_field(self.twitter_username_field)

    def clear_community_portal_field(self):
        """Clear the community portal input field"""
        self._clear_field(self.community_portal_username_field)

    def clear_people_directory_field(self):
        """Clear the people directory input field"""
        self._clear_field(self.people_directory_username_field)

    def clear_matrix_field(self):
        """Clear the matrix nickname input field"""
        self._clear_field(self.matrix_nickname_field)

    def clear_country_dropdown_field(self):
        """Clear the country dropdown field"""
        self._select_option_by_value(self.country_dropdown, "")

    def clear_city_field(self):
        """Clear the city input field"""
        self._clear_field(self.city_field)

    def clear_involved_from_month_select_field(self):
        """Clear the involved with mozilla month dropdown"""
        self._select_option_by_value(self.involved_with_mozilla_from_month, "0")

    def clear_involved_from_year_select_field(self):
        """Clear the involved with mozilla year dropdown"""
        self._select_option_by_value(self.involved_with_mozilla_from_year, "0")

    def click_cancel_button(self):
        """Click the cancel button"""
        self._click(self.cancel_button)

    def click_update_my_profile_button(self, expected_url=None, expected_locator=None):
        """Click the update my profile button"""
        self._click(self.update_my_profile_button, expected_url=expected_url,
                    expected_locator=expected_locator)

    def click_close_account_option(self):
        """Click the close account and delete all profile information link"""
        self._click(self.close_account_and_delete_all_profile_information_link)

    def add_confirmation_code_to_close_account_modal(self, invalid_code=False):
        """
        Add the confirmation code to the close account modal.
            Args:
                invalid_code (bool): If set to true to be used in tests which are covering the
                submission of an invalid code inside the user deletion modal.
        """
        self._wait_for_given_timeout(1000)
        code = self._get_text_of_element(self.close_account_username_modal_confirmation_code)
        if invalid_code:
            code += "A"

        self._type(self.close_account_username_modal, code, 10)

    def clear_confirmation_code_from_close_account_modal(self):
        """Clearing the confirmation code from the close account modal"""
        self._clear_field(self.close_account_username_modal)

    def click_close_account_button(self):
        """Click the close account button in the close account modal"""
        self._click(self.close_account_delete_button, expected_url=re.compile(r"close_account$"),
                    retries=2)

    def is_delete_your_account_button_disabled(self) -> bool:
        """Returning whether the 'Delete Your Account' button is disabled or not."""
        return self._is_element_disabled(self.close_account_delete_button)

    def click_on_close_modal_button(self):
        """Clicking on the 'X' button from the close account modal"""
        self._click(self.close_modal_button)

    def click_manage_firefox_account_button(self):
        """Click the manage firefox account button"""
        self._click(self.manage_firefox_account_button)

    def click_make_email_visible_checkbox(self, check: bool):
        """Click the make email visible checkbox"""
        self._checkbox_interaction(self.make_email_visible_to_logged_in_users_checkbox, check)

    def is_make_email_visible_checkbox_selected(self) -> bool:
        """Return True if the make email visible checkbox is selected"""
        return self._is_checkbox_checked(self.make_email_visible_to_logged_in_users_checkbox)
