from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.auth_page import AuthPage


class AuthFlowPage:

    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.auth_page = AuthPage(page)

    # Providing OTP code to FxA auth.
    def __provide_otp_code(self, otp_code: str):
        """Add data to 'Enter your OTP code' input field and click on 'Submit' button

        Args:
            otp_code (str): OTP code to be added to the input field.
        """
        self.auth_page.add_data_to_otp_code_input_field(otp_code)
        self.auth_page.click_on_otp_code_confirm_button()

    # Providing the needed login credentials to FxA auth.
    def __provide_login_credentials_and_submit(self, username: str, password: str):
        """Provide login credentials to FxA auth and submit them.

        Args:
            username (str): Username to be added to the input field.
            password (str): Password to be added to the input field
        """
        self.auth_page.add_data_to_email_input_field(username)
        self.auth_page.click_on_enter_your_email_submit_button()

        self.auth_page.add_data_to_password_input_field(password)
        with self.utilities.page.expect_navigation():
            self.auth_page.click_on_enter_your_password_submit_button()

    def login_with_existing_session(self):
        """Login with an existing session."""
        if self.auth_page.is_continue_with_firefox_button_displayed():
            """If the 'Continue with Firefox Accounts' button is displayed, click on it."""
            self.auth_page.click_on_continue_with_firefox_accounts_button()
        self.auth_page.click_on_user_logged_in_sign_in_button()

    # Sign in flow.
    def sign_in_flow(self, username: str, account_password: str) -> str:
        """Sign in flow.

        Args:
            username (str): Username to be used for sign in.
            account_password (str): Password to be used for sign in.
        """
        # Forcing an email clearance
        self.utilities.clear_fxa_email(username)

        if self.auth_page.is_continue_with_firefox_button_displayed():
            """If the 'Continue with Firefox Accounts' button is displayed, click on it."""
            self.auth_page.click_on_continue_with_firefox_accounts_button()

        if self.auth_page.is_use_a_different_account_button_displayed():
            """If the 'Use a different account' button is displayed, click on it."""
            self.auth_page.click_on_use_a_different_account_button()

        self.__provide_login_credentials_and_submit(username, account_password)

        if self.auth_page.is_enter_otp_code_input_field_displayed():
            """If the OTP code input field is displayed, provide the OTP code."""
            self.__provide_otp_code(self.utilities.get_fxa_verification_code(
                fxa_username=username))
        self.utilities.wait_for_dom_to_load()
        return username
