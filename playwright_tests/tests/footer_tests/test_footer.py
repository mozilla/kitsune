import re
import allure
import pytest
from playwright.sync_api import expect, Page
from urllib.parse import urljoin
from playwright_tests.pages.sumo_pages import SumoPages


# C945147
@pytest.mark.footerSectionTests
def test_all_footer_links_are_working(page: Page):
    sumo_pages = SumoPages(page)
    for link in sumo_pages.footer_section.get_all_footer_links():
        relative_url = link.get_attribute("href")

        if relative_url == "https://twitter.com/firefox":
            print("Skipping Twitter link because it returned 400 due to custom user agent being"
                  "used by playwright")
            continue

        # Verify if URL is absolute, and construct the full URL if it's not
        if not relative_url.startswith(('http://', 'https://')):
            base_url = page.url
            url = urljoin(base_url, relative_url)
        else:
            url = relative_url

        # Use Playwright's API to make the request within the browser context
        response = page.request.get(url)

        # Some links are returning status code 429.
        # We are currently treating them as pass cases.
        with allure.step(f"Verifying that {url} is not broken"):
            assert response.status in set(range(400)) | {403, 429}


# C2316348
@pytest.mark.footerSectionTests
def test_locale_selector(page: Page):
    sumo_pages = SumoPages(page)
    with allure.step("Verifying that all footer select options are redirecting the user to the "
                     "correct page locale"):
        for locale in sumo_pages.footer_section.get_all_footer_locales():
            sumo_pages.footer_section.switch_to_a_locale(locale)
            expect(
                page
            ).to_have_url(re.compile(f".*{locale}"))
