import random
import time

from playwright.sync_api import ElementHandle, Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

# How long a click on a link or form submit gets to start its page load before the page is
# asked whether it handled the click itself (e.g. a form posted by JS in the background).
NAVIGATION_START_WINDOW = 0.3

# How long a click the page did not handle gets to start the page load the browser owes it,
# before it is treated as a click that did not take and retried.
NAVIGATION_EXPECTED_WINDOW = 5

# How long a page load the click started gets to commit the new page (or turn into a download).
NAVIGATION_COMMIT_TIMEOUT = 30

# Describes the click target: whether it is a link to another page or a form submit, and if
# so starts recording whether the click (and the form submit) reach the page unhandled, i.e.
# without a script calling preventDefault().
PREPARE_CLICK_JS = """el => {
    const target = {navigates: false, submit: false, formValid: true};
    const link = el.closest('a[href]');
    if (link) {
        const href = link.getAttribute('href').trim().toLowerCase();
        const url = new URL(link.href, location.href);
        const samePage = url.origin + url.pathname + url.search
                         === location.origin + location.pathname + location.search;
        target.navigates = !(href.startsWith('#') || href.startsWith('javascript:')
                             || link.target === '_blank' || link.hasAttribute('download')
                             || (samePage && url.hash));
    } else {
        const button = el.closest('button, input[type=submit], input[type=image]');
        const form = el.matches('form') ? el
            : (button && ['submit', 'image'].includes(button.type) ? button.form : null);
        if (form) {
            target.navigates = target.submit = true;
            target.formValid = form.noValidate || (button && button.formNoValidate)
                               || form.checkValidity();
        }
    }
    if (target.navigates) {
        window.__sumoClick = {clicked: false, clickPrevented: false,
                              submitted: false, submitPrevented: false};
        window.addEventListener('click', e => Object.assign(
            window.__sumoClick, {clicked: true, clickPrevented: e.defaultPrevented}),
            {once: true});
        window.addEventListener('submit', e => Object.assign(
            window.__sumoClick, {submitted: true, submitPrevented: e.defaultPrevented}),
            {once: true});
    }
    return target;
}"""


class BasePage:

    def __init__(self, page: Page):
        self.page = page

    def _get_element_locator(self, xpath: str) -> Locator:
        """Returns the element locator for a given selector."""
        return self.page.locator(xpath)

    def _get_current_page_url(self) -> str:
        """Returns the current page URL."""
        return self.page.url

    def _get_element_handles(self, locator: Locator) -> list[ElementHandle]:
        """Returns a list of element handles from a given locator."""
        return locator.element_handles()

    def _get_element_handle(self, locator: Locator) -> ElementHandle:
        """Returns a single element handle from a given locator."""
        return locator.element_handle()

    def _get_text_of_elements(self, locator: Locator) -> list[str]:
        """Returns a list of inner texts for a given locator."""
        return locator.all_inner_texts()

    def _get_text_of_element(self, locator: Locator) -> str:
        """Returns the inner text of a given locator."""
        return locator.inner_text()

    def _is_element_empty(self, locator: Locator) -> bool:
        """Returns True if the locator has no inner text."""
        return not locator.inner_text()

    def _get_elements_count(self, locator: Locator) -> int:
        """Returns the element count for a given locator."""
        return locator.count()

    def _get_element_attribute_value(
        self, element: str | Locator | list[Locator] | ElementHandle, attribute: str
    ) -> str | list[str]:
        """Returns the attribute value(s) of a given locator or element."""
        if isinstance(element, str):
            return self._get_element_locator(element).get_attribute(attribute)
        elif isinstance(element, list):
            return [el.get_attribute(attribute) for el in element]
        else:
            return element.get_attribute(attribute)

    def _wait_for_given_timeout(self, timeout: float):
        """Pauses execution for a given timeout in milliseconds."""
        self.page.wait_for_timeout(timeout)

    def _get_element_input_value(self, locator: Locator) -> str:
        """Returns the input value of a given locator."""
        return locator.input_value()

    def _get_element_text_content(self, locator: Locator) -> str:
        """Returns the text content of a given locator."""
        return locator.text_content()

    def _get_text_content_of_all_locators(self, locator: Locator) -> list[str]:
        """Returns a list of text content for the given locator."""
        return locator.all_text_contents()

    def _checkbox_interaction(self, element: str | Locator, check: bool, retries=3, delay=500):
        """Checks or unchecks a checkbox element with retry logic.

        Args:
            element: The element locator or selector string.
            check: Whether to check (True) or uncheck (False) the checkbox.
        """
        for attempt in range(retries):
            try:
                locator = self._get_element_locator(element) if isinstance(element, str) else element
                if check:
                    locator.check()
                else:
                    locator.uncheck()
                break
            except PlaywrightTimeoutError as e:
                print(f"Checkbox interaction failed. Retrying... {e}")
                if attempt < retries - 1:
                    self.page.wait_for_timeout(delay)
                else:
                    raise
            except PlaywrightError as e:
                # A click which lands while the layout settles leaves the state unchanged;
                # check()/uncheck() only click when the state is still wrong, so retrying is safe.
                if "did not change its state" not in str(e) or attempt == retries - 1:
                    raise
                print(f"Checkbox click did not take. Retrying... {e}")
                self.page.wait_for_timeout(delay)

    def _is_element_disabled(self, locator: Locator) -> bool:
        """Returns whether the locator is disabled."""
        return locator.is_disabled()

    def _click(self, element: str | Locator | ElementHandle, expected_locator=None,
               expected_locator_to_be_hidden=None, expected_url=None, with_force=False, retries=3,
               delay=500, wait_for_navigation: bool | None = None):
        """Clicks on a given element locator with retry logic.

        Args:
            element: The element locator, selector string, or element handle to click.
            expected_locator: Locator expected to be visible after the click.
            expected_locator_to_be_hidden: Locator expected to be hidden after the click.
            expected_url: URL expected after the click.
            with_force: Whether to force the click.
            wait_for_navigation: True for clicks that must navigate - fails if they don't.
            False skips navigation handling. Left unset, a navigation the click starts is
            detected and waited for. In both the True and the detected case, links and form
            submits wait for the current page to settle before clicking, since scripts still
            running after DOMContentLoaded can shift the layout (e.g. revealing the scam alert
            banner) and make the click miss; then the new page is awaited, so the next action
            or an expected_locator check does not run against the old one.
        """
        navigated = False
        for attempt in range(retries):
            try:
                element_locator = (
                    self._get_element_locator(element) if isinstance(element, str) else element
                )
                if wait_for_navigation:
                    self.page.wait_for_load_state("load")
                    with self.page.expect_navigation(wait_until="domcontentloaded"):
                        element_locator.click(force=with_force)
                    navigated = True
                elif wait_for_navigation is False:
                    element_locator.click(force=with_force)
                    self.wait_for_dom_to_load()
                else:
                    navigated = self._click_detecting_navigation(element_locator, with_force)
                self._recover_if_on_error_page()
                if expected_locator:
                    self._wait_for_locator(expected_locator, timeout=3000, raise_exception=True)
                if expected_locator_to_be_hidden:
                    self._wait_for_locator_to_be_hidden(
                        expected_locator_to_be_hidden, raise_exception=True)
                if expected_url:
                    self.page.wait_for_url(expected_url, timeout=10000)
                break
            except PlaywrightTimeoutError:
                # Once the click has navigated, clicking again would act on the new page (or
                # resubmit a form), so a failing check afterwards is final.
                if navigated:
                    raise
                if expected_locator:
                    print(f"Expected locator {expected_locator} not found. Retrying...")
                if expected_locator_to_be_hidden:
                    print(f"Locator {expected_locator_to_be_hidden} is not hidden yet")
                if expected_url:
                    print(f"Expected URL {expected_url} not found. Retrying...")
                if attempt < retries - 1:
                    self.page.wait_for_timeout(delay)
                else:
                    raise

    def _click_detecting_navigation(self, element_locator: Locator | ElementHandle,
                                    with_force: bool) -> bool:
        """Clicks the element and, if the click starts a page load, waits for the new page.

        Returns:
            bool: Whether the click navigated.
        """
        target = element_locator.evaluate(PREPARE_CLICK_JS)
        likely_navigates = target["navigates"]
        if likely_navigates:
            self.page.wait_for_load_state("load")
        main_frame = self.page.main_frame
        started, committed, downloads = [], [], []

        def on_request(request):
            if request.is_navigation_request() and request.frame == main_frame:
                started.append(request)

        def on_frame_navigated(frame):
            if frame == main_frame:
                committed.append(frame)

        def on_download(download):
            downloads.append(download)

        self.page.on("request", on_request)
        self.page.on("framenavigated", on_frame_navigated)
        self.page.on("download", on_download)
        try:
            element_locator.click(force=with_force)
            if likely_navigates:
                deadline = time.monotonic() + NAVIGATION_START_WINDOW
                while not started and time.monotonic() < deadline:
                    self.page.wait_for_timeout(50)
            if likely_navigates and not started and self._click_owes_navigation(target):
                deadline = time.monotonic() + NAVIGATION_EXPECTED_WINDOW
                while not started and time.monotonic() < deadline:
                    self.page.wait_for_timeout(100)
                if not started:
                    # _click retries a click that has not navigated.
                    raise PlaywrightTimeoutError(
                        "The click was not handled by the page but did not navigate")
            if not started:
                self.wait_for_dom_to_load()
                return False
            response = started[-1].response()
            # A failed request, a 204 or a download leaves the current page in place.
            if (response is None or response.status == 204
                    or "attachment" in (response.headers.get("content-disposition") or "")):
                return False
            if not committed:
                # A response the browser saves rather than displays (e.g. a feed Firefox does
                # not render) starts a download instead of committing a new page.
                deadline = time.monotonic() + NAVIGATION_COMMIT_TIMEOUT
                while not committed and not downloads and time.monotonic() < deadline:
                    self.page.wait_for_timeout(100)
                if downloads:
                    return False
                if not committed:
                    raise PlaywrightTimeoutError("The click's navigation never committed")
        finally:
            self.page.remove_listener("request", on_request)
            self.page.remove_listener("framenavigated", on_frame_navigated)
            self.page.remove_listener("download", on_download)
        self.wait_for_dom_to_load()
        return True

    def _click_owes_navigation(self, target: dict) -> bool:
        """Whether a link or submit click that started no page load should have: the page did
        not handle it with a script, and (for a submit) the form passed browser validation. A
        click that never reached the page at all also counts, since it did not take.

        Args:
            target (dict): The click target as described by PREPARE_CLICK_JS.
        """
        outcome = self.page.evaluate("() => window.__sumoClick")
        if outcome is None or outcome["clickPrevented"]:
            return False
        if not target["submit"]:
            return True
        if not target["formValid"]:
            return False
        return not (outcome["submitted"] and outcome["submitPrevented"])

    def _recover_if_on_error_page(self, retries: int = 3) -> None:
        """If the last main-frame navigation response was a 502, reload the page until it
        isn't. The `_last_main_nav_status` attribute is maintained by the response listener
        registered in `tests/conftest.py::navigate_to_homepage`.
        """
        for attempt in range(retries):
            status = getattr(self.page, "_last_main_nav_status", None)
            if status is None or status != 502:
                return
            print(f"On 502 page, reload attempt "
                  f"{attempt + 1}/{retries} in 5s...")
            self.page.wait_for_timeout(5000)
            try:
                self.page.reload(wait_until="domcontentloaded")
            except PlaywrightError as e:
                print(f"Reload during 502 recovery failed: {e}")

    def _click_on_an_element_by_index(self, locator: Locator, index: int):
        """Clicks on an element at a given index within a locator."""
        self._click(locator.nth(index))

    def _click_on_first_item(self, locator: Locator):
        """Clicks the first element matched by a locator."""
        self._click(locator.first)

    def _fill(self, locator: Locator, text: str, with_force=False):
        """Fills a text input with the given text."""
        locator.fill(text, force=with_force)

    def _type(self, locator: Locator, text: str, delay: int):
        """Types text into a locator with a per-keystroke delay."""
        locator.type(text=text, delay=delay)

    def _press_a_key(self, locator: Locator, key: str):
        """Presses a key on a given locator."""
        locator.press(key)

    def _clear_field(self, locator: Locator):
        """Clears the input field of a given locator."""
        locator.clear()

    def _select_option_by_label(self, locator: Locator, label_name: str, expected_locator=None):
        """Selects a select-box option by its visible label."""
        self.wait_for_dom_to_load()
        locator.select_option(label=label_name)
        if expected_locator:
            self._wait_for_locator(expected_locator)

    def _select_option_by_value(self, locator: Locator, value: str):
        """Selects a select-box option by its value attribute."""
        locator.select_option(value=value)

    def _select_random_option_by_value(self, dropdown_locator: Locator, locator_options: Locator):
        """Selects a random non-empty option from a select box."""
        elements = []
        for option in locator_options.all():
            value = option.get_attribute('value')
            if value:
                elements.append(value)
        self._select_option_by_value(dropdown_locator, random.choice(elements))

    def _accept_dialog(self):
        """Registers a handler to automatically accept the next dialog."""
        self.page.on("dialog", lambda dialog: dialog.accept())

    def _hover_over_element(self, locator: Locator):
        """Hovers the mouse over a given locator."""
        locator.hover()

    def _is_element_visible(self, locator: Locator) -> bool:
        """Returns whether the element matched by the locator is visible."""
        return locator.is_visible()

    def _is_checkbox_checked(self, locator: Locator) -> bool:
        """Returns whether the checkbox matched by the locator is checked."""
        return locator.is_checked()

    def _wait_for_locator(self, locator: Locator, timeout=3500, raise_exception=False):
        """Waits for a locator to become visible.

        Args:
            locator: The locator to wait for.
            timeout: Timeout in milliseconds.
            raise_exception: Re-raise the timeout error if True.
        """
        try:
            locator.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            print(f"{locator} is not displayed")
            if raise_exception:
                raise

    def _wait_for_locator_to_be_hidden(self, locator: Locator, timeout=3500,
                                       raise_exception=False):
        """Waits for a locator to become hidden.

        Args:
            locator: The locator to wait for.
            timeout: Timeout in milliseconds.
            raise_exception: Re-raise the timeout error if True.
        """
        try:
            locator.wait_for(state="hidden", timeout=timeout)
        except PlaywrightTimeoutError:
            print(f"{locator} is not displayed")
            if raise_exception:
                raise

    def _move_mouse_to_location(self, x: int, y: int):
        """Moves the mouse to absolute page coordinates."""
        self.page.mouse.move(x, y)

    def eval_on_selector_for_last_child_text(self, element: str) -> str:
        """Returns the text content of the last child of a matched element."""
        return self.page.eval_on_selector(
            element,
            "el => el.lastChild?.textContent?.trim()"
        )

    def wait_for_dom_to_load(self):
        """Waits for the DOMContentLoaded event. Use after full-page navigations."""
        try:
            self.page.wait_for_load_state("domcontentloaded")
        except PlaywrightTimeoutError:
            print("DOMContentLoaded event was not fired. Continuing...")

    def wait_for_networkidle(self):
        """Waits for network idle. Use explicitly after full-page navigations only."""
        try:
            self.page.wait_for_load_state("networkidle")
        except PlaywrightTimeoutError:
            print("Network idle state was not reached. Continuing...")