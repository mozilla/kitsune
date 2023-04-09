import socket
import pytest
import docker

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.messages.homepage_messages import HomepageMessages
from selenium_tests.pages.pages import Pages


@pytest.fixture(params=["chrome", "firefox"])
def setup(request, logger_setup, get_docker_container_ip):
    browser = request.param
    logger = logger_setup
    selenium_hub_ip = get_docker_container_ip

    if browser == "chrome":
        browser_options = ChromeOptions()
        browser_options.add_argument("-headless")
        browser_options.add_argument("-window-size=1200x600")
        browser_options.add_argument("-disable-gpu")
        browser_options.add_argument("--log-level=3")

    else:
        browser_options = FirefoxOptions()
        browser_options.add_argument("-headless")
        browser_options.add_argument("-window-size=1200x600")
        browser_options.add_argument("-disable-gpu")
        browser_options.log.level = "warn"

    driver = webdriver.Remote(
        command_executor=f"http://{selenium_hub_ip}:4444", options=browser_options
    )

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


@pytest.fixture(scope="session")
def get_docker_container_ip():
    client = docker.from_env()
    container = client.containers.get("selenium-hub")
    ip_address = container.attrs["NetworkSettings"]["IPAddress"]

    return socket.gethostbyname(ip_address)
