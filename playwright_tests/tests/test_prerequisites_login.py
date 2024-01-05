import pytest
from playwright_tests.core.testutilities import TestUtilities


class TestLoginSessions(TestUtilities):
    # Need to update these tests to fetch the usernames and credentials from GH secrets
    @pytest.mark.loginSessions
    def test_create_user_sessions_for_test_accounts(self):

        for i in super().user_secrets_accounts:
            self.sumo_pages.top_navbar._click_on_signin_signup_button()

            self.sumo_pages.auth_flow_page.sign_in_flow(
                username=super().user_secrets_accounts[i],
                account_password=super().user_secrets_pass
            )

            print(super().user_secrets_accounts[i])
            self.wait_for_given_timeout(3500)
            username = self.username_extraction_from_email(
                super().user_secrets_accounts[i]
            )
            print(username)
            self.store_session_cookies(username)
            # Deleting cookies from browser storage (avoiding server invalidation from logout)
            # and reloading the page to be signed out before re-entering the loop.
            self.delete_cookies()
            self.page.reload()
