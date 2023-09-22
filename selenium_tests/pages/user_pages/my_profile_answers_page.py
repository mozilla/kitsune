from selenium.webdriver.common.by import By
from selenium_tests.core.base_page import BasePage
from selenium.webdriver.remote.webdriver import WebDriver


class MyProfileAnswersPage(BasePage):
    __my_answers_page_header = (By.XPATH, "//h2[@class='sumo-page-subheading']")
    __my_answers_question_subject_links = (By.XPATH, "//article[@id='profile']//li/a")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_page_header(self) -> str:
        return super()._get_text_of_element(self.__my_answers_page_header)

    def get_text_of_question_subjects(self) -> list[str]:
        return super()._get_text_of_elements(self.__my_answers_question_subject_links)

    def click_on_specific_answer(self, answer_id: str):
        xpath = (By.XPATH, f"//article[@id='profile']//a[contains(@href, '{answer_id}')]")
        super()._click(xpath)

    def get_my_answer_text(self, answer_id: str) -> str:
        xpath = (
            By.XPATH,
            f"//article[@id='profile']//a[contains(@href, '{answer_id}')]/following"
            f"-sibling::blockquote",
        )
        return super()._get_text_of_element(xpath)
