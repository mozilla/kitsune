from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.pages.auth_page import AuthPage
from playwright_tests.pages.homepage import Homepage


class AuthFlowPage(TestUtilities, AuthPage, Homepage):
    # Providing OTP code to FxA auth.
    def __provide_otp_code(self, otp_code: str):
        super()._add_data_to_otp_code_input_field(otp_code)
        super()._click_on_otp_code_confirm_button()

    # Providing the needed login credentials to FxA auth.
    def __provide_login_credentials_and_submit(self, username: str, password: str):
        super()._add_data_to_email_input_field(username)
        super()._click_on_enter_your_email_submit_button()

        if super()._is_logged_in_sign_in_button_displayed():
            super()._click_on_user_logged_in_sign_in_button()
        else:
            super()._add_data_to_password_input_field(password)
            super()._click_on_enter_your_password_submit_button()

    # Sign in flow.
    def sign_in_flow(
        self, username: str, account_password: str
    ) -> str:

        # Forcing an email clearance
        super().clear_fxa_email(username)

        if super()._is_continue_with_firefox_button_displayed():
            super()._click_on_continue_with_firefox_accounts_button()

        super().clear_session_storage()
        self.__provide_login_credentials_and_submit(username, account_password)

        if super()._is_enter_otp_code_input_field_displayed():
            self.__provide_otp_code(super().get_fxa_verification_code(fxa_username=username))

        return username
