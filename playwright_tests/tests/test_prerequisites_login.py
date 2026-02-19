import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.mark.loginSessions
def test_create_user_sessions_for_test_accounts(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    staff_user = utilities.staff_user

    sumo_pages.auth_flow_page.sign_in_flow(
        username=staff_user, account_password=utilities.user_secrets_pass, via_top_navbar=True
    )
    expect(sumo_pages.top_navbar.signed_in_username).to_have_text(
        utilities.username_extraction_from_email(staff_user)
    )
    utilities.store_session_cookies(utilities.username_extraction_from_email(staff_user))


# C3067317
@pytest.mark.loginSessions
def test_new_account_creation(page: Page, restmail_test_account_creation):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    username, password = restmail_test_account_creation

    with check, allure.step("Verifying that the correct username is displayed inside the"
                            " top-navbar and the correct user message banner is displayed"):
        utilities.wait_for_url_to_be(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US, 20000)

        expect(sumo_pages.top_navbar.signed_in_username).to_have_text(
            utilities.username_extraction_from_email(username)
        )
        assert (sumo_pages.homepage.get_user_notification() == HomepageMessages.
                NEW_USER_REGISTRATION_MESSAGE)