from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileEditContributionAreasPage(BasePage):
    __edit_contribution_areas_page_header = "//h3[@class='sumo-page-heading']"
    __edit_contribution_areas_checkboxes = "//input[@type='checkbox']"
    __edit_contribution_areas_kb_contributors = "//input[@value='kb-contributors']"
    __edit_contribution_areas_l10n_contributors = "//input[@value='l10n-contributors']"
    __edit_contribution_areas_forum_contributors = "//input[@value='forum-contributors']"
    __edit_contribution_areas_social_media_contributors = "//input[@value='social-contributors']"
    __edit_contribution_areas_mobile_support_contributors = "//input[@value='mobile-contributors']"
    __edit_contribution_areas_checkbox_labels = "//input[@type='checkbox']/parent::label"
    __edit_contribution_areas_update_button = ("//article[@id='edit-contributions']/form//button["
                                               "@type='submit']")
    __edit_contribution_areas_preferences_saved_banner = "//ul[@class='user-messages']/li"
    __edit_contribution_areas_preferences_saved_banner_text = "//ul[@class='user-messages']/li/p"
    __edit_contribution_areas_preferences_saved_banner_close_button = ("//ul[@class='user"
                                                                       "-messages']/li/button")

    def __init__(self, page: Page):
        super().__init__(page)

    def _edit_con_areas_pref_banner_txt(self) -> str:
        return super()._get_text_of_element(
            self.__edit_contribution_areas_preferences_saved_banner_text)

    def _get_edit_contribution_areas_page_header(self) -> str:
        return super()._get_text_of_element(self.__edit_contribution_areas_page_header)

    def _get_contrib_areas_checkbox_labels(self) -> set[str]:
        initial_list = set(
            super()._get_text_of_elements(self.__edit_contribution_areas_checkbox_labels)
        )
        normalized_list = set(
            [
                item.lower()
                .replace(" ", "-")
                .replace("media", "")
                .replace("support", "")
                .replace("--", "-")
                [1:]
                for item in initial_list
            ]
        )
        return normalized_list

    def _click_on_update_contribution_areas_button(self):
        super()._click(self.__edit_contribution_areas_update_button)

    def _click_on_unchecked_cont_areas_checkboxes(self):
        for checkbox in super()._get_element_handles(self.__edit_contribution_areas_checkboxes):
            if not checkbox.is_checked():
                checkbox.click()

    def _click_on_all_checked_cont_areas_checkboxes(self):
        for checkbox in super()._get_element_handles(self.__edit_contribution_areas_checkboxes):
            if checkbox.is_checked():
                checkbox.click()

    def _click_on_edit_cont_pref_banner_close_button(self):
        super()._click(self.__edit_contribution_areas_preferences_saved_banner_close_button)

    def _is_edit_cont_pref_banner_displayed(self) -> Locator:
        return super()._get_element_locator(
            self.__edit_contribution_areas_preferences_saved_banner)

    def _is_kb_contributors_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__edit_contribution_areas_kb_contributors)

    def _is_l10n_contributors_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__edit_contribution_areas_l10n_contributors)

    def _is_forum_contributors_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(self.__edit_contribution_areas_forum_contributors)

    def _is_social_media_contributors_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(
            self.__edit_contribution_areas_social_media_contributors)

    def _is_mobile_support_contributors_checkbox_checked(self) -> bool:
        return super()._is_checkbox_checked(
            self.__edit_contribution_areas_mobile_support_contributors)

    def _are_all_cont_pref_checkboxes_checked(self) -> bool:
        is_checked = [
            self._is_kb_contributors_checkbox_checked(),
            self._is_l10n_contributors_checkbox_checked(),
            self._is_forum_contributors_checkbox_checked(),
            self._is_social_media_contributors_checkbox_checked(),
            self._is_mobile_support_contributors_checkbox_checked(),
        ]

        if False in is_checked:
            return False
        else:
            return True
