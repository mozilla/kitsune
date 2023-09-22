from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


# Abstract all common actions into this central location.


class BasePage:
    def __init__(self, driver: WebDriver):
        self._driver = driver

    def current_url(self) -> str:
        return self._driver.current_url

    def navigate_back(self):
        self._driver.back()

    def navigate_forward(self):
        self._driver.forward()

    def navigate_to(self, link):
        self._driver.get(link)

    def _find_element(self, locator: tuple) -> WebElement:
        self.__wait_until_element_is_visible(locator)
        return self._driver.find_element(*locator)

    def _find_elements(self, locator: tuple) -> list[WebElement]:
        self.__wait_until_element_is_visible(locator)
        return self._driver.find_elements(*locator)

    def _type(self, locator: tuple, text: str):
        self._find_element(locator).send_keys(text)

    def _upload_jpg_image(self, locator: tuple, path_to_image: str):
        self._find_element(locator).send_keys(path_to_image)

    def _clear_input_field(self, locator: tuple):
        self._find_element(locator).clear()

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

    def _get_value_of_web_element_attribute(self, web_element: tuple) -> str:
        return self._find_element(web_element).get_attribute("value")

    def _get_values_of_web_elements_attributes(self, web_element: tuple) -> list[str]:
        web_elements = self._find_elements(web_element)
        values = []
        for element in web_elements:
            values.append(element.get_attribute("value"))
        return values

    def _get_attribute_value_of_web_element(self, web_element: tuple, attribute: str) -> str:
        return self._find_element(web_element).get_attribute(attribute)

    def _get_value_of_css_property(self, web_element: tuple, text: str) -> str:
        return self._find_element(web_element).value_of_css_property(text)

    def _get_css_value_of_pseudo_html_element(
        self, locator: str, pseudo_element_locator: str, property_to_get: str
    ) -> str:
        script = (
            f"return window.getComputedStyle(document.querySelector('{locator}'),"
            f"'{pseudo_element_locator}').getPropertyValue('{property_to_get}')"
        )
        return self._driver.execute_script(script)

    def _get_number_of_elements(self, locator: tuple) -> int:
        return len(self._find_elements(locator))

    # Select functions

    def _select_option_by_value(self, web_element: tuple, value: str):
        select_element = Select(self._find_element(web_element))
        select_element.select_by_value(value)

    def _select_option_by_text(self, web_element: tuple, text: str):
        select_element = Select(self._find_element(web_element))
        select_element.select_by_visible_text(text)

    def _clear_select_option_field(self, web_element: tuple):
        select_element = Select(self._find_element(web_element))
        select_element.deselect_all()

    def _get_select_chosen_option(self, web_element: tuple) -> str:
        select_element = Select(self._find_element(web_element))
        selected_element = select_element.first_selected_option
        return selected_element.text

    # ActionsChains class functions
    def _mouseover_element(self, locator: tuple):
        action = ActionChains(self._driver)
        action.move_to_element(self._find_element(locator)).perform()

    def _mouseover_web_element(self, element: WebElement):
        action = ActionChains(self._driver)
        action.move_to_element(element).perform()

    def _scroll_element_in_view(self, locator: tuple):
        self._driver.execute_script("window.scrollTo(0, arguments[0].offsetTop);", locator)

    def _press_home_keyboard_button(self):
        actions = ActionChains(self._driver)
        actions.send_keys(Keys.HOME).perform()

    def _press_enter_keyboard_button(self):
        actions = ActionChains(self._driver)
        actions.send_keys(Keys.ENTER).perform()

    # Alert handling
    def _accept_alert(self):
        try:
            self.__wait_until_alert_is_present()
            self._driver.switch_to.alert.accept()

        except TimeoutException:
            print("No alert is present")

    def _dismiss_alert(self):
        try:
            self.__wait_until_alert_is_present()
            self._driver.switch_to.alert.dismiss()

        except TimeoutException:
            print("No alert is present")

    def _switch_next_child_tab(self):
        current_window_handle = self._driver.current_window_handle
        first_child_window = self._driver.window_handles

        for window in first_child_window:
            if window != current_window_handle:
                self._driver.switch_to.window(window)

    def _is_element_displayed(self, locator: tuple) -> bool:
        try:
            return self._find_element(locator).is_displayed()
        except NoSuchElementException:
            return False
        except TimeoutException:
            return False

    def _is_element_selected(self, locator: tuple) -> bool:
        return self._find_element(locator).is_selected()

    def _is_web_element_selected(self, web_element: WebElement) -> bool:
        return web_element.is_selected()

    def __wait_until_element_is_visible(self, locator: tuple, time: int = 2):
        wait = WebDriverWait(self._driver, time)
        wait.until(ec.visibility_of_element_located(locator))

    def wait_until_page_is(self, url: str, time: int = 5):
        wait = WebDriverWait(self._driver, time)
        wait.until(ec.url_to_be(url))

    def __wait_until_alert_is_present(self, time: int = 4):
        wait = WebDriverWait(self._driver, time)
        wait.until(ec.alert_is_present(), "No alert is displayed")

    def wait_for_url_title_to_contain(self, url: str):
        wait = WebDriverWait(self._driver, 5)
        wait.until(ec.title_contains(url))

    def _wait_for_element_to_be_clickable(self, locator: tuple, time: int = 10):
        wait = WebDriverWait(self._driver, time)
        wait.until(ec.element_to_be_clickable(locator))
