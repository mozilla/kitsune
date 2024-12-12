from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class CommonWebElements(BasePage):
    AVOID_SPAM_BANNER = {
        "scam_banner": "//div[@id='id_scam_alert']",
        "scam_banner_text": "//div[@id='id_scam_alert']//p[@class='heading']",
        "learn_more_button": "//div[@id='id_scam_alert']//a"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Actions against the Avoid Spam Banner
    def get_scam_banner_text(self) -> str:
        """Returns the scam banner text."""
        return self._get_text_of_element(self.AVOID_SPAM_BANNER["scam_banner_text"])
