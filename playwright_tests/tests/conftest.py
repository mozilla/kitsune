import os

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
            context = browser.new_context()
            page = context.new_page()
        else:
            browser = playwright.firefox.launch()
            context = browser.new_context()
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
        context.close()


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
def pytest_runtest_makereport(item):
    try:
        pytest_html = item.config.pluginmanager.getplugin("html")
        outcome = yield
        report = outcome.get_result()
        extra = getattr(report, "extra", [])
        if report.when == "call":
            xfail = hasattr(report, "wasxfail")
            if (report.skipped and xfail) or (report.failed and not xfail):
                report_directory = "reports/"
                file_name_edit = report.nodeid.split("::")
                file_name = file_name_edit[2] + ".png"
                destination_file = os.path.join(report_directory, file_name)
                page.screenshot(path=destination_file, full_page=True)
                if file_name:
                    html = (
                        '<div><img src="%s" alt="screenshot" style="width:300px; height=200px"'
                        'onclick="window.open(this.src)" align="right"/></div>' % file_name
                    )

                    extra.append(pytest_html.extras.html(html))
            report.extra = extra
    except Exception as e:
        print(e)
