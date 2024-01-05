from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MyProfileAnswersPage(BasePage):
    # My Profile Answers.
    __my_answers_page_header = "//h2[@class='sumo-page-subheading']"
    __my_answers_question_subject_links = "//article[@id='profile']//li/a"

    def __init__(self, page: Page):
        super().__init__(page)

    # My Profile Answers actions.
    def _get_page_header(self) -> str:
        return super()._get_text_of_element(self.__my_answers_page_header)

    def _get_text_of_question_subjects(self) -> list[str]:
        return super()._get_text_of_elements(self.__my_answers_question_subject_links)

    def _click_on_specific_answer(self, answer_id: str):
        xpath = f"//article[@id='profile']//a[contains(@href, '{answer_id}')]"
        super()._click(xpath)

    def _get_my_answer_text(self, answer_id: str) -> str:
        xpath = (f"//article[@id='profile']//a[contains(@href, '{answer_id}')]/following-sibling"
                 f"::blockquote")
        return super()._get_text_of_element(xpath)
