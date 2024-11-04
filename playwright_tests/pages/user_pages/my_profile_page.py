from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage


class MyProfilePage(BasePage):
    # Sidebar locators
    SIDEBAR_LOCATORS = {
        "user_navbar_options": "//ul[@id='user-nav']/li/a",
        "user_navbar_selected_element": "//a[@class='selected']"
    }

    # Admin/other user actions locators
    ADMIN_ACTIONS_LOCATORS = {
        "edit_user_profile_option": "//div[@id='admin-actions']/a[contains(text(), "
                                    "'Edit user profile')]",
        "report_abuse_profile_option": "//article[@id='profile']/a[contains(text(), "
                                       "'Report Abuse')]",
        "deactivate_this_user_button": "//input[@value='Deactivate this user']",
        "deactivate_this_user_and_mark_all_content_as_spam": "//input[@value='Deactivate this "
                                                             "user and mark all content as spam']",
        "private_message_button": "//p[@class='pm']/a"
    }

    # Report Abuse locators
    REPORT_ABUSE_LOCATORS = {
        "report_abuse_panel": "//section[@id='report-abuse-']",
        "spam_or_other_unrelated_content_option": "//label[contains(text(),'Spam or other "
                                                  "unrelated content')]",
        "inappropriate_language_or_dialog_option": "//label[contains(text(),'Inappropriate "
                                                   "language/dialog')]",
        "other_please_specify_option": "//label[contains(text(),'Other (please specify)')]",
        "have_more_to_say_textarea": "//textarea[@name='other']",
        "report_abuse_close_panel_button": "//div[@class='mzp-c-modal-close']/button",
        "report_abuse_submit_button": "//section[@id='report-abuse-']//button[@type='submit']",
        "reported_user_confirmation_message": "//span[@class='message']"
    }

    # Contributions section locators
    CONTRIBUTIONS_LOCATORS = {
        "questions_link": "//section[@class='contributions']//a[contains(text(), 'question')]",
        "answers_link": "//section[@class='contributions']//a[contains(text(), 'answer')]",
        "provided_solutions_text": "//section[@class='contributions']//li[contains(text(),"
                                   "'solution')]",
        "provided_documents_link": "//section[@class='contributions']//a[contains(text(),"
                                   "'document')]"
    }

    # My Profile page details locators
    PROFILE_DETAILS_LOCATORS = {
        "page_header": "//h1[@class='sumo-page-heading']",
        "page_subheading": "//article[@id='profile']/h2[contains(@class, 'sumo-page-subheading')]",
        "email_address": "//p/strong",
        "displayed_email_address": "//li[@class='avatar-group--details-item']/span[@class='email']"
                                   "/a",
        "sign_out_button": "//article[@id='profile']//a[contains(text(), 'Sign Out')]",
        "display_name_header": "//h2[@class='sumo-callout-heading user']",
        "username_info": "//span[@class='username']",
        "location_info": "//h2[contains(@class,'location')]",
        "website_info": "//label[contains(text(), 'Website')]/following-sibling::a",
        "twitter_info": "//label[contains(text(), 'Twitter')]/following-sibling::a",
        "community_portal_info": "//label[contains(text(), 'Community Portal')]/following-sibling"
                                 "::a",
        "people_directory_info": "//label[contains(text(), 'People Directory')]/following-sibling"
                                 "::a",
        "matrix_info": "//label[contains(text(),'Matrix')]/parent::li",
        "contributed_from_info": "//section[@class='contributions']//li[1]",
        "bio_info": "//section[@class='bio']/p",
        "groups_section": "//section[@class='groups']",
        "groups_heading": "//section[@class='groups']/h2",
        "groups_list_items": "//section[@class='groups']/ul/li"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # My profile page actions.
    def get_my_profile_display_name_header_text(self) -> str:
        """Get the display name header text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["display_name_header"])

    def get_my_profile_display_name_username_text(self) -> str:
        """Get the display name username text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["username_info"])

    def get_my_profile_location_text(self) -> str:
        """Get the location text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["location_info"])

    def get_my_profile_website_text(self) -> str:
        """Get the website text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["website_info"])

    def get_my_profile_twitter_text(self) -> str:
        """Get the Twitter text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["twitter_info"])

    def get_my_profile_community_portal_text(self) -> str:
        """Get the community portal text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["community_portal_info"])

    def get_my_profile_people_directory_text(self) -> str:
        """Get the people directory text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["people_directory_info"])

    def get_my_profile_matrix_text(self) -> str:
        """Get the Matrix text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["matrix_info"])

    def get_my_contributed_from_text(self) -> str:
        """Get the contributed from text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["contributed_from_info"])

    def get_my_profile_bio_text(self) -> str:
        """Get the bio text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["bio_info"])

    def get_my_profile_page_header(self) -> str:
        """Get the profile page header."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["page_header"])

    def get_my_profile_email_information(self) -> str:
        """Get the email information."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["email_address"])

    def get_text_of_selected_navbar_option(self) -> str:
        """Get the text of the selected navbar option."""
        return self._get_text_of_element(self.SIDEBAR_LOCATORS["user_navbar_selected_element"])

    def get_navbar_menu_options(self) -> list[ElementHandle]:
        """Get the navbar menu options."""
        return self._get_element_handles(self.SIDEBAR_LOCATORS["user_navbar_options"])

    def get_text_of_all_navbar_menu_options(self) -> list[str]:
        """Get the text of all navbar menu options."""
        return self._get_text_of_elements(self.SIDEBAR_LOCATORS["user_navbar_options"])

    def get_text_of_publicly_displayed_username(self) -> str:
        """Get the text of the publicly displayed username."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["displayed_email_address"])

    def get_text_of_profile_subheading_location(self) -> str:
        """Get the text of the profile subheading location."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["page_subheading"])

    def get_my_profile_questions_text(self) -> str:
        """Get the profile questions text."""
        return self._get_text_of_element(self.CONTRIBUTIONS_LOCATORS["questions_link"])

    def is_question_displayed(self) -> bool:
        """Check if the question is displayed."""
        return self._is_element_visible(self.CONTRIBUTIONS_LOCATORS["questions_link"])

    def get_my_profile_solutions_text(self) -> str:
        """Get the profile solutions text."""
        return self._get_text_of_element(self.CONTRIBUTIONS_LOCATORS["provided_solutions_text"])

    def is_solutions_displayed(self) -> bool:
        """Check if the solutions are displayed."""
        return self._is_element_visible(self.CONTRIBUTIONS_LOCATORS["provided_solutions_text"])

    def get_my_profile_documents_text(self) -> str:
        """Get the profile documents text."""
        return self._get_text_of_element(self.CONTRIBUTIONS_LOCATORS["provided_documents_link"])

    def get_my_profile_answers_text(self) -> str:
        """Get the profile answers text."""
        return self._get_text_of_element(self.CONTRIBUTIONS_LOCATORS["answers_link"])

    def get_my_profile_groups_heading_text(self) -> str:
        """Get the profile groups heading text."""
        return self._get_text_of_element(self.PROFILE_DETAILS_LOCATORS["groups_heading"])

    def get_my_profile_groups_items_text(self) -> set[str]:
        """Get the profile groups items text."""
        return set(self._get_text_of_elements(self.PROFILE_DETAILS_LOCATORS["groups_list_items"]))

    def click_on_edit_user_profile_button(self):
        """Click on the edit user profile button."""
        self._click(self.ADMIN_ACTIONS_LOCATORS["edit_user_profile_option"])

    def click_my_profile_answers_link(self):
        """Click on the profile answers link."""
        self._click(self.CONTRIBUTIONS_LOCATORS["answers_link"])

    def click_on_my_profile_questions_link(self):
        """Click on the profile questions link."""
        self._click(self.CONTRIBUTIONS_LOCATORS["questions_link"])

    def click_on_my_profile_document_link(self):
        """Click on the profile document link."""
        self._click(self.CONTRIBUTIONS_LOCATORS["provided_documents_link"])

    def click_on_my_website_link(self):
        """Click on the website link."""
        self._click(self.PROFILE_DETAILS_LOCATORS["website_info"])

    def click_on_twitter_link(self):
        """Click on the Twitter link."""
        self._click(self.PROFILE_DETAILS_LOCATORS["twitter_info"])

    def click_on_community_portal_link(self):
        """Click on the community portal link."""
        self._click(self.PROFILE_DETAILS_LOCATORS["community_portal_info"])

    def click_on_people_directory_link(self):
        """Click on the people directory link."""
        self._click(self.PROFILE_DETAILS_LOCATORS["people_directory_info"])

    def click_on_element(self, element: ElementHandle):
        """Click on the given element."""
        element.click()

    def click_my_profile_page_sign_out_button(self, expected_url=None):
        """Click on the profile page sign out button.

        Args:
            expected_url (str): The expected URL after clicking the sign out button
        """
        self._click(self.PROFILE_DETAILS_LOCATORS["sign_out_button"], expected_url=expected_url)

    def click_on_report_abuse_option(self):
        """Click on the report abuse option."""
        self._click(self.ADMIN_ACTIONS_LOCATORS["report_abuse_profile_option"])

    def click_on_report_abuse_close_button(self):
        """Click on the report abuse close button."""
        self._click(self.REPORT_ABUSE_LOCATORS["report_abuse_close_panel_button"])

    def click_on_private_message_button(self, expected_url=None):
        """Click on the private message button.

        Args:
            expected_url (str): The expected URL after clicking the private message button.
        """
        self._click(self.ADMIN_ACTIONS_LOCATORS["private_message_button"],
                    expected_url=expected_url)

    def publicly_displayed_email_element(self) -> Locator:
        """Get the locator for the publicly displayed email element."""
        return self._get_element_locator(self.PROFILE_DETAILS_LOCATORS["displayed_email_address"])

    def is_website_information_displayed(self) -> bool:
        """Check if the website information is displayed."""
        return self._is_element_visible(self.PROFILE_DETAILS_LOCATORS["website_info"])

    def groups_section_element(self) -> Locator:
        """Get the locator for the groups section."""
        return self._get_element_locator(self.PROFILE_DETAILS_LOCATORS["groups_section"])

    def edit_user_profile_option_element(self) -> Locator:
        """Get the locator for the edit user profile option."""
        return self._get_element_locator(self.ADMIN_ACTIONS_LOCATORS["edit_user_profile_option"])

    def is_report_user_option_displayed(self) -> Locator:
        """Get the locator for the report user option."""
        return self._get_element_locator(self.ADMIN_ACTIONS_LOCATORS["report_abuse_profile_"
                                                                     "option"])

    def is_report_abuse_panel_displayed(self) -> Locator:
        """Get the locator for the report abuse panel."""
        return self._get_element_locator(self.REPORT_ABUSE_LOCATORS["report_abuse_panel"])

    def is_deactivate_this_user_button_displayed(self) -> Locator:
        """Get the locator for the deactivate this user button."""
        return self._get_element_locator(
            self.ADMIN_ACTIONS_LOCATORS["deactivate_this_user_button"])

    def deactivate_user_and_mark_content_as_spam_button(self) -> Locator:
        """Get the locator for the deactivate user and mark content as spam button."""
        return self._get_element_locator(
            self.ADMIN_ACTIONS_LOCATORS["deactivate_this_user_and_mark_all_content_as_spam"])
