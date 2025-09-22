import random
import string
import warnings
import requests
import allure
import pytest
from playwright.sync_api import Page, Error
from requests import JSONDecodeError
from slugify import slugify
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright._impl._errors import TimeoutError


@pytest.fixture(autouse=True)
def navigate_to_homepage(page: Page):
    """
    This fixture is used in all functions. It navigates to the SuMo homepage and returns the page
    object.
    """
    utilities = Utilities(page)
    # Set default navigation timeout to 30 seconds.
    page.set_default_navigation_timeout(30000)

    # Block pontoon requests in the current page context.
    page.route("**/pontoon.mozilla.org/**", utilities.block_request)

    def handle_502_error(response):
        """
        This function is used to handle 502 errors. It reloads the page after 5 seconds if a
        502 error is encountered.
        """
        for attempt in range(5):
            if response.status == 502:
                warnings.warn("502 encountered")
                page = response.request.frame.page
                print("502 error encountered. Reloading the page after 5 seconds.")
                page.wait_for_timeout(5000)
                try:
                    utilities.refresh_page()
                    return
                except TimeoutError:
                    print("TimeoutError encountered after reload.")

    page.context.on("response", handle_502_error)

    # Navigate to the SUMO stage homepage.
    page.goto(HomepageMessages.STAGE_HOMEPAGE_URL)

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
def browser_context_args(browser_context_args, tmpdir_factory: pytest.TempdirFactory):
    """
    Modifying the default browser context to include the location of the browser session screencast
    and the custom user agent.
    """
    return {
        "user_agent": Utilities.user_agent,
        **browser_context_args,
        "record_video_dir": tmpdir_factory.mktemp('videos')
    }


@pytest.fixture()
def create_user_factory(page: Page, request):
    created_users = []
    utilities = Utilities(page)
    session_id = utilities.get_session_id(utilities.username_extraction_from_email(
        utilities.staff_user))

    def _create_user(username: str = None, groups: [str] = None, permissions: [str] = None):
        """
        This helper function which creates a test user account.

        Args:
            username (str): The username of the test user account
            groups (list[str]): The groups to which the user belongs
            permissions (list[str]): The permissions of the user
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
