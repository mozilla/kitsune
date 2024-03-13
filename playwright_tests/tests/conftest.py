import allure
import pytest
from playwright.sync_api import sync_playwright
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.fixture()
def setup(request, browser, logger_setup):
    requested_browser = browser
    logger = logger_setup
    global page

    with sync_playwright() as playwright:
        if requested_browser == "chrome":
            browser = playwright.chromium.launch()
            context = browser.new_context(record_video_dir="reports/videos")
            page = context.new_page()
        else:
            browser = playwright.firefox.launch()
            context = browser.new_context(record_video_dir="reports/videos")
            page = context.new_page()

        sumo_pages = SumoPages(page)
        logger.info(f"Running tests on: {requested_browser}")
        page.goto(HomepageMessages.STAGE_HOMEPAGE_URL)
        request.cls.page = page
        request.cls.context = context
        request.cls.sumo_pages = sumo_pages
        request.cls.requested_browser = requested_browser
        request.cls.logger = logger
        yield
        page.context.close()
        page.video.delete()


def pytest_addoption(parser):
    parser.addoption("--browser")


@pytest.fixture(scope="class", autouse=True)
def browser(request):
    return request.config.getoption("--browser")


# Clearing the logs from the previous run
@pytest.fixture(scope="session")
def logger_setup():
    logger = TestUtilities().get_logger()

    try:
        log_file = open("../reports/logs/logfile.log", "w")
        log_file.truncate()
        log_file.close()
        logger.info("Cleared previous logs")
    except FileNotFoundError:
        print("No log file found to remove")

    return logger


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport():
    try:
        outcome = yield
        report = outcome.get_result()
        if report.when == "call":
            xfail = hasattr(report, "wasxfail")
            if (report.skipped and xfail) or (report.failed and not xfail):
                allure.attach.file(
                    page.video.path(),
                    name="Video",
                    attachment_type=allure.attachment_type.WEBM
                )
    except Exception as e:
        print(e)
