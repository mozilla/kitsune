import pytest
from playwright.sync_api import Page, expect

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.mark.loginSessions
def test_create_user_sessions_for_test_accounts(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    sumo_pages.top_navbar.click_on_signin_signup_button()

    # Also acts as a wait. Introduced in order to avoid flakiness which occurred on some
    # GH runs.
    expect(sumo_pages.auth_page.get_continue_with_firefox_button_locator()).to_be_visible()

    sumo_pages.auth_flow_page.sign_in_flow(
        username=utilities.staff_user,
        account_password=utilities.user_secrets_pass
    )
    utilities.wait_for_given_timeout(3500)
    username = utilities.username_extraction_from_email(utilities.staff_user)
    utilities.store_session_cookies(username)
