from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class AuthPage(BasePage):
    # Auth page content
    AUTH_PAGE_CONTENT_LOCATORS = {
        "auth_page_section": "//section[@class='sumo-auth--wrap']",
        "fxa_sign_in_page_header": "//h1[@id='fxa-signin-password-header']",
        "auth_page_main_header": "//h1[@class='sumo-page-heading']",
        "auth_page_subheading_text": "//div[@class='sumo-page-section']/p",
        "cant_sign_in_to_my_Mozilla_account_link": "//div[@class='trouble-text']//a",
        "continue_with_firefox_accounts_button": "//p[@class='login-button-wrap']/a",
        "use_a_different_account_button": "//a[text()='Use a different account']",
        "user_logged_in_sign_in_button": "//button[text()='Sign in']",
        "enter_your_email_input_field": "//input[@name='email']",
        "enter_your_email_submit_button": "//button[@id='submit-btn']",
        "enter_your_password_input_field": "//input[@type='password']",
        "enter_your_password_submit_button": "//button[text()='Sign in']",
        "enter_otp_code_input_field": "//input[@id='otp-code']",
        "enter_otp_code_confirm_button": "//button[@id='submit-btn']"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    def click_on_cant_sign_in_to_my_mozilla_account_link(self):
        """Click on 'Can't sign in to my Mozilla account' link"""
        self._click(self.AUTH_PAGE_CONTENT_LOCATORS["cant_sign_in_to_my_Mozilla_account_link"])

    def click_on_continue_with_firefox_accounts_button(self):
        """Click on 'Continue with Firefox Accounts' button"""
        self._click(self.AUTH_PAGE_CONTENT_LOCATORS["continue_with_firefox_accounts_button"])

    def click_on_use_a_different_account_button(self):
        """Click on 'Use a different account' button"""
        self._click(self.AUTH_PAGE_CONTENT_LOCATORS["use_a_different_account_button"])

    def click_on_user_logged_in_sign_in_button(self):
        """Click on 'Sign in' button"""
        self._click(self.AUTH_PAGE_CONTENT_LOCATORS["user_logged_in_sign_in_button"])

    def click_on_enter_your_email_submit_button(self):
        """Click on 'Submit' e-mail button"""
        self._click(self.AUTH_PAGE_CONTENT_LOCATORS["enter_your_email_submit_button"])

    def click_on_enter_your_password_submit_button(self):
        """Click on 'Sign in' password button"""
        self._click(self.AUTH_PAGE_CONTENT_LOCATORS["enter_your_password_submit_button"])

    def click_on_otp_code_confirm_button(self):
        """Click on 'Submit' OTP code button"""
        self._click(self.AUTH_PAGE_CONTENT_LOCATORS["enter_otp_code_confirm_button"])

    def add_data_to_email_input_field(self, text: str):
        """Add data to 'Enter your email' input field"""
        self._fill(self.AUTH_PAGE_CONTENT_LOCATORS["enter_your_email_input_field"], text)

    def add_data_to_password_input_field(self, text: str):
        """Add data to 'Enter your password' input field"""
        self._fill(self.AUTH_PAGE_CONTENT_LOCATORS["enter_your_password_input_field"], text)

    def add_data_to_otp_code_input_field(self, text: str):
        """Add data to 'Enter OTP code' input field"""
        self._fill(self.AUTH_PAGE_CONTENT_LOCATORS["enter_otp_code_input_field"], text)

    def clear_email_input_field(self):
        """Clear 'Enter your email' input field"""
        self._clear_field(self.AUTH_PAGE_CONTENT_LOCATORS["enter_your_email_input_field"])

    def is_use_a_different_account_button_displayed(self) -> bool:
        """Check if 'Use a different account' button is displayed"""
        self._wait_for_selector(self.AUTH_PAGE_CONTENT_LOCATORS["use_a_different_account_button"],
                                timeout=5000)
        return self._is_element_visible(self.AUTH_PAGE_CONTENT_LOCATORS
                                        ["use_a_different_account_button"])

    def is_logged_in_sign_in_button_displayed(self) -> bool:
        """Check if 'Sign in' button is displayed"""
        return self._is_element_visible(
            self.AUTH_PAGE_CONTENT_LOCATORS["user_logged_in_sign_in_button"])

    def is_enter_otp_code_input_field_displayed(self) -> bool:
        """Check if 'Enter OTP code' input field is displayed"""
        self._wait_for_selector(
            self.AUTH_PAGE_CONTENT_LOCATORS["continue_with_firefox_accounts_button"])
        return self._is_element_visible(self.AUTH_PAGE_CONTENT_LOCATORS
                                        ["enter_otp_code_input_field"])

    def is_continue_with_firefox_button_displayed(self) -> bool:
        """Check if 'Continue with Firefox Accounts' button is displayed"""
        self._wait_for_selector(self.AUTH_PAGE_CONTENT_LOCATORS
                                ["continue_with_firefox_accounts_button"])
        return self._is_element_visible(self.AUTH_PAGE_CONTENT_LOCATORS
                                        ["continue_with_firefox_accounts_button"])

    def get_continue_with_firefox_button_locator(self) -> Locator:
        """Get 'Continue with Firefox Accounts' button locator"""
        return self._get_element_locator(self.AUTH_PAGE_CONTENT_LOCATORS
                                         ["continue_with_firefox_accounts_button"])
