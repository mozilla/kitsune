import os.path
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.homepage_messages import HomepageMessages
from selenium_tests.pages.pages import Pages


@pytest.fixture()
def setup(request, logger_setup, browser):
    browser = browser
    logger = logger_setup
    global driver

    if browser == "chrome":
        browser_options = ChromeOptions()
        browser_options.add_argument("-disable-gpu")
        browser_options.add_argument("--no-sandbox")
        browser_options.add_argument("--log-level=3")
        browser_options.add_argument("--ignore-ssl-errors=yes")
        browser_options.add_argument("--ignore-certificate-errors")
        browser_options.add_argument("--force-device-scale-factor=0.1")
        browser_options.add_argument("start-maximized")

    else:
        browser_options = FirefoxOptions()
        browser_options.add_argument("-disable-gpu")
        browser_options.add_argument("--no-sandbox")
        browser_options.set_preference("log.level", "warn")
        browser_options.add_argument("start-maximized")

    driver = webdriver.Remote(
        command_executor="http://0.0.0.0:4444/wd/hub", options=browser_options
    )

    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    driver.implicitly_wait(3)
    driver.maximize_window()
    pages = Pages(driver)
    logger.info(f"Running tests on {browser} browser")
    driver.get(HomepageMessages.STAGE_HOMEPAGE_URL)

    request.cls.pages = pages
    request.cls.driver = driver
    request.cls.browser = browser
    request.cls.logger = logger
    yield
    driver.quit()


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
        log_file = open("reports/logs/logfile.log", "w")
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
                driver.save_screenshot(destination_file)
                if file_name:
                    html = (
                        '<div><img src="%s" alt="screenshot" style="width:300px; height=200px"'
                        'onclick="window.open(this.src)" align="right"/></div>' % file_name
                    )

                extra.append(pytest_html.extras.html(html))
            report.extra = extra
    except Exception as e:
        print(e)
