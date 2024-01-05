from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage


class MyProfilePage(BasePage):
    # Sidebar
    __my_profile_user_navbar_options = "//ul[@id='user-nav']/li/a"
    __my_profile_user_navbar_selected_element = "//a[@class='selected']"

    # Admin/other user actions
    __edit_user_profile_option = ("//div[@id='admin-actions']/a[contains(text(), 'Edit user "
                                  "profile')]")
    __report_abuse_profile_option = "//article[@id='profile']/a[contains(text(), 'Report Abuse')]"
    __deactivate_this_user_button = "//input[@value='Deactivate this user']"
    __deactivate_this_user_and_mark_all_content_as_spam = ("//input[@value='Deactivate this user "
                                                           "and mark all content as spam']")
    __private_message_button = "//p[@class='pm']/a"

    # Report Abuse
    __report_abuse_panel = "//section[@id='report-abuse']"
    __spam_or_other_unrelated_content_option = ("//label[contains(text(),'Spam or other unrelated "
                                                "content')]")
    __inappropriate_language_or_dialog_option = ("//label[contains(text(),'Inappropriate "
                                                 "language/dialog')]")
    __other_please_specify_option = "//label[contains(text(),'Other (please specify)')]"
    __have_more_to_say_textarea = "//textarea[@name='other']"
    __report_abuse_close_panel_button = "//div[@class='mzp-c-modal-close']/button"
    __report_abuse_submit_button = "//section[@id='report-abuse']//button[@type='submit']"
    __reported_user_confirmation_message = "//span[@class='message']"

    # Contributions section
    __my_profile_contributions_questions_link = ("//section[@class='contributions']//a[contains("
                                                 "text(), 'question')]")
    __my_profile_contributions_answers_link = ("//section[@class='contributions']//a[contains("
                                               "text(), 'answer')]")
    __my_profile_provided_solutions_text = ("//section[@class='contributions']//li[contains(text("
                                            "),'solution')]")
    __my_profile_provided_documents_link = ("//section[@class='contributions']//a[contains(text("
                                            "),'document')]")

    # My Profile page details
    __my_profile_page_header = "//h1[@class='sumo-page-heading']"
    __my_profile_page_subheading = ("//article[@id='profile']/h2[contains(@class, "
                                    "'sumo-page-subheading')]")
    __my_profile_email_address = "//p/strong"
    __my_profile_displayed_email_address = ("//li[@class='avatar-group--details-item']/span["
                                            "@class='email']/a")
    __my_profile_sign_out_button = "//article[@id='profile']//a[@data-event-label='Sign Out']"
    __my_profile_display_name_header = "//h2[@class='sumo-callout-heading user']"
    __my_profile_username_info = "//span[@class='username']"
    __my_profile_location_info = "//h2[contains(@class,'location')]"
    __my_profile_website_info = "//label[contains(text(), 'Website')]/following-sibling::a"
    __my_profile_twitter_info = "//label[contains(text(), 'Twitter')]/following-sibling::a"
    __my_profile_community_portal_info = ("//label[contains(text(), 'Community "
                                          "Portal')]/following-sibling::a")
    __my_profile_people_directory_info = ("//label[contains(text(), 'People "
                                          "Directory')]/following-sibling::a")
    __my_profile_matrix_info = "//label[contains(text(),'Matrix')]/parent::li"
    __my_profile_contributed_from_info = "//section[@class='contributions']//li[1]"
    __my_profile_bio_info = "//section[@class='bio']/p"
    __my_profile_groups_section = "//section[@class='groups']"
    __my_profile_groups_heading = "//section[@class='groups']/h2"
    __my_profile_groups_list_items = "//section[@class='groups']/ul/li"

    def __init__(self, page: Page):
        super().__init__(page)

    # My profile page actions.
    def _get_my_profile_display_name_header_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_display_name_header)

    def _get_my_profile_display_name_username_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_username_info)

    def _get_my_profile_location_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_location_info)

    def _get_my_profile_website_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_website_info)

    def _get_my_profile_twitter_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_twitter_info)

    def _get_my_profile_community_portal_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_community_portal_info)

    def _get_my_profile_people_directory_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_people_directory_info)

    def _get_my_profile_matrix_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_matrix_info)

    def _get_my_contributed_from_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_contributed_from_info)

    def _get_my_profile_bio_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_bio_info)

    def _get_my_profile_page_header(self) -> str:
        return super()._get_text_of_element(self.__my_profile_page_header)

    def _get_my_profile_email_information(self) -> str:
        return super()._get_text_of_element(self.__my_profile_email_address)

    def _get_text_of_selected_navbar_option(self) -> str:
        return super()._get_text_of_element(self.__my_profile_user_navbar_selected_element)

    def _get_navbar_menu_options(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__my_profile_user_navbar_options)

    def _get_text_of_all_navbar_menu_options(self) -> list[str]:
        return super()._get_text_of_elements(self.__my_profile_user_navbar_options)

    def _get_text_of_publicly_displayed_username(self) -> str:
        return super()._get_text_of_element(self.__my_profile_displayed_email_address)

    def _get_text_of_profile_subheading_location(self) -> str:
        return super()._get_text_of_element(self.__my_profile_page_subheading)

    def _get_my_profile_questions_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_contributions_questions_link)

    def _get_my_profile_solutions_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_provided_solutions_text)

    def _get_my_profile_documents_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_provided_documents_link)

    def _get_my_profile_answers_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_contributions_answers_link)

    def _get_my_profile_groups_heading_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_groups_heading)

    def _get_my_profile_groups_items_text(self) -> set[str]:
        initial_list = set(super()._get_text_of_elements(self.__my_profile_groups_list_items))
        return initial_list

    def _click_on_edit_user_profile_button(self):
        super()._click(self.__edit_user_profile_option)

    def _click_my_profile_answers_link(self):
        super()._click(self.__my_profile_contributions_answers_link)

    def _click_on_my_profile_questions_link(self):
        super()._click(self.__my_profile_contributions_questions_link)

    def _click_on_my_profile_document_link(self):
        super()._click(self.__my_profile_provided_documents_link)

    def _click_on_my_website_link(self):
        super()._click(self.__my_profile_website_info)

    def _click_on_twitter_link(self):
        super()._click(self.__my_profile_twitter_info)

    def _click_on_community_portal_link(self):
        super()._click(self.__my_profile_community_portal_info)

    def _click_on_people_directory_link(self):
        super()._click(self.__my_profile_people_directory_info)

    def _click_on_element(self, element: ElementHandle):
        element.click()

    def _click_my_profile_page_sign_out_button(self):
        super()._click(self.__my_profile_sign_out_button)

    def _click_on_report_abuse_option(self):
        super()._click(self.__report_abuse_profile_option)

    def _click_on_report_abuse_close_button(self):
        super()._click(self.__report_abuse_close_panel_button)

    def _click_on_private_message_button(self):
        super()._click(self.__private_message_button)

    def _publicly_displayed_email_element(self) -> Locator:
        return super()._get_element_locator(self.__my_profile_displayed_email_address)

    def _is_website_information_displayed(self) -> bool:
        return super()._is_element_visible(self.__my_profile_website_info)

    def _groups_section_element(self) -> Locator:
        return super()._get_element_locator(self.__my_profile_groups_section)

    def _edit_user_profile_option_element(self) -> Locator:
        return super()._get_element_locator(self.__edit_user_profile_option)

    def _is_report_user_option_displayed(self) -> Locator:
        return super()._get_element_locator(self.__report_abuse_profile_option)

    def _is_report_abuse_panel_displayed(self) -> Locator:
        return super()._get_element_locator(self.__report_abuse_panel)

    def _is_deactivate_this_user_button_displayed(self) -> Locator:
        return super()._get_element_locator(self.__deactivate_this_user_button)

    def _deactivate_this_user_and_mark_content_as_spam_elem(self) -> Locator:
        return super()._get_element_locator(
            self.__deactivate_this_user_and_mark_all_content_as_spam)
