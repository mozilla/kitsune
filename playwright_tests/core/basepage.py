from playwright.sync_api import Page, ElementHandle, Locator, TimeoutError


class BasePage:

    def __init__(self, page: Page):
        self._page = page

    # Single locator retrieval.
    # Waits for DOM load to finish.
    def _get_element_locator(self, xpath: str) -> Locator:
        self.__wait_for_dom_load_to_finnish()
        return self._page.locator(xpath)

    # Multiple locators retrieval.
    # Waits for DOM load to finish.
    def _get_elements_locators(self, xpath: str) -> list[Locator]:
        self.__wait_for_dom_load_to_finnish()
        return self._page.locator(xpath).all()

    # Single locator retrieval without wait.
    def _get_element_locator_no_wait(self, xpath: str) -> Locator:
        return self._page.locator(xpath)

    # Element handle retrieval.
    def _get_element_handles(self, xpath: str) -> list[ElementHandle]:
        return self._get_element_locator(xpath).element_handles()

    # Multiple element handles retrieval.
    def _get_element_handle(self, xpath: str) -> ElementHandle:
        return self._get_element_locator(xpath).element_handle()

    # Multiples elements inner text retrieval.
    def _get_text_of_elements(self, xpath: str) -> list[str]:
        return self._get_element_locator(xpath).all_inner_texts()

    # Element inner text retrieval.
    def _get_text_of_element(self, xpath: str) -> str:
        return self._get_element_locator(xpath).inner_text()

    # Elements count retrieval.
    def _get_elements_count(self, xpath: str) -> int:
        return self._get_element_locator(xpath).count()

    # Fetching a particular element attribute value.
    def _get_element_attribute_value(self, xpath: str, attribute: str) -> str:
        return self._get_element_locator(xpath).get_attribute(attribute)

    # Fetch a particular element locator attribute value.
    def _get_element_locator_attribute_value(self, locator: Locator, attribute: str) -> str:
        self.__wait_for_dom_load_to_finnish()
        return locator.get_attribute(attribute)

    # Fetching a particular element input value.
    def _get_element_input_value(self, xpath: str) -> str:
        return self._get_element_locator(xpath).input_value()

    # Get element inner text from page.
    def _get_element_inner_text_from_page(self, xpath: str) -> str:
        return self._page.inner_text(xpath)

    # Clicking on a particular element.
    def _click(self, xpath: str):
        self._get_element_locator(xpath).click()

    # Clicking on a particular element without wait.
    def _click_without_wait(self, xpath: str):
        self._get_element_locator_no_wait(xpath).click()

    # Filling text to an element input.
    def _fill(self, xpath: str, text: str):
        self._get_element_locator(xpath).fill(text)

    # Typing text inside an input field with a given delay.
    def _type(self, xpath: str, text: str, delay: int):
        self._get_element_locator(xpath).type(text=text, delay=delay)

    # Type inside an input field by pressing a particular key.
    def _press_a_key(self, xpath: str, key: str):
        self._get_element_locator(xpath).press(key)

    # Clearing an input field.
    def _clear_field(self, xpath: str):
        self._get_element_locator(xpath).clear()

    # Clicking on a particular element by index.
    def _click_on_an_element_by_index(self, xpath: str, index: int):
        self._get_element_locator(xpath).nth(index).click()

    # Clicking on the first element from a locator list.
    def _click_on_first_item(self, xpath: str):
        self._get_element_locator(xpath).first.click()

    # Choosing an option by label from a select element.
    def _select_option_by_label(self, xpath: str, label_name: str):
        self._get_element_locator(xpath).select_option(label=label_name)

    # Choosing an option by value from a select element.
    def _select_option_by_value(self, xpath: str, value: str):
        self._get_element_locator(xpath).select_option(value=value)

    # Accept a dialog.
    def _accept_dialog(self):
        self._page.on("dialog", lambda dialog: dialog.accept())

    # Hover over a particular element.
    def _hover_over_element(self, xpath: str):
        self._get_element_locator(xpath).hover()

    # Verifying if a particular element is visible.
    def _is_element_visible(self, xpath: str) -> bool:
        return self._get_element_locator(xpath).is_visible()

    # Verifying if a particular checkbox is checked.
    def _is_checkbox_checked(self, xpath: str) -> bool:
        return self._get_element_locator(xpath).is_checked()

    # Custom wait for DOM load to finish.
    def __wait_for_dom_load_to_finnish(self):
        self._page.wait_for_load_state("domcontentloaded")
        self._page.wait_for_load_state("load")

    # Custom wait for selector to be displayed.
    def _wait_for_selector(self, xpath: str):
        try:
            self._page.wait_for_selector(xpath, timeout=3500)
        except TimeoutError:
            print("Use a different account button is not displayed")

    # Clears the browser session storage and reloads the page after.
    def clear_session_storage(self):
        self._page.evaluate('window.localStorage.clear()')
        self._page.reload()
