import pytest
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.homepage_messages import HomepageMessages
from selenium_tests.pages.pages import Pages


@pytest.fixture(params=["chrome", "firefox"])
def setup(request, driver_setup, logger_setup):
    browser = request.param
    logger = logger_setup

    if browser == "chrome":
        driver = webdriver.Chrome(executable_path=driver_setup[0])
    else:
        driver = webdriver.Firefox(executable_path=driver_setup[1])

    pages = Pages(driver)

    logger.info(f"Running tests on {browser} browser")

    driver.get(HomepageMessages.STAGE_HOMEPAGE_URL)
    driver.maximize_window()

    request.cls.pages = pages
    request.cls.driver = driver
    request.cls.browser = browser
    request.cls.logger = logger
    yield
    driver.quit()

# Using DriverManager to fetch the necessary drivers automatically and returning their location
@pytest.fixture(scope='session')
def driver_setup():
    chrome_driver_path = ChromeDriverManager().install()
    firefox_driver_path = GeckoDriverManager().install()

    drivers = [chrome_driver_path, firefox_driver_path]

    return drivers

# Instantiating a logger instance to be used in our entire testing session & clearing the logs from the previous run
@pytest.fixture(scope='session')
def logger_setup():
    logger = TestUtilities().get_logger()

    try:
        log_file = open("reports/logs/logfile.log", "w")
        log_file.truncate()
        log_file.close()
        logger.info("Cleared previous logs")
    except:
        print("No log file found to remove")

    return logger
