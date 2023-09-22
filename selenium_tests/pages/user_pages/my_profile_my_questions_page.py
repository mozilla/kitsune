from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class MyProfileMyQuestionsPage(BasePage):
    __my_profile_my_questions_page_heading = (By.XPATH, "//h2[@class='sumo-page-subheading']")
    __my_profile_my_questions_no_question_message = (By.XPATH, "//article[@id='profile']/p")
    __my_profile_my_questions_list = (By.XPATH, "//article[@id='profile']/ul/a")
    __my_profile_my_questions_titles = (By.XPATH, "//article[@id='profile']/ul/a/li")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def is_question_list_displayed(self) -> bool:
        return super()._is_element_displayed(self.__my_profile_my_questions_list)

    def is_no_question_message_displayed(self) -> bool:
        return super()._is_element_displayed(self.__my_profile_my_questions_no_question_message)

    def get_text_of_no_question_message(self) -> str:
        return super()._get_text_of_element(self.__my_profile_my_questions_no_question_message)

    def get_number_of_questions(self) -> int:
        return super()._get_number_of_elements(self.__my_profile_my_questions_list)

    def click_on_a_question_by_index(self, index_of_question: int):
        xpath = (By.XPATH, f"//article[@id='profile']/ul/a[{index_of_question}]/li")
        super()._click(xpath)

    def get_text_of_first_listed_question(self) -> str:
        xpath = (By.XPATH, "//article[@id='profile']/ul/a[1]")
        return super()._get_text_of_element(xpath)
