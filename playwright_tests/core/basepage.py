from playwright.sync_api import Page, ElementHandle, Locator, TimeoutError


class BasePage:

    def __init__(self, page: Page):
        self._page = page

    def _get_element_locator(self, xpath: str) -> Locator:
        self.__wait_for_dom_load_to_finnish()
        return self._page.locator(xpath)

    def _get_element_locator_no_wait(self, xpath: str) -> Locator:
        return self._page.locator(xpath)

    def _get_element_handles(self, xpath: str) -> list[ElementHandle]:
        return self._get_element_locator(xpath).element_handles()

    def _get_element_handle(self, xpath: str) -> ElementHandle:
        return self._get_element_locator(xpath).element_handle()

    def _get_text_of_elements(self, xpath: str) -> list[str]:
        return self._get_element_locator(xpath).all_inner_texts()

    def _get_text_of_element(self, xpath: str) -> str:
        return self._get_element_locator(xpath).inner_text()

    def _get_elements_count(self, xpath: str) -> int:
        return self._get_element_locator(xpath).count()

    def _get_element_attribute_value(self, xpath: str, attribute: str) -> str:
        return self._get_element_locator(xpath).get_attribute(attribute)

    def _get_element_inner_text_from_page(self, xpath: str) -> str:
        return self._page.inner_text(xpath)

    def _get_element_input_value(self, xpath: str) -> str:
        return self._get_element_locator(xpath).input_value()

    def _click(self, xpath: str):
        self._get_element_locator(xpath).click()

    def _click_without_wait(self, xpath: str):
        self._get_element_locator_no_wait(xpath).click()

    def _fill(self, xpath: str, text: str):
        self._get_element_locator(xpath).fill(text)

    def _type(self, xpath: str, text: str, delay: int):
        self._get_element_locator(xpath).type(text=text, delay=delay)

    def _press_a_key(self, xpath: str, key: str):
        self._get_element_locator(xpath).press(key)

    def _clear_field(self, xpath: str):
        self._get_element_locator(xpath).clear()

    def _click_on_an_element_by_index(self, xpath: str, index: int):
        self._get_element_locator(xpath).nth(index).click()

    def _click_on_first_item(self, xpath: str):
        self._get_element_locator(xpath).first.click()

    def _select_option_by_label(self, xpath: str, label_name: str):
        self._get_element_locator(xpath).select_option(label=label_name)

    def _select_option_by_value(self, xpath: str, value: str):
        self._get_element_locator(xpath).select_option(value=value)

    def _accept_dialog(self):
        self._page.on("dialog", lambda dialog: dialog.accept())

    def _hover_over_element(self, xpath: str):
        self._get_element_locator(xpath).hover()

    def _is_element_visible(self, xpath: str) -> bool:
        return self._get_element_locator(xpath).is_visible()

    def _is_checkbox_checked(self, xpath: str) -> bool:
        return self._get_element_locator(xpath).is_checked()

    def __wait_for_dom_load_to_finnish(self):
        self._page.wait_for_load_state("domcontentloaded")
        self._page.wait_for_load_state("load")

    def _wait_for_selector(self, xpath: str):
        try:
            self._page.wait_for_selector(xpath, timeout=3500)
        except TimeoutError:
            print("Use a different account button is not displayed")
