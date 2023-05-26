import pytest
import requests
import pytest_check as check

from selenium_tests.core.test_utilities import TestUtilities


class TestFooter(TestUtilities):
    # C945147
    @pytest.mark.smokeTest
    def test_all_footer_links_are_working(self):
        self.logger.info("Verifying that footer links are not broken")

        for link in self.pages.footer_section.get_all_footer_links():
            url = link.get_attribute("href")

            # I have noticed that one of our footer link:
            # https://foundation.mozilla.org/ seems to reject
            # requests that do not identify a User-Agent.
            # We are fetching the User-Agent via the JS executor,
            # constructing and passing the header to our request.

            user_agent = self.driver.execute_script("return navigator.userAgent")

            if "HeadlessChrome" in user_agent:
                user_agent = user_agent.replace("HeadlessChrome", "Chrome")

            header = {"User-Agent": f"{user_agent}"}
            print(header)
            response = requests.get(url, headers=header)

            check.is_true(
                response.status_code < 400,
                f"The following url if broken: {url}."
                f" Received status code: {response.status_code}",
            )
