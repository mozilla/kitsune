from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class MyProfileEditContributionAreasPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # My profile contribution areas page locators.
        self.edit_contribution_areas_page_header = page.locator("h3[class='sumo-page-heading']")
        self.edit_contribution_areas_checkboxes = page.locator("input[type='checkbox']")
        self.edit_contribution_areas_kb_contributors = page.locator(
            "input[value='kb-contributors']")
        self.edit_contribution_areas_l10n_contributors = page.locator(
            "input[value='l10n-contributors']")
        self.edit_contribution_areas_forum_contributors = page.locator(
            "input[value='forum-contributors']")
        self.edit_contribution_areas_checkbox_labels = page.locator(
            "//input[@type='checkbox']/parent::label")
        self.edit_contribution_areas_update_button = page.locator(
            "article#edit-contributions form button[type='submit']")
        self.edit_contribution_areas_preferences_saved_banner = page.locator(
            "ul[class='user-messages'] li")
        self.edit_contribution_areas_preferences_saved_banner_text = page.locator(
            "ul[class='user-messages'] li p")
        self.edit_contribution_areas_preferences_saved_banner_close_button = page.locator(
            "ul[class='user-messages'] li button")

    # My profile contribution areas page actions.
    def edit_con_areas_pref_banner_txt(self) -> str:
        """Get the display pref banner text"""
        return self._get_text_of_element(
            self.edit_contribution_areas_preferences_saved_banner_text)

    def get_edit_contribution_areas_page_header(self) -> str:
        """Get the header text of the edit contribution areas page header"""
        return self._get_text_of_element(self.edit_contribution_areas_page_header)

    def get_contrib_areas_checkbox_labels(self) -> set[str]:
        """Get the label text of the contribution areas checkboxes"""
        return {
            item.lower()
            .replace(" ", "-")
            .replace("--", "-")[1:]
            for item in self._get_text_of_elements(self.edit_contribution_areas_checkbox_labels)
        }

    def click_on_update_contribution_areas_button(self):
        """Click on the update contribution areas button"""
        self._click(self.edit_contribution_areas_update_button)

    def click_on_unchecked_cont_areas_checkboxes(self):
        """Check all unchecked contribution areas checkboxes"""
        for checkbox in self._get_element_handles(self.edit_contribution_areas_checkboxes):
            if not checkbox.is_checked():
                checkbox.check()

    def click_on_all_checked_cont_areas_checkboxes(self):
        """Uncheck all checked contribution areas checkboxes"""
        for checkbox in self._get_element_handles(self.edit_contribution_areas_checkboxes):
            if checkbox.is_checked():
                checkbox.uncheck()

    def click_on_edit_cont_pref_banner_close_button(self):
        """Click on the close button of the edit contribution areas preferences saved banner"""
        self._click(self.edit_contribution_areas_preferences_saved_banner_close_button)

    def is_edit_cont_pref_banner_displayed(self) -> Locator:
        """Check if the edit contribution areas preferences saved banner is displayed"""
        return self.edit_contribution_areas_preferences_saved_banner

    def is_kb_contributors_checkbox_checked(self) -> bool:
        """Check if the kb contributors checkbox is checked"""
        return self._is_checkbox_checked(self.edit_contribution_areas_kb_contributors)

    def is_l10n_contributors_checkbox_checked(self) -> bool:
        """Check if the l10n contributors checkbox is checked"""
        return self._is_checkbox_checked(self.edit_contribution_areas_l10n_contributors)

    def is_forum_contributors_checkbox_checked(self) -> bool:
        """Check if the forum contributors checkbox is checked"""
        return self._is_checkbox_checked(self.edit_contribution_areas_forum_contributors)

    def are_all_cont_pref_checked(self) -> bool:
        """Check if all contribution areas checkboxes are checked"""
        return all([
            self.is_kb_contributors_checkbox_checked(),
            self.is_l10n_contributors_checkbox_checked(),
            self.is_forum_contributors_checkbox_checked()
        ])
