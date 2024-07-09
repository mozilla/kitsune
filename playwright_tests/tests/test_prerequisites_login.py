import pytest
from playwright_tests.core.testutilities import TestUtilities
from playwright.sync_api import expect, Page
from playwright_tests.flows.auth_flows.auth_flow import AuthFlowPage
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.mark.loginSessions
def test_create_user_sessions_for_test_accounts(page: Page):
    test_utilities = TestUtilities(page)
    sumo_pages = SumoPages(page)
    auth_flow = AuthFlowPage(page)

    i = 0
    keys = list(test_utilities.user_secrets_accounts.keys())
    tried_once = False
    while i < len(keys):
        sumo_pages.top_navbar._click_on_signin_signup_button()

        # Also acts as a wait. Introduced in order to avoid flakiness which occurred on some
        # GH runs.
        expect(sumo_pages.auth_page._get_continue_with_firefox_button_locator()).to_be_visible()

        auth_flow.sign_in_flow(
            username=test_utilities.user_secrets_accounts[keys[i]],
            account_password=test_utilities.user_secrets_pass
        )

        test_utilities.wait_for_given_timeout(3500)
        username = test_utilities.username_extraction_from_email(
            test_utilities.user_secrets_accounts[keys[i]]
        )
        test_utilities.store_session_cookies(username)

        # Trying to log in. If the login fails, we retry creating the failed session. If we
        # retried once, fail the test.
        test_utilities.start_existing_session(
            username
        )

        if sumo_pages.top_navbar._get_text_of_logged_in_username() != username and not tried_once:
            tried_once = True
        elif sumo_pages.top_navbar._get_text_of_logged_in_username() != username and tried_once:
            pytest.fail(f"Unable to sign in with {username}")
        else:
            i += 1
            test_utilities.delete_cookies()
