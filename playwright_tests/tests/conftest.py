import allure
import pytest
from playwright.sync_api import Page
from slugify import slugify

from playwright_tests.messages.homepage_messages import HomepageMessages


@pytest.fixture(autouse=True)
def navigate_to_homepage(page: Page):
    """
    This fixture is used in all functions. It navigates to the SuMo homepage and returns the page
    object.
    """
    page.set_default_navigation_timeout(120000)
    page.goto(HomepageMessages.STAGE_HOMEPAGE_URL)
    return page


def pytest_runtest_makereport(item, call) -> None:
    """
    If there is a test failure we are saving & attaching the test execution's screencast to
    allure reporting.
    """
    if call.when == "call":
        if call.excinfo is not None and "page" in item.funcargs:
            page: Page = item.funcargs["page"]

            video_path = page.video.path()
            page.context.close()  # ensure video saved
            allure.attach(
                open(video_path, 'rb').read(),
                name=f"{slugify(item.nodeid)}.webm",
                attachment_type=allure.attachment_type.WEBM
            )


@pytest.fixture()
def browser_context_args(browser_context_args, tmpdir_factory: pytest.TempdirFactory):
    """
    Modifying the default browser context to include the location of the browser session screencast
    """
    return {
        **browser_context_args,
        "record_video_dir": tmpdir_factory.mktemp('videos')
    }
