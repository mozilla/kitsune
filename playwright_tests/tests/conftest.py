import warnings

import allure
import pytest
from playwright.sync_api import Page
from slugify import slugify
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages


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
        if response.status == 502:
            warnings.warn("502 encountered")
            page = response.request.frame.page
            print("502 error encountered. Reloading the page after 5 seconds.")
            page.wait_for_timeout(5000)
            page.reload()

    page.context.on("response", handle_502_error)

    # Navigate to the SUMO stage homepage.
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
