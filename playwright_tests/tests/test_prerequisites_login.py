import pytest
from playwright_tests.core.utilities import Utilities
from playwright.sync_api import expect, Page
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.mark.loginSessions
def test_create_user_sessions_for_test_accounts(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    i = 0
    keys = list(utilities.user_secrets_accounts.keys())
    tried_once = False
    while i < len(keys):
        sumo_pages.top_navbar.click_on_signin_signup_button()

        # Also acts as a wait. Introduced in order to avoid flakiness which occurred on some
        # GH runs.
        expect(sumo_pages.auth_page.get_continue_with_firefox_button_locator()).to_be_visible()

        sumo_pages.auth_flow_page.sign_in_flow(
            username=utilities.user_secrets_accounts[keys[i]],
            account_password=utilities.user_secrets_pass
        )

        utilities.wait_for_given_timeout(3500)
        username = utilities.username_extraction_from_email(
            utilities.user_secrets_accounts[keys[i]]
        )
        utilities.store_session_cookies(username)

        # Trying to log in. If the login fails, we retry creating the failed session. If we
        # retried once, fail the test.
        utilities.start_existing_session(
            username
        )

        if sumo_pages.top_navbar.get_text_of_logged_in_username() != username and not tried_once:
            tried_once = True
        elif sumo_pages.top_navbar.get_text_of_logged_in_username() != username and tried_once:
            pytest.fail(f"Unable to sign in with {username}")
        else:
            i += 1
            utilities.delete_cookies()
