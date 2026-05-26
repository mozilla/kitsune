from typing import Literal

from playwright.sync_api import Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.user_pages.my_profile_page import MyProfilePage


class UserProfileFlow:
    def __init__(self, page: Page):
        self.page = page
        self.utilities = Utilities(page)
        self.my_profile_page = MyProfilePage(page)

    REPORT_REASON = Literal[
        "Spam or other unrelated content",
        "Inappropriate language/dialog",
        "Abusive content",
        "Other (please specify)",
    ]

    _REPORT_REASON_ACTIONS = {
        "Spam or other unrelated content": "click_on_spam_content_option",
        "Inappropriate language/dialog": "click_on_inappropriate_language_option",
        "Abusive content": "click_on_abusive_content_option",
        "Other (please specify)": "click_on_other_content_option",
    }

    def report_user_profile(self, report_reason: REPORT_REASON, report_details: str = ""):
        self.my_profile_page.click_on_report_abuse_option()
        getattr(self.my_profile_page, self._REPORT_REASON_ACTIONS[report_reason])()
        if report_details:
            self.my_profile_page.fill_have_more_to_say_textarea(report_details)
        self.my_profile_page.click_on_report_submit_button()
