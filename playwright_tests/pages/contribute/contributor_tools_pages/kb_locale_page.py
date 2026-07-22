from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class KBLocalePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the /kb/locales list page."""
        self.locale_list_heading = page.locator("article#locale-listing h1.sumo-page-heading")
        self.locale_list_entries = page.locator("article#locale-listing ul li a")
        self.locale_list_entry = lambda locale_code: page.locator(
            f"article#locale-listing ul li a[href$='/kb/locales/{locale_code}/']")

        """Locators belonging to the per-locale team details page."""
        self.locale_team_heading = page.locator("article#locale-listing h1.sumo-page-heading")
        self.page_notification_banner = page.locator(
            "li[class*='mzp-c-notification-bar'] p, ul.user-messages li p")
        self.edit_role_option = lambda role: page.locator(f"#locale-{role}s a.edit")
        self.add_role_form_input = lambda role: page.locator(
            f"#add-{role}-form input#token-input-id_users")
        self.add_role_submit_button = lambda role: page.locator(
            f"#add-{role}-form input[type='submit']")
        self.autocomplete_result = lambda username: page.locator(
            f"//div[@class='name_search']/b[text()='{username}']")
        self.role_member = lambda role, username: page.locator(
            f"#locale-{role}s ul.users li").filter(
            has=page.locator(f"a[href$='to={username}']"))
        self.role_member_remove_button = lambda role, username: self.role_member(
            role, username).locator("a.sumo-delete-button")
        self.role_member_private_message_link = lambda role, username: self.role_member(
            role, username).locator("span.asked-on a")
        self.role_member_profile_link = lambda role, username: self.role_member(
            role, username).locator("a.author-name")

        """Locators belonging to the remove-from-locale confirmation page."""
        self.confirm_remove_submit_button = page.locator(
            "article#remove-leader form input[type='submit']")
        self.confirm_remove_cancel_option = page.locator("article#remove-leader form a")

    # ---------------------------------------------------------------- Locale list actions
    def get_locale_list_entries_count(self) -> int:
        """Returns the number of locales listed on the /kb/locales page."""
        self._wait_for_locator(self.locale_list_entries.first)
        return self._get_elements_count(self.locale_list_entries)

    def get_first_locale_entry_href(self) -> str:
        """Returns the href of the first listed locale entry."""
        self._wait_for_locator(self.locale_list_entries.first)
        return self._get_element_attribute_value(self.locale_list_entries.first, "href")

    def click_on_first_locale_entry(self):
        """Clicks the first listed locale entry."""
        self._click_on_first_item(self.locale_list_entries)

    def click_on_locale_entry(self, locale_code: str):
        """Clicks the list entry for a specific locale code."""
        self._click(self.locale_list_entry(locale_code))

    # ---------------------------------------------------------------- Locale team actions
    def get_locale_team_heading_text(self) -> str:
        return self._get_text_of_element(self.locale_team_heading)

    def click_on_edit_role_option(self, role: str):
        """Reveals the add/remove controls for a role section."""
        self._click(self.edit_role_option(role))

    def add_user_to_role(self, username: str, role: str):
        """Reveal the add form for the given role, search for and select the user via the
        autocomplete, then submit the form."""
        self.click_on_edit_role_option(role)
        self._type(self.add_role_form_input(role), username, delay=0)
        self._click(self.autocomplete_result(username))
        self._click(self.add_role_submit_button(role),
                    expected_locator=self.role_member(role, username))

    def click_on_remove_user_from_role(self, username: str, role: str):
        """Reveal the role section controls and click the remove (x) button for a user, landing
        on the removal confirmation page."""
        self.click_on_edit_role_option(role)
        self._click(self.role_member_remove_button(role, username))

    def click_on_confirm_remove_button(self):
        """Confirm the removal on the confirmation page."""
        self._click(self.confirm_remove_submit_button)

    def click_on_private_message_link_for_user(self, username: str, role: str, expected_url=None):
        """Click the 'Private message' link shown for a user listed in a role section."""
        self._click(self.role_member_private_message_link(role, username),
                    expected_url=expected_url)

    def click_on_profile_link_for_user(self, username: str, role: str):
        """Click the profile (display name) link shown for a user listed in a role section."""
        self._click(self.role_member_profile_link(role, username))
