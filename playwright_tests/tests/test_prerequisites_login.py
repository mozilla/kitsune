import pytest
from playwright.sync_api import Page, expect
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.mark.loginSessions
def test_create_user_sessions_for_test_accounts(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    staff_user = utilities.staff_user

    sumo_pages.top_navbar.click_on_signin_signup_button()
    # Also acts as a wait. Introduced in order to avoid flakiness which occurred on some
    # GH runs.
    expect(sumo_pages.auth_page.continue_with_firefox_accounts_button).to_be_visible()

    sumo_pages.auth_flow_page.sign_in_flow(
        username=staff_user,
        account_password=utilities.user_secrets_pass
    )
    expect(sumo_pages.top_navbar.signed_in_username).to_have_text(
        utilities.username_extraction_from_email(staff_user)
    )
    utilities.store_session_cookies(utilities.username_extraction_from_email(staff_user))
