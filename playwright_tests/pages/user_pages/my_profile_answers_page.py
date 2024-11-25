from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MyProfileAnswersPage(BasePage):
    # My Profile Answers.
    MY_PROFILE_ANSWERS_LOCATORS = {
        "my_answers_page_header": "//h2[@class='sumo-page-subheading']",
        "my_answers_question_subject_links": "//article[@id='profile']//li/a"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # My Profile Answers actions.
    def get_page_header(self) -> str:
        """Get the header of the My Profile Answers page."""
        return self._get_text_of_element(self.MY_PROFILE_ANSWERS_LOCATORS["my_answers_page_"
                                                                          "header"])

    def get_text_of_question_subjects(self) -> list[str]:
        """Get the text of the question subjects."""
        return self._get_text_of_elements(self.MY_PROFILE_ANSWERS_LOCATORS["my_answers_question_"
                                                                           "subject_links"])

    def click_on_specific_answer(self, answer_id: str):
        """Click on a specific answer"""
        self._click(f"//article[@id='profile']//a[contains(@href, '{answer_id}')]")

    def get_my_answer_text(self, answer_id: str) -> str:
        """Get the text of a specific answer."""
        return self._get_text_of_element(f"//article[@id='profile']//"
                                         f"a[contains(@href, '{answer_id}')]/"
                                         f"following-sibling::blockquote")

    def get_my_answer_question_title(self, answer_id: str) -> str:
        """Get the title of the question that the answer belongs to.

        Args:
        answer_id: str: The id of the answer.
        """
        return self._get_text_of_element(f"//article[@id='profile']//a[contains(@href,"
                                         f" '{answer_id}')]")
