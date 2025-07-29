from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class AuthPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Auth page content
        self.auth_page_section = page.locator("section.sumo-auth--wrap")
        self.fxa_sign_in_page_header = page.locator("h1.fxa-signin-password-header")
        self.auth_page_main_header = page.locator("h1.sumo-page-heading")
        self.auth_page_subheading_text = page.locator("div.sumo-page-section p")
        self.cant_sign_in_to_my_Mozilla_account_link = page.locator("div.trouble-text a")
        self.continue_with_firefox_accounts_button = page.locator("p.login-button-wrap a")
        self.use_a_different_account_button = page.get_by_role(
            "link", name="Use a different account", exact=True)
        self.user_logged_in_sign_in_button = page.get_by_role(
            "button", name="Sign in", exact=True)
        self.enter_your_email_input_field = page.locator("input[name='email']")
        self.enter_your_email_submit_button = page.get_by_role(
            "button", name='Sign up or sign in', exact=True)
        self.enter_your_password_input_field = page.locator("input[type='password']")
        self.enter_your_password_submit_button = page.get_by_role(
            "button", name="Sign in", exact=True)
        self.enter_otp_code_input_field = page.locator("input#otp-code")
        self.enter_otp_code_confirm_button = page.locator("button#submit-btn")

    def click_on_cant_sign_in_to_my_mozilla_account_link(self):
        """Click on 'Can't sign in to my Mozilla account' link"""
        self._click(self.cant_sign_in_to_my_Mozilla_account_link)

    def click_on_continue_with_firefox_accounts_button(self):
        """Click on 'Continue with Firefox Accounts' button"""
        self._click(self.continue_with_firefox_accounts_button)

    def click_on_use_a_different_account_button(self):
        """Click on 'Use a different account' button"""
        self._click(self.use_a_different_account_button)

    def click_on_user_logged_in_sign_in_button(self):
        """Click on 'Sign in' button"""
        self._click(self.user_logged_in_sign_in_button)

    def click_on_enter_your_email_submit_button(self):
        """Click on 'Submit' e-mail button"""
        self._click(self.enter_your_email_submit_button)

    def click_on_enter_your_password_submit_button(self):
        """Click on 'Sign in' password button"""
        self._click(self.enter_your_password_submit_button)

    def click_on_otp_code_confirm_button(self):
        """Click on 'Submit' OTP code button"""
        self._click(self.enter_otp_code_confirm_button)

    def add_data_to_email_input_field(self, text: str):
        """Add data to 'Enter your email' input field"""
        self._fill(self.enter_your_email_input_field, text)

    def add_data_to_password_input_field(self, text: str):
        """Add data to 'Enter your password' input field"""
        self._fill(self.enter_your_password_input_field, text)

    def add_data_to_otp_code_input_field(self, text: str):
        """Add data to 'Enter OTP code' input field"""
        self._fill(self.enter_otp_code_input_field, text)

    def clear_email_input_field(self):
        """Clear 'Enter your email' input field"""
        self._clear_field(self.enter_your_email_input_field)

    def is_use_a_different_account_button_displayed(self) -> bool:
        """Check if 'Use a different account' button is displayed"""
        self._wait_for_locator(self.use_a_different_account_button, 4500)
        return self._is_element_visible(self.use_a_different_account_button)

    def is_logged_in_sign_in_button_displayed(self) -> bool:
        """Check if 'Sign in' button is displayed"""
        return self._is_element_visible(self.user_logged_in_sign_in_button)

    def is_enter_otp_code_input_field_displayed(self) -> bool:
        """Check if 'Enter OTP code' input field is displayed"""
        self._wait_for_locator(self.continue_with_firefox_accounts_button)
        return self._is_element_visible(self.enter_otp_code_input_field)

    def is_continue_with_firefox_button_displayed(self) -> bool:
        """Check if 'Continue with Firefox Accounts' button is displayed"""
        self._wait_for_locator(self.continue_with_firefox_accounts_button)
        return self._is_element_visible(self.continue_with_firefox_accounts_button)

    def get_continue_with_firefox_button_locator(self) -> Locator:
        """Get 'Continue with Firefox Accounts' button locator"""
        return self.continue_with_firefox_accounts_button
