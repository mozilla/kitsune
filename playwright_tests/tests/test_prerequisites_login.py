import pytest
from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import expect


class TestLoginSessions(TestUtilities):
    # Need to update these tests to fetch the usernames and credentials from GH secrets
    @pytest.mark.loginSessions
    def test_create_user_sessions_for_test_accounts(self):

        i = 0
        keys = list(super().user_secrets_accounts.keys())
        tried_once = False
        while i < len(keys):
            self.sumo_pages.top_navbar._click_on_signin_signup_button()

            # Also acts as a wait. Introduced in order to avoid flakiness which occurred on some
            # GH runs.
            expect(
                self.sumo_pages.auth_page._get_continue_with_firefox_button_locator()
            ).to_be_visible()

            self.sumo_pages.auth_flow_page.sign_in_flow(
                username=super().user_secrets_accounts[keys[i]],
                account_password=super().user_secrets_pass
            )

            self.wait_for_given_timeout(3500)
            username = self.username_extraction_from_email(
                super().user_secrets_accounts[keys[i]]
            )
            self.store_session_cookies(username)

            # Trying to log in. If the login fails, we retry creating the failed session. If we
            # retried once, fail the test.
            self.start_existing_session(
                username
            )

            if self.sumo_pages.top_navbar._get_text_of_logged_in_username(
            ) != username and not tried_once:
                tried_once = True
            elif self.sumo_pages.top_navbar._get_text_of_logged_in_username(
            ) != username and tried_once:
                pytest.fail(f"Unable to sign in with {username}")
            else:
                i += 1

            self.delete_cookies()
