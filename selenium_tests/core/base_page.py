from selenium.common import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


# Abstract all common actions into this central location.


class BasePage:
    def __init__(self, driver: WebDriver):
        self._driver = driver

    def navigate_back(self):
        self._driver.back()

    def navigate_forward(self):
        self._driver.forward()

    def navigate_to(self, link):
        self._driver.get(link)

    def _find_element(self, locator: tuple) -> WebElement:
        self._wait_until_element_is_visible(locator)
        return self._driver.find_element(*locator)

    def _find_elements(self, locator: tuple) -> list[WebElement]:
        self._wait_until_element_is_visible(locator)
        return self._driver.find_elements(*locator)

    def _type(self, locator: tuple, text: str):
        self._find_element(locator).send_keys(text)

    def _click(self, locator: tuple):
        self._find_element(locator).click()

    def _click_on_web_element(self, web_element: WebElement):
        web_element.click()

    def _get_text_of_element(self, locator: tuple) -> str:
        return self._find_element(locator).text

    def _get_text_of_elements(self, locator: tuple) -> list[str]:
        text = []
        elements = self._find_elements(locator)
        for element in elements:
            text.append(element.text)
        return text

    def _get_number_of_elements(self, locator: tuple) -> int:
        return len(self._find_elements(locator))

    @property
    def current_url(self) -> str:
        return self._driver.current_url

    def is_element_displayed(self, locator: tuple) -> bool:
        try:
            return self._find_element(locator).is_displayed()
        except NoSuchElementException:
            return False

    def _wait_until_element_is_visible(self, locator: tuple, time: int = 5):
        wait = WebDriverWait(self._driver, time)
        wait.until(ec.visibility_of_element_located(locator))
