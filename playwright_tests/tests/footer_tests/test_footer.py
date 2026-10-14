import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urldefrag

import allure
import pytest
import requests
from playwright.sync_api import Page, expect

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages

# Splits the locale walk across xdist workers; matches CI's --numprocesses 6.
LOCALE_SHARDS = 6
# Footer links are checked concurrently; each one is a plain GET to mostly external sites.
LINK_CHECK_WORKERS = 10


def _fetch_status(url: str) -> int | str:
    """Returns the status of a GET to the url, or the error when the request itself fails."""
    headers = {
        "User-Agent": Utilities.user_agent,
        Utilities.fxa_browser_challenge_header: Utilities.fxa_browser_challenge_value,
    }
    try:
        return requests.get(url, headers=headers, timeout=30).status_code
    except requests.RequestException as error:
        return str(error)


# C945147
@pytest.mark.footerSectionTests
def test_all_footer_links_are_working(page: Page):
    sumo_pages = SumoPages(page)
    # A fragment only points within a page, so each page is requested once.
    urls = [url for url in dict.fromkeys(
        urldefrag(link).url for link in sumo_pages.footer_section.get_all_footer_links())
        if url != "https://twitter.com/firefox"]

    with ThreadPoolExecutor(max_workers=LINK_CHECK_WORKERS) as executor:
        statuses = dict(zip(urls, executor.map(_fetch_status, urls), strict=True))

    broken_links = []
    for url, status in statuses.items():
        with allure.step(f"Verifying that {url} is not broken ({status})"):
            # Some links return 403/429 to automated requests; those count as working.
            if not isinstance(status, int) or (status >= 400 and status not in (403, 429)):
                broken_links.append(f"{url} -> {status}")

    assert not broken_links, f"Broken footer links: {broken_links}"


# C2316348
@pytest.mark.footerSectionTests
@pytest.mark.parametrize("shard", range(LOCALE_SHARDS))
def test_locale_selector(page: Page, shard: int):
    sumo_pages = SumoPages(page)
    with allure.step("Verifying that all footer select options are redirecting the user to the "
                     "correct page locale"):
        for locale in sumo_pages.footer_section.get_all_footer_locales()[shard::LOCALE_SHARDS]:
            sumo_pages.footer_section.switch_to_a_locale(locale)
            expect(page).to_have_url(re.compile(f".*/{re.escape(locale)}(/|$)"))
