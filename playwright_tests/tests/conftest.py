import random
import string
import requests
import allure
import pytest
from playwright.sync_api import Page
from requests import JSONDecodeError
from slugify import slugify
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright._impl._errors import TargetClosedError

from playwright_tests.pages.sumo_pages import SumoPages


@pytest.fixture(autouse=True)
def navigate_to_homepage(page: Page):
    """
    Sets the default navigation timeout, blocks Pontoon requests, and navigates to the SuMo
    homepage. 502 responses on the initial navigation are retried by `navigate_to_link`. A
    passive response listener records the status of the last main-frame navigation response on
    `page._last_main_nav_status`, so `BasePage._recover_if_on_error_page` can reload the page
    when a click navigates to a 502.
    """
    utilities = Utilities(page)
    page.set_default_navigation_timeout(30000)
    page.route("**/pontoon.mozilla.org/**", utilities.block_request)

    page._last_main_nav_status = None

    def _track_main_nav_status(response):
        try:
            if (response.request.is_navigation_request()
                    and response.frame == page.main_frame):
                page._last_main_nav_status = response.status
        except Exception as e:
            print(f"Nav-status listener ignored error: {e}")

    page.on("response", _track_main_nav_status)
    utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL)
    return page

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call) -> None:
    """
    This pytest hook is triggered after each test execution.
    If a test failure occurred (including pytest assertion failures) we are saving & attaching the
    test execution screencast to the allure report for better debugging.
    """
    outcome = yield  # Capture the result of the test execution.

    # Ensure that the hook is executed during the test execution phase.
    if call.when == "call":
        report = outcome.get_result()  # Retrieve the test execution report.

        # Ensure the test has failed and involves Playwright automation.
        if report.failed and "page" in item.funcargs:
            page: Page = item.funcargs["page"]  # Retrieve the page object from the test args.
            video_path = page.video.path()  # Retrieve the path to the recorded video.
            page.context.close()  # Close the browser context to ensure the video is saved.

            # Attaching the video to the Allure report:
            allure.attach(
                open(video_path, 'rb').read(),
                name=f"{slugify(item.nodeid)}.webm",
                attachment_type=allure.attachment_type.WEBM
            )


@pytest.fixture()
def browser_context_args(browser_context_args):
    """
    Modifying the default browser context to include the custom user agent.
    """
    return {
        "user_agent": Utilities.user_agent,
        "extra_http_headers":{
            f"{Utilities.fxa_browser_challenge_header}": f"{Utilities.fxa_browser_challenge_value}"
        },
        **browser_context_args,
    }


@pytest.fixture()
def create_user_factory(page: Page, request):
    created_users = []
    utilities = Utilities(page)
    session_id = utilities.get_session_id(utilities.username_extraction_from_email(
        utilities.staff_user))

    def _create_user(username: str = None, groups: [str] = None, permissions: [str] = None):
        """
        This helper function creates a test user account.

        Args:
            username (str): The username of the test user account.
            groups (list[str]): The groups to which the user belongs.
            permissions (list[str]): The permissions of the user.
        """
        if username is None:
            username = ''.join(random.choice(
                string.ascii_lowercase + string.digits) for _ in range(10))
        endpoint = HomepageMessages.STAGE_HOMEPAGE_URL_EN_US + "users/api/create"

        request_body = {
            "username": username,
            "groups": groups if groups else [],
            "permissions": permissions if permissions else [],
        }
        print(request_body)

        additional_headers = {
            "Content-Type": "application/json",
            "Cookie": f"session_id={session_id}",
            "User-Agent": Utilities.user_agent
        }

        for attempt in range(3):
            response = requests.post(url=endpoint, json=request_body, headers=additional_headers)
            try:
                data = response.json()
                created_users.append(username)
                print(f"User creation API responded with: {data}")
                return data
            except (ValueError, JSONDecodeError) as e:
                print("The user creation API failed. Retrying")
                utilities.wait_for_given_timeout(5000)

    def _cleanup():
        """
        Test finalizer function which triggers the deletion of the newly created test accounts.
        """
        endpoint = HomepageMessages.STAGE_HOMEPAGE_URL_EN_US + "users/api/trigger-delete"
        for username in created_users:
            print("Deleting created users")
            additional_headers = {
                "Cookie": f"session_id={session_id}",
                "User-Agent": Utilities.user_agent
            }
            request_body = {"username": username}
            requests.post(url=endpoint, json=request_body, headers=additional_headers)


    request.addfinalizer(_cleanup)
    return _create_user

@pytest.fixture()
def restmail_test_account_creation(page: Page, request):
    sumo_pages = SumoPages(page)
    """Creates and deletes a restmail test account on teardown."""
    username = 'Test'.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(3)) + "@restmail.net"
    password = 'Test'.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(3))

    user, user_password = sumo_pages.auth_flow_page.sign_in_flow(
        username=username, account_password=password, via_top_navbar=True, is_restmail=True,
        new_account=True
    )

    browser = page.context.browser

    def _cleanup():
        try:
            sumo_pages.auth_flow_page.delete_test_account_flow(username, password)
        except TargetClosedError as e:
            cleanup_context = browser.new_context(
                extra_http_headers={
                f"{Utilities.fxa_browser_challenge_header}":
                    f"{Utilities.fxa_browser_challenge_value}"
                }
            )
            cleanup_page = cleanup_context.new_page()
            try:
                cleanup_sumo_pages = SumoPages(cleanup_page)
                cleanup_sumo_pages.auth_flow_page.delete_test_account_flow(username, password)
            except Exception as e:
                print(f"Restmail test account cleanup failed: {e}")
            finally:
                cleanup_context.close()

    request.addfinalizer(_cleanup)
    return user, user_password
