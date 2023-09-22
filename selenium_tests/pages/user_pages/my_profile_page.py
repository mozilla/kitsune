from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class MyProfilePage(BasePage):
    # Sidebar
    __my_profile_user_navbar_options = (By.XPATH, "//ul[@id='user-nav']/li/a")
    __my_profile_user_navbar_selected_element = (By.XPATH, "//a[@class='selected']")

    # Admin/other user actions
    __edit_user_profile_option = (
        By.XPATH,
        "//div[@id='admin-actions']/a[contains(text(), 'Edit user profile')]",
    )
    __report_abuse_profile_option = (
        By.XPATH,
        "//article[@id='profile']/a[contains(text(), 'Report Abuse')]",
    )
    __deactivate_this_user_button = (By.XPATH, "//input[@value='Deactivate this user']")
    __deactivate_this_user_and_mark_all_content_as_spam = (
        By.XPATH,
        "//input[@value='Deactivate this user and mark " "all content as spam']",
    )
    __private_message_button = (By.XPATH, "//p[@class='pm']/a")

    # Report Abuse
    __report_abuse_panel = (By.XPATH, "//section[@id='report-abuse']")
    __spam_or_other_unrelated_content_option = (
        By.XPATH,
        "//label[contains(text(),'Spam or other unrelated content')]",
    )
    __inappropriate_language_or_dialog_option = (
        By.XPATH,
        "//label[contains(text(),'Inappropriate language/dialog')]",
    )
    __other_please_specify_option = (
        By.XPATH,
        "//label[contains(text(),'Other (please specify)')]",
    )
    __have_more_to_say_textarea = (By.XPATH, "//textarea[@name='other']")
    __report_abuse_close_panel_button = (By.XPATH, "//div[@class='mzp-c-modal-close']/button")
    __report_abuse_submit_button = (
        By.XPATH,
        "//section[@id='report-abuse']//button[@type='submit']",
    )
    __reported_user_confirmation_message = (By.XPATH, "//span[@class='message']")

    # Contributions section
    __my_profile_contributions_questions_link = (
        By.XPATH,
        "//section[@class='contributions']//a[contains(text(), " "'question')]",
    )
    __my_profile_contributions_answers_link = (
        By.XPATH,
        "//section[@class='contributions']//a[contains(text(), " "'answer')]",
    )
    __my_profile_provided_solutions_text = (
        By.XPATH,
        "//section[@class='contributions']//li[contains(text(),'solution')]",
    )

    __my_profile_provided_documents_link = (
        By.XPATH,
        "//section[@class='contributions']//a[contains(text(),'document')]",
    )

    # My Profile page details
    __my_profile_page_header = (By.XPATH, "//h1[@class='sumo-page-heading']")
    __my_profile_page_subheading = (
        By.XPATH,
        "//article[@id='profile']/h2[contains(@class, 'sumo-page-subheading')]",
    )
    __my_profile_email_address = (By.XPATH, "//p/strong")
    __my_profile_displayed_email_address = (
        By.XPATH,
        "//li[@class='avatar-group--details-item']/span[@class='email']/a",
    )
    __my_profile_sign_out_button = (
        By.XPATH,
        "//article[@id='profile']//a[@data-event-label='Sign Out']",
    )
    __my_profile_display_name_header = (By.XPATH, "//h2[@class='sumo-callout-heading user']")
    __my_profile_username_info = (By.XPATH, "//span[@class='username']")
    __my_profile_location_info = (By.XPATH, "//h2[contains(@class,'location')]")
    __my_profile_website_info = (
        By.XPATH,
        "//label[contains(text(), 'Website')]/following-sibling::a",
    )
    __my_profile_twitter_info = (
        By.XPATH,
        "//label[contains(text(), 'Twitter')]/following-sibling::a",
    )
    __my_profile_community_portal_info = (
        By.XPATH,
        "//label[contains(text(), 'Community Portal')]/following-sibling::a",
    )
    __my_profile_people_directory_info = (
        By.XPATH,
        "//label[contains(text(), 'People Directory')]/following-sibling::a",
    )
    __my_profile_matrix_info = (By.XPATH, "//label[contains(text(),'Matrix')]/parent::li")
    __my_profile_contributed_from_info = (By.XPATH, "//section[@class='contributions']//li[1]")
    __my_profile_bio_info = (By.XPATH, "//section[@class='bio']/p")
    __my_profile_groups_section = (By.XPATH, "//section[@class='groups']")
    __my_profile_groups_heading = (By.XPATH, "//section[@class='groups']/h2")
    __my_profile_groups_list_items = (By.XPATH, "//section[@class='groups']/ul/li")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_my_profile_display_name_header_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_display_name_header)

    def get_my_profile_display_name_username_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_username_info)

    def get_my_profile_location_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_location_info)

    def get_my_profile_website_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_website_info)

    def get_my_profile_twitter_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_twitter_info)

    def get_my_profile_community_portal_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_community_portal_info)

    def get_my_profile_people_directory_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_people_directory_info)

    def get_my_profile_matrix_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_matrix_info)

    def get_my_contributed_from_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_contributed_from_info)

    def get_my_profile_bio_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_bio_info)

    def get_my_profile_page_header(self) -> str:
        return super()._get_text_of_element(self.__my_profile_page_header)

    def get_my_profile_email_information(self) -> str:
        return super()._get_text_of_element(self.__my_profile_email_address)

    def get_text_of_selected_navbar_option(self) -> str:
        return super()._get_text_of_element(self.__my_profile_user_navbar_selected_element)

    def get_navbar_menu_options(self) -> list[WebElement]:
        return super()._find_elements(self.__my_profile_user_navbar_options)

    def get_text_of_all_navbar_menu_options(self) -> list[str]:
        return super()._get_text_of_elements(self.__my_profile_user_navbar_options)

    def get_text_of_publicly_displayed_username(self) -> str:
        return super()._get_text_of_element(self.__my_profile_displayed_email_address)

    def get_text_of_profile_subheading_location(self) -> str:
        return super()._get_text_of_element(self.__my_profile_page_subheading)

    def get_my_profile_questions_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_contributions_questions_link)

    def get_my_profile_solutions_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_provided_solutions_text)

    def get_my_profile_documents_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_provided_documents_link)

    def get_my_profile_answers_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_contributions_answers_link)

    def get_my_profile_groups_heading_text(self) -> str:
        return super()._get_text_of_element(self.__my_profile_groups_heading)

    def get_my_profile_groups_items_text(self) -> set[str]:
        initial_list = set(super()._get_text_of_elements(self.__my_profile_groups_list_items))
        return initial_list

    def click_on_edit_user_profile_button(self):
        super()._click(self.__edit_user_profile_option)

    def click_my_profile_answers_link(self):
        super()._click(self.__my_profile_contributions_answers_link)

    def click_on_my_profile_questions_link(self):
        super()._click(self.__my_profile_contributions_questions_link)

    def click_on_my_profile_document_link(self):
        super()._click(self.__my_profile_provided_documents_link)

    def click_on_my_website_link(self):
        super()._click(self.__my_profile_website_info)

    def click_on_twitter_link(self):
        super()._click(self.__my_profile_twitter_info)

    def click_on_community_portal_link(self):
        super()._click(self.__my_profile_community_portal_info)

    def click_on_people_directory_link(self):
        super()._click(self.__my_profile_people_directory_info)

    def click_on_element(self, element: WebElement):
        super()._click_on_web_element(element)

    def click_my_profile_page_sign_out_button(self):
        super()._click(self.__my_profile_sign_out_button)

    def click_on_report_abuse_option(self):
        super()._click(self.__report_abuse_profile_option)

    def click_on_report_abuse_close_button(self):
        super()._click(self.__report_abuse_close_panel_button)

    def click_on_private_message_button(self):
        super()._click(self.__private_message_button)

    def is_publicly_displayed_email_displayed(self) -> bool:
        return super()._is_element_displayed(self.__my_profile_displayed_email_address)

    def is_website_information_displayed(self) -> bool:
        return super()._is_element_displayed(self.__my_profile_website_info)

    def is_groups_section_displayed(self) -> bool:
        return super()._is_element_displayed(self.__my_profile_groups_section)

    def is_edit_user_profile_option_displayed(self) -> bool:
        return super()._is_element_displayed(self.__edit_user_profile_option)

    def is_report_user_option_displayed(self) -> bool:
        return super()._is_element_displayed(self.__report_abuse_profile_option)

    def is_report_abuse_panel_displayed(self) -> bool:
        return super()._is_element_displayed(self.__report_abuse_panel)

    def is_deactivate_this_user_button_displayed(self) -> bool:
        return super()._is_element_displayed(self.__deactivate_this_user_button)

    def is_deactivate_this_user_and_mark_content_as_spam_displayed(self) -> bool:
        return super()._is_element_displayed(
            self.__deactivate_this_user_and_mark_all_content_as_spam
        )
