from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class AuthPage(BasePage):

    # Auth page content
    __auth_page_section = "//section[@class='sumo-auth--wrap']"
    __fxa_sign_in_page_header = "//h1[@id='fxa-signin-password-header']"
    __auth_page_main_header = "//h1[@class='sumo-page-heading']"
    __auth_page_subheading_text = "//div[@class='sumo-page-section']/p"

    # Continue with firefox accounts button
    __continue_with_firefox_accounts_button = "//p[@class='login-button-wrap']/a"

    # Use a different account option
    __use_a_different_account_button = "//a[@id='use-different']"

    # Already logged in 'Sign in' button
    __user_logged_in_sign_in_button = "//button[@id='use-logged-in']"

    # Email submission
    __enter_your_email_input_field = "//input[@name='email']"
    __enter_your_email_submit_button = "//button[@id='submit-btn']"

    # Password submission
    __enter_your_password_input_field = "//input[@id='password']"
    __enter_your_password_submit_button = "//button[@id='submit-btn']"

    # OTP Code
    __enter_otp_code_input_field = "//input[@id='otp-code']"
    __enter_otp_code_confirm_button = "//button[@id='submit-btn']"

    def __init__(self, page: Page):
        super().__init__(page)

    def click_on_continue_with_firefox_accounts_button(self):
        super()._click(self.__continue_with_firefox_accounts_button)

    def click_on_use_a_different_account_button(self):
        super()._click(self.__use_a_different_account_button)

    def click_on_user_logged_in_sign_in_button(self):
        super()._click(self.__user_logged_in_sign_in_button)

    def click_on_enter_your_email_submit_button(self):
        super()._click(self.__enter_your_email_submit_button)

    def click_on_enter_your_password_submit_button(self):
        super()._click(self.__enter_your_password_submit_button)

    def click_on_otp_code_confirm_button(self):
        super()._click(self.__enter_otp_code_confirm_button)

    def add_data_to_email_input_field(self, text: str):
        super()._fill(self.__enter_your_email_input_field, text)

    def add_data_to_password_input_field(self, text: str):
        super()._fill(self.__enter_your_password_input_field, text)

    def add_data_to_otp_code_input_field(self, text: str):
        super()._fill(self.__enter_otp_code_input_field, text)

    def clear_email_input_field(self):
        super()._clear_field(self.__enter_your_email_input_field)

    def is_use_a_different_account_button_displayed(self) -> bool:
        super()._wait_for_selector(self.__use_a_different_account_button)
        return super()._is_element_visible(self.__use_a_different_account_button)

    def is_logged_in_sign_in_button_displayed(self) -> bool:
        return super()._is_element_visible(self.__user_logged_in_sign_in_button)

    def is_enter_otp_code_input_field_displayed(self) -> bool:
        super()._wait_for_selector(self.__continue_with_firefox_accounts_button)
        return super()._is_element_visible(self.__enter_otp_code_input_field)

    def is_continue_with_firefox_button_displayed(self) -> bool:
        super()._wait_for_selector(self.__continue_with_firefox_accounts_button)
        return super()._is_element_visible(self.__continue_with_firefox_accounts_button)
