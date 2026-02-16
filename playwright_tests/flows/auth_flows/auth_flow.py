from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.auth_page import AuthPage
from playwright_tests.pages.top_navbar import TopNavbar


class AuthFlowPage:

    def __init__(self, page: Page):
        self.page = page
        self.utilities = Utilities(page)
        self.auth_page = AuthPage(page)
        self.top_navbar = TopNavbar(page)

    # Providing OTP code to FxA auth.
    def __provide_otp_code(self, otp_code: str, new_account: bool = False):
        """Add data to 'Enter your OTP code' input field and click on 'Submit' button

        Args:
            otp_code (str): OTP code to be added to the input field.
            new_account (str): If the user is a new fxa account.
        """
        if new_account:
            self.auth_page.add_data_to_new_account_otp_code_input_field(otp_code)
        else:
            self.auth_page.add_data_to_otp_code_input_field(otp_code)
        self.auth_page.click_on_otp_code_confirm_button()

    # Providing the needed login credentials to FxA auth.
    def __provide_login_credentials_and_submit(self, username: str, password: str,
                                               new_account: bool = False):
        """Provide login credentials to FxA auth and submit them.

        Args:
            username (str): Username to be added to the input field.
            password (str): Password to be added to the input field.
            new_account (bool): If we are creating a new fxa test account.
        """
        self.auth_page.add_data_to_email_input_field(username)
        self.auth_page.click_on_enter_your_email_submit_button()

        self.auth_page.add_data_to_password_input_field(password)
        with self.utilities.page.expect_navigation():
            if new_account:
                self.auth_page.click_on_create_account_button()
            else:
                self.auth_page.click_on_enter_your_password_submit_button()

    def login_with_existing_session(self):
        """Login with an existing session."""
        if self.auth_page.is_continue_with_firefox_button_displayed():
            """If the 'Continue with Firefox Accounts' button is displayed, click on it."""
            self.auth_page.click_on_continue_with_firefox_accounts_button()
        self.auth_page.click_on_user_logged_in_sign_in_button()

    # Sign in flow.
    def sign_in_flow(self, username: str, account_password: str, via_top_navbar: bool = False,
                     is_restmail: bool = False, new_account: bool = False) -> [str, str]:
        """Sign in flow.

        Args:
            username (str): Username to be used for sign in.
            account_password (str): Password to be used for sign in.
            via_top_navbar (bool): If the login should be initiated via the top-navbar.
            is_restmail (bool): If restmail test user.
            new_account (bool): If creating a new test user fxa account.
        """
        if via_top_navbar:
            self.top_navbar.click_on_signin_signup_button()
            # Also acts as a wait. Introduced in order to avoid flakiness which occurred on some
            # GH runs.
            self.auth_page.continue_with_firefox_accounts_button.wait_for(timeout=5000)

        if self.auth_page.is_continue_with_firefox_button_displayed():
            """If the 'Continue with Firefox Accounts' button is displayed, click on it."""
            self.auth_page.click_on_continue_with_firefox_accounts_button()

        if self.auth_page.is_use_a_different_account_button_displayed():
            """If the 'Use a different account' button is displayed, click on it."""
            self.auth_page.click_on_use_a_different_account_button()

        self.__provide_login_credentials_and_submit(username, account_password, new_account)
        if self.auth_page.is_enter_otp_code_input_field_displayed():
            """If the OTP code input field is displayed, provide the OTP code."""
            self.__provide_otp_code(self.utilities.get_fxa_verification_code(
                restmail_username=username if is_restmail else None, new_account=new_account
            ), new_account=new_account
            )
        self.utilities.wait_for_dom_to_load()
        return username, account_password

    def delete_test_account_flow(self, username: str, password: str):
        self.page.goto(self.utilities.different_endpoints['fxa_stage'])
        try:
            self.auth_page.enter_your_email_input_field.wait_for(state="visible", timeout=3500)
            self.auth_page.add_data_to_email_input_field(username)
            self.auth_page.click_on_enter_your_email_submit_button()
            self.auth_page.add_data_to_password_input_field(password)
            self.auth_page.click_on_enter_your_password_submit_button()
        except PlaywrightTimeoutError:
            self.auth_page.click_on_user_logged_in_sign_in_button()
        self.auth_page.click_on_delete_account_button()
        self.auth_page.check_all_acknowledge_fxa_page_checkboxes()
        self.auth_page.click_on_continue_deletion_button()
        self.auth_page.add_fxa_password(password)
        self.auth_page.click_on_the_delete_confirmation_button()
