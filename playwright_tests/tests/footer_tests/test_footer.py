import re
import allure
import pytest
import requests
from pytest_check import check
from playwright.sync_api import expect, Page
from urllib.parse import urljoin
from playwright_tests.pages.sumo_pages import SumoPages


# C945147
@pytest.mark.footerSectionTests
def test_all_footer_links_are_working(page: Page):
    sumo_pages = SumoPages(page)
    for link in sumo_pages.footer_section._get_all_footer_links():
        relative_url = link.get_attribute("href")

        # Verify if URL is absolute, and construct the full URL if it's not
        if not relative_url.startswith(('http://', 'https://')):
            base_url = page.url
            url = urljoin(base_url, relative_url)
        else:
            url = relative_url

        # I have noticed that one of our footer link: https://foundation.mozilla.org/
        # seems to reject requests coming from Headless Chrome user-agent.
        # We are fetching the User-Agent via the JS executor,
        # constructing and passing the header to our request.

        user_agent = page.evaluate("navigator.userAgent")

        if "HeadlessChrome" in user_agent:
            user_agent = user_agent.replace("HeadlessChrome", "Chrome")

        header = {"User-Agent": f"{user_agent}"}
        # Remove this
        response = requests.get(url, headers=header)

        # Some links are returning status code 429.
        # We are currently treating them as pass cases.
        with check, allure.step(f"Verifying that {url} is not broken are not broken"):
            assert response.status_code in set(range(400)) | {403, 429}


# C2316348
@pytest.mark.footerSectionTests
def test_locale_selector(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Verifying that all footer select options are redirecting the user to the "
                     "correct page locale"):
        for locale in sumo_pages.footer_section._get_all_footer_locales():
            sumo_pages.footer_section._switch_to_a_locale(locale)
            expect(
                page
            ).to_have_url(re.compile(f".*{locale}"))
