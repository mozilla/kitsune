from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MyProfileAnswersPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # My Profile Answers locators.
        self.my_answers_page_header = page.locator("h2[class='sumo-page-subheading']")
        self.my_answers_question_subject_links = page.locator("article#profile li a")
        self.answer_by_id = lambda id: page.locator(f"article#profile a[href*='{id}']")
        self.answer_text = lambda id: page.locator(
            f"//article[@id='profile']//a[contains(@href, '{id}')]/following-sibling::blockquote")

    # My Profile Answers actions.
    def get_page_header(self) -> str:
        """Get the header of the My Profile Answers page."""
        return self._get_text_of_element(self.my_answers_page_header)

    def get_text_of_question_subjects(self) -> list[str]:
        """Get the text of the question subjects."""
        return self._get_text_of_elements(self.my_answers_question_subject_links)

    def click_on_specific_answer(self, answer_id: str):
        """Click on a specific answer"""
        self._click(self.answer_by_id(answer_id))

    def get_my_answer_text(self, answer_id: str) -> str:
        """Get the text of a specific answer."""
        return self._get_text_of_element(self.answer_text(answer_id))

    def get_my_answer_question_title(self, answer_id: str) -> str:
        """Get the title of the question that the answer belongs to.

        Args:
        answer_id: str: The id of the answer.
        """
        return self._get_text_of_element(self.answer_by_id(answer_id))
