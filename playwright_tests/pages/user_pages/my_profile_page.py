from playwright.sync_api import ElementHandle, Locator, Page

from playwright_tests.core.basepage import BasePage


class MyProfilePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Sidebar locators
        self.user_navbar_options = page.locator("ul#user-nav li a")
        self.user_navbar_selected_element = page.locator("a.selected")

        # Admin/other user actions locators
        self.edit_user_profile_option = page.locator("div#admin-actions").get_by_role(
            "link").filter(has_text="Edit user profile")
        self.report_abuse_profile_option = page.locator("article#profile").get_by_role(
            "link").filter(has_text="Report Abuse")
        self.deactivate_this_user_button = page.locator("input[value='Deactivate this user']")
        self.deactivate_this_user_and_mark_all_content_as_spam = page.locator(
            "input[value='Deactivate this user and mark all content as spam']")
        self.private_message_button = page.locator("p.pm").get_by_role("link")

        # Report Abuse locators
        self.report_abuse_panel = page.locator("section#report-abuse-")
        self.spam_or_other_unrelated_content_option = page.locator("label").filter(
            has_text="Spam or other unrelated content")
        self.inappropriate_language_or_dialog_option = page.locator("label").filter(
            has_text="Inappropriate language/dialog")
        self.other_please_specify_option = page.locator("label").filter(
            has_text="Other (please specify)")
        self.have_more_to_say_textarea = page.locator("textarea[name='other']")
        self.report_abuse_close_panel_button = page.locator(
            "div[class='mzp-c-modal-close'] button")
        self.report_abuse_submit_button = page.locator(
            "section#report-abuse- button[type='submit']")
        self.reported_user_confirmation_message = page.locator("span[class='message']")

        # Contributions section locators
        self.questions_link = page.locator("section[class='contributions']").get_by_role(
            "link").filter(has_text="question")
        self.answers_link = page.locator("section[class='contributions']").get_by_role(
            "link").filter(has_text="answer")
        self.provided_solutions_text = page.locator("section[class='contributions']").get_by_role(
            "listitem").filter(has_text="solution")
        self.provided_documents_link = page.locator("section[class='contributions']").get_by_role(
            "link").filter(has_text="document")

        # My Profile page details locators
        self.page_header = page.locator("h1[class='sumo-page-heading']")
        self.page_subheading = page.locator("article#profile h2[class*='sumo-page-subheading']")
        self.email_address = page.locator("p strong")
        self.displayed_email_address = page.locator(
            "li[class='avatar-group--details-item'] span[class='email'] a")
        self.sign_out_button = page.locator("article#profile").get_by_role("link").filter(
            has_text="Sign Out")
        self.display_name_header = page.locator("h2[class='sumo-callout-heading user']")
        self.display_name_by_username = lambda username: page.get_by_role(
            "heading", name=username, exact=True)
        self.username_info = page.locator("span[class='username']")
        self.location_info = page.locator("h2[class*='location']")
        self.website_info = page.locator(
            "//label[contains(text(), 'Website')]/following-sibling::a")
        self.twitter_info = page.locator(
            "//label[contains(text(), 'Twitter')]/following-sibling::a")
        self.community_portal_info = page.locator(
            "//label[contains(text(), 'Community Portal')]/following-sibling::a")
        self.people_directory_info = page.locator(
            "//label[contains(text(), 'People Directory')]/following-sibling::a")
        self.matrix_info = page.locator("//label[contains(text(),'Matrix')]/parent::li")
        self.contributed_from_info = page.locator("//section[@class='contributions']//li[1]")
        self.bio_info = page.locator("section[class='bio'] p")
        self.groups_section = page.locator("section[class='groups']")
        self.groups_heading = page.locator("section[class='groups'] h2")
        self.groups_list_items = page.locator("section[class='groups'] ul li")
        self.group_by_name = lambda group_name: page.locator(
            "section[class='groups']").get_by_role("link", name=group_name, exact=True)

    # My profile page actions.
    def get_my_profile_display_name_header_text(self) -> str:
        """Get the display name header text."""
        return self._get_text_of_element(self.display_name_header)

    def get_expected_header_locator(self, expected_username: str) -> Locator:
        """Get the expected header locator.

        Args:
            expected_username (str): The expected username
        """
        return self.display_name_by_username(expected_username)

    def get_my_profile_display_name_username_text(self) -> str:
        """Get the display name username text."""
        return self._get_text_of_element(self.username_info)

    def get_my_profile_location_text(self) -> str:
        """Get the location text."""
        return self._get_text_of_element(self.location_info)

    def get_my_profile_website_text(self) -> str:
        """Get the website text."""
        return self._get_text_of_element(self.website_info)

    def get_my_profile_twitter_text(self) -> str:
        """Get the Twitter text."""
        return self._get_text_of_element(self.twitter_info)

    def get_my_profile_community_portal_text(self) -> str:
        """Get the community portal text."""
        return self._get_text_of_element(self.community_portal_info)

    def get_my_profile_people_directory_text(self) -> str:
        """Get the people directory text."""
        return self._get_text_of_element(self.people_directory_info)

    def get_my_profile_matrix_text(self) -> str:
        """Get the Matrix text."""
        return self._get_text_of_element(self.matrix_info)

    def get_my_contributed_from_text(self) -> str:
        """Get the contributed from text."""
        return self._get_text_of_element(self.contributed_from_info)

    def get_my_profile_bio_text_paragraphs(self) -> list[str]:
        """Get the bio text."""
        return self._get_text_of_elements(self.bio_info)

    def get_my_profile_page_header(self) -> str:
        """Get the profile page header."""
        return self._get_text_of_element(self.page_header)

    def get_my_profile_email_information(self) -> str:
        """Get the email information."""
        return self._get_text_of_element(self.email_address)

    def get_text_of_selected_navbar_option(self) -> str:
        """Get the text of the selected navbar option."""
        return self._get_text_of_element(self.user_navbar_selected_element)

    def get_navbar_menu_options(self) -> list[ElementHandle]:
        """Get the navbar menu options."""
        return self._get_element_handles(self.user_navbar_options)

    def get_text_of_all_navbar_menu_options(self) -> list[str]:
        """Get the text of all navbar menu options."""
        return self._get_text_of_elements(self.user_navbar_options)

    def get_text_of_publicly_displayed_username(self) -> str:
        """Get the text of the publicly displayed username."""
        return self._get_text_of_element(self.displayed_email_address)

    def get_text_of_profile_subheading_location(self) -> str:
        """Get the text of the profile subheading location."""
        return self._get_text_of_element(self.page_subheading)

    def get_my_profile_questions_text(self) -> str:
        """Get the profile questions text."""
        return self._get_text_of_element(self.questions_link)

    def is_question_displayed(self) -> bool:
        """Check if the question link is displayed."""
        return self._is_element_visible(self.questions_link)

    def get_my_profile_solutions_text(self) -> str:
        """Get the profile solutions text."""
        return self._get_text_of_element(self.provided_solutions_text)

    def is_solutions_displayed(self) -> bool:
        """Check if the solutions are displayed."""
        return self._is_element_visible(self.provided_solutions_text)

    def get_my_profile_documents_text(self) -> str:
        """Get the profile documents text."""
        return self._get_text_of_element(self.provided_documents_link)

    def get_my_profile_answers_text(self) -> str:
        """Get the profile answers text."""
        return self._get_text_of_element(self.answers_link)

    def get_my_profile_groups_heading_text(self) -> str:
        """Get the profile groups heading text."""
        return self._get_text_of_element(self.groups_heading)

    def get_my_profile_groups_items_text(self) -> set[str]:
        """Get the profile groups items text."""
        return set(self._get_text_of_elements(self.groups_list_items))

    def click_on_edit_user_profile_button(self):
        """Click on the edit user profile button."""
        self._click(self.edit_user_profile_option)

    def click_my_profile_answers_link(self):
        """Click on the profile answers link."""
        self._click(self.answers_link)

    def is_my_profile_answers_link_visible(self) -> bool:
        """Verifying if the profile answers link option is visible."""
        return self._is_element_visible(self.answers_link)

    def click_on_my_profile_questions_link(self):
        """Click on the profile questions link."""
        self._click(self.questions_link)

    def click_on_my_profile_document_link(self):
        """Click on the profile document link."""
        self._click(self.provided_documents_link)

    def click_on_my_website_link(self):
        """Click on the website link."""
        self._click(self.website_info)

    def click_on_twitter_link(self):
        """Click on the Twitter link."""
        self._click(self.twitter_info)

    def click_on_community_portal_link(self):
        """Click on the community portal link."""
        self._click(self.community_portal_info)

    def click_on_people_directory_link(self):
        """Click on the people directory link."""
        self._click(self.people_directory_info)

    def click_on_element(self, element: ElementHandle):
        """Click on the given element."""
        element.click()

    def click_my_profile_page_sign_out_button(self, expected_url=None):
        """Click on the profile page sign out button.

        Args:
            expected_url (str): The expected URL after clicking the 'sign out' button
        """
        self._click(self.sign_out_button, expected_url=expected_url)

    def click_on_report_abuse_option(self):
        """Click on the report abuse option."""
        self._click(self.report_abuse_profile_option)

    def click_on_report_abuse_close_button(self):
        """Click on the report abuse close button."""
        self._click(self.report_abuse_close_panel_button)

    def click_on_private_message_button(self, expected_url=None):
        """Click on the private message button.

        Args:
            expected_url (str): The expected URL after clicking the private message button.
        """
        self._click(self.private_message_button, expected_url=expected_url)

    def publicly_displayed_email_element(self) -> Locator:
        """Get the locator for the publicly displayed email element."""
        return self.displayed_email_address

    def is_website_information_displayed(self) -> bool:
        """Check if the website information is displayed."""
        return self._is_element_visible(self.website_info)

    def groups_section_element(self) -> Locator:
        """Get the locator for the groups section."""
        return self.groups_section

    def click_on_a_particular_profile_group(self, group_name: str):
        """Click on a particular profile group.

        Args:
            group_name (str): The name of the group to click on
        """
        self._click(self.group_by_name(group_name))

    def edit_user_profile_option_element(self) -> Locator:
        """Get the locator for the edit user profile option."""
        return self.edit_user_profile_option

    def is_report_user_option_displayed(self) -> Locator:
        """Get the locator for the report user option."""
        return self.report_abuse_profile_option

    def is_report_abuse_panel_displayed(self) -> Locator:
        """Get the locator for the report abuse panel."""
        return self.report_abuse_panel

    def is_deactivate_this_user_button_displayed(self) -> Locator:
        """Get the locator for the deactivate this user button."""
        return self.deactivate_this_user_button

    def deactivate_user_and_mark_content_as_spam_button(self) -> Locator:
        """Get the locator for the deactivate user and mark content as spam button."""
        return self.deactivate_this_user_and_mark_all_content_as_spam
