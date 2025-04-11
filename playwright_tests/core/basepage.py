import random
from typing import Union
from playwright.sync_api import Page, ElementHandle, Locator
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class BasePage:

    def __init__(self, page: Page):
        self.page = page

    def _get_element_locator(self, xpath: str, with_wait=True) -> Locator:
        """
        This helper function returns the element locator from a given xpath.
        """
        if with_wait:
            self.wait_for_dom_to_load()
        return self.page.locator(xpath)

    def _get_elements_locators(self, xpath: str) -> list[Locator]:
        """
        This helper function returns a list of element locators from a given xpath.
        """
        self.wait_for_dom_to_load()
        return self.page.locator(xpath).all()

    def _get_current_page_url(self) -> str:
        """
        This helper function returns the current page URL.
        """
        return self.page.url

    def _get_element_handles(self, locator: Locator) -> list[ElementHandle]:
        """
        This helper function returns a list of element handles from a given locator.
        """
        self.wait_for_dom_to_load()
        return locator.element_handles()

    def _get_element_handle(self, locator: Locator) -> ElementHandle:
        """
        This helper function returns a single element handle from a given locator.
        """
        self.wait_for_dom_to_load()
        return locator.element_handle()

    def _get_text_of_elements(self, locator: Locator) -> list[str]:
        """
        This helper function returns a list containing the inner texts of a given locator.
        """
        self.wait_for_dom_to_load()
        return locator.all_inner_texts()

    def _get_text_of_element(self, locator: Locator) -> str:
        """
        This helper function returns the inner text of a given locator.
        """
        self.wait_for_dom_to_load()
        return locator.inner_text()

    def _get_text_of_locator(self, locator: Locator) -> str:
        """
        This helper function returns the inner text of a given locator.
        """
        return locator.inner_text()

    def _is_element_empty(self, locator: Locator) -> bool:
        """
        This helper function returns checks if the given locator has an inner text.
        """
        self.wait_for_dom_to_load()
        return not locator.inner_text()

    def _get_elements_count(self, locator: Locator) -> int:
        """
        This helper function returns the web element count from a given locator.
        """
        self.wait_for_dom_to_load()
        return locator.count()

    def _get_element_attribute_value(self, element: Union[str, Locator, list[Locator],
                                     ElementHandle], attribute: str) -> Union[str, list[str]]:
        """
        This helper function returns the given attribute of a given locator or web element.
        """
        if isinstance(element, str):
            return self._get_element_locator(element).get_attribute(attribute)
        elif isinstance(element, list):
            self.wait_for_dom_to_load()
            values = []
            for element in element:
                values.append(element.get_attribute(attribute))
            return values
        else:
            self.wait_for_dom_to_load()
            return element.get_attribute(attribute)

    def _wait_for_given_timeout(self, timeout: float):
        """
        This helper function pauses the execution for a given timeout.
        """
        self.page.wait_for_timeout(timeout)

    def _get_element_input_value(self, locator: Locator) -> str:
        """
        This helper function returns the input value of a given element locator.
        """
        return locator.input_value()

    def _get_element_inner_text_from_page(self, locator: Locator) -> str:
        """
        This helper function returns the inner text of a given locator via the page instance.
        """
        return locator.inner_text()

    def _get_element_text_content(self, locator: Locator) -> str:
        """
        This helper function returns the text content of a given locator via the page instance.
        """
        return locator.text_content()

    def _get_text_content_of_all_locators(self, locator: Locator) -> list[str]:
        """
        This helper function returns a list of text content for the given locator.
        """
        return locator.all_text_contents()

    def _checkbox_interaction(self, element: [str, ElementHandle], check: bool, retries=3,
                              delay=2000):
        """
        This helper function interacts with a checkbox element.

        Args:
        element (Union[str, ElementHandle]): The element locator to interact with.
        check (bool): Whether to check or uncheck the checkbox.
        """
        self.wait_for_networkidle()
        for attempt in range(retries):
            try:
                locator = self._get_element_locator(element) if isinstance(
                    element,str) else element
                if check:
                    locator.check()
                else:
                    locator.uncheck()
                break
            except (PlaywrightTimeoutError, Exception) as e:
                print(f"Checkbox interaction failed. Retrying... {e}")
                if attempt < retries - 1:
                    self.page.wait_for_timeout(delay)
                else:
                    raise Exception("Max retries exceeded. Could not interact with the checkbox")

    def _click(self, element: Union[str, Locator, ElementHandle], expected_locator=None,
               expected_url=None, with_force=False, retries=3, delay=2000):
        """
        This helper function clicks on a given element locator.

        Args:
        element (Union[str, Locator, ElementHandle]): The element locator to click on.
        expected_locator (str): The expected locator to wait for after the click.
        expected_url (str): The expected URL to wait for after the click.
        with_force (bool): Whether to force the click.
        """
        self.wait_for_networkidle()
        for attempt in range(retries):
            try:
                element_locator = self._get_element_locator(element) if isinstance(
                    element, str) else element
                element_locator.click(force=with_force)
                if expected_locator:
                    self._wait_for_locator(expected_locator, timeout=3000)
                if expected_url:
                    self.page.wait_for_url(expected_url, timeout=3000)
                break
            except PlaywrightTimeoutError:
                if expected_locator:
                    print(f"Expected locator {expected_locator} not found. Retrying...")
                if expected_url:
                    print(f"Expected URL {expected_url} not found. Retrying...")
                if attempt < retries - 1:
                    self.page.wait_for_timeout(delay)

    def _click_on_an_element_by_index(self, locator: Locator, index: int):
        """
        This helper function clicks on a given element locator based on a given index.
        """
        self.wait_for_networkidle()
        locator.nth(index).click()

    def _click_on_first_item(self, locator: Locator):
        """
        This helper function clicks on the first item from a given web element locator list.
        """
        self.wait_for_networkidle()
        locator.first.click()

    def _fill(self, locator: Locator, text: str, with_force=False):
        """
        This helper function fills a given text inside a given element locator.
        """
        self.wait_for_dom_to_load()
        locator.fill(text, force=with_force)

    def _type(self, locator: Locator, text: str, delay: int):
        """
        This helper function types a given string inside a given element locator with a given delay
        """
        self.wait_for_dom_to_load()
        locator.type(text=text, delay=delay)

    def _press_a_key(self, locator: Locator, key: str):
        """
        This helper function types a given key inside a given element locator.
        """
        self.wait_for_dom_to_load()
        locator.press(key)

    def _clear_field(self, locator: Locator):
        """
        This helper function clears the given element locator input field.
        """
        self.wait_for_dom_to_load()
        locator.clear()

    def _select_option_by_label(self, locator: Locator, label_name: str):
        """
        This helper function selects an element from a given select box based on label.
        """
        self.wait_for_dom_to_load()
        locator.select_option(label=label_name)

    def _select_option_by_value(self, locator: Locator, value: str):
        """
        This helper function selects a element from a given select box based on value.
        """
        self.wait_for_dom_to_load()
        locator.select_option(value=value)

    def _select_random_option_by_value(self, dropdown_locator: Locator, locator_options: Locator):
        """
        This helper function selects a random option from a given web element locator.
        """
        self.wait_for_dom_to_load()
        elements = []
        for element in locator_options.all():
            locator_value = self._get_element_attribute_value(element, 'value')
            if locator_value == '':
                continue
            else:
                elements.append(locator_value)
        self._select_option_by_value(dropdown_locator, random.choice(elements))

    def _accept_dialog(self):
        """
        This helper function accepts the displayed dialog.
        """
        self.page.on("dialog", lambda dialog: dialog.accept())

    def _hover_over_element(self, locator: Locator):
        """
        This helper function performs a mouse-over action over a given element locator.
        """
        self.wait_for_dom_to_load()
        locator.hover()

    def _is_element_visible(self, locator: Locator) -> bool:
        """
        This helper function finds the locator of the given locator and checks if it is visible.
        """
        self.wait_for_dom_to_load()
        if locator.count() > 0:
            return locator.is_visible()
        else:
            return False

    def _is_locator_visible(self, locator: Locator) -> bool:
        """
        This helper function checks if the given locator is visible.
        """
        return locator.is_visible()

    def _is_checkbox_checked(self, locator: Locator) -> bool:
        """
        This helper function checks if a given element locator is checked.
        """
        self.wait_for_dom_to_load()
        return locator.is_checked()

    def _wait_for_locator(self, locator: Locator, timeout=3500):
        """
        This helper function waits for a given element locator to be visible based on a given
        timeout.
        """
        try:
            locator.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            print(f"{locator} is not displayed")

    def _move_mouse_to_location(self, x: int, y: int):
        """
        This helper function moves the mouse to a given location.

        Args:
        x (int): The x-coordinate.
        y (int): The y-coordinate.
        """
        self.page.mouse.move(x, y)

    def wait_for_page_to_load(self):
        """
        This helper function awaits for the load event to be fired.
        """
        try:
            self.page.wait_for_load_state("load")
        except PlaywrightTimeoutError:
            print("Load event was not fired. Continuing...")

    def eval_on_selector_for_last_child_text(self, element: str) -> str:
        """
        This helper function evaluates a JavaScript expression on the given element and returns
        the text content of the last child element.
        """
        return self.page.eval_on_selector(
            element,
            "el => el.lastChild?.textContent?.trim()"
        )

    def wait_for_dom_to_load(self):
        """
        This helper function awaits for the DOMContentLoaded event to be fired.
        """
        try:
            self.page.wait_for_load_state("domcontentloaded")
        except PlaywrightTimeoutError:
            print("DOMContentLoaded event was not fired. Continuing...")

    def wait_for_networkidle(self):
        """
        This helper function waits until there are no network connections for at least 500ms.
        """
        try:
            self.page.wait_for_load_state("networkidle")
        except PlaywrightTimeoutError:
            print("Network idle state was not reached. Continuing...")
