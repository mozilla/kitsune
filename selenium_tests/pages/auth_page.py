from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class AuthPage(BasePage):
    __auth_page_section = (By.XPATH, "//section[@class='sumo-auth--wrap']")
    __fxa_sign_in_page_header = (By.XPATH, "//h1[@id='fxa-signin-password-header']")
    __auth_page_main_header = (By.XPATH, "//h1[@class='sumo-page-heading']")
    __auth_page_subheading_text = (By.XPATH, "//div[@class='sumo-page-section']/p")
    __continue_with_firefox_accounts_button = (By.XPATH, "//p[@class='login-button-wrap']/a")
    __use_a_different_account_button = (By.XPATH, "//a[@id='use-different']")
    __user_logged_in_sign_in_button = (By.XPATH, "//button[@id='use-logged-in']")
    __enter_your_email_input_field = (By.XPATH, "//input[@name='email']")
    __enter_your_email_submit_button = (By.XPATH, "//button[@id='submit-btn']")
    __enter_your_password_input_field = (By.XPATH, "//input[@id='password']")
    __enter_your_password_submit_button = (By.XPATH, "//button[@id='submit-btn']")
    __enter_otp_code_input_field = (By.XPATH, "//input[@id='otp-code']")
    __enter_otp_code_confirm_button = (By.XPATH, "//button[@id='submit-btn']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

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
        super()._type(self.__enter_your_email_input_field, text)

    def add_data_to_password_input_field(self, text: str):
        super()._type(self.__enter_your_password_input_field, text)

    def add_data_to_otp_code_input_field(self, text: str):
        super()._type(self.__enter_otp_code_input_field, text)

    def clear_email_input_field(self):
        super()._clear_input_field(self.__enter_your_email_input_field)

    def is_use_a_different_account_button_displayed(self) -> bool:
        return super()._is_element_displayed(self.__use_a_different_account_button)

    def is_logged_in_sign_in_button_displayed(self) -> bool:
        return super()._is_element_displayed(self.__user_logged_in_sign_in_button)

    def is_enter_otp_code_input_field_displayed(self) -> bool:
        return super()._is_element_displayed(self.__enter_otp_code_input_field)

    def is_continue_with_firefox_button_displayed(self) -> bool:
        return super()._is_element_displayed(self.__continue_with_firefox_accounts_button)
