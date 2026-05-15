from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class MyProfileAnswersPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the Answers page."""
        self.my_answers_page_header = page.locator("h2[class='sumo-page-subheading']")
        self.my_answers_question_subject_links = page.locator("article#profile li a")
        self.answer_by_id = lambda id: page.locator(f"article#profile a[href*='{id}']")
        self.answer_text = lambda id: page.locator(
            f"//article[@id='profile']//a[contains(@href, '{id}')]/following-sibling::blockquote")

    """Actions against the profile answers page locators."""
    def click_on_specific_answer(self, answer_id: str):
        """Click on a specific answer"""
        self._click(self.answer_by_id(answer_id))

