from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.pages.auth_page import AuthPage
from selenium_tests.pages.homepage import Homepage


class AuthFlowPage(TestUtilities, AuthPage, Homepage):
    def __provide_otp_code(self, otp_code: str):
        super().add_data_to_otp_code_input_field(otp_code)
        super().click_on_otp_code_confirm_button()

    def __provide_login_credentials_and_submit(self, username: str, password: str):
        super().add_data_to_email_input_field(username)
        super().click_on_enter_your_email_submit_button()

        if super().is_logged_in_sign_in_button_displayed():
            super().click_on_user_logged_in_sign_in_button()
        else:
            super().add_data_to_password_input_field(password)
            super().click_on_enter_your_password_submit_button()

    def sign_in_flow(
        self, username: str, account_password: str, sign_in_with_same_account: bool
    ) -> str:
        # Forcing an email clearance
        super().clear_fxa_email(username)

        if super().is_continue_with_firefox_button_displayed():
            super().click_on_continue_with_firefox_accounts_button()

        if super().is_use_a_different_account_button_displayed() and not sign_in_with_same_account:
            super().click_on_use_a_different_account_button()
            super().clear_email_input_field()
            self.__provide_login_credentials_and_submit(username, account_password)
        elif super().is_logged_in_sign_in_button_displayed() and sign_in_with_same_account:
            super().click_on_user_logged_in_sign_in_button()
        else:
            self.__provide_login_credentials_and_submit(username, account_password)

        if super().is_enter_otp_code_input_field_displayed():
            self.__provide_otp_code(super().get_fxa_verification_code(fxa_username=username))

        return self.username_extraction_from_email(username)
