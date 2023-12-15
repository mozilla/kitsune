from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileMyQuestionsPage(BasePage):
    __my_profile_my_questions_page_heading = "//h2[@class='sumo-page-subheading']"
    __my_profile_my_questions_no_question_message = "//article[@id='profile']/p"
    __my_profile_my_questions_list = "//article[@id='profile']/ul/a"
    __my_profile_my_questions_titles = "//article[@id='profile']/ul/a/li"

    def __init__(self, page: Page):
        super().__init__(page)

    def is_question_list_displayed(self) -> Locator:
        return super()._get_element_locator(self.__my_profile_my_questions_list)

    def is_no_question_message_displayed(self) -> Locator:
        return super()._get_element_locator(self.__my_profile_my_questions_no_question_message)

    def get_text_of_no_question_message(self) -> str:
        return super()._get_text_of_element(self.__my_profile_my_questions_no_question_message)

    def get_number_of_questions(self) -> int:
        return len(super()._get_element_handles(self.__my_profile_my_questions_list))

    def click_on_a_question_by_index(self, index_of_question: int):
        xpath = f"//article[@id='profile']/ul/a[{index_of_question}]/li"
        super()._click(xpath)

    def click_on_a_question_by_name(self, question_title: str):
        xpath = f"//article[@id='profile']/ul/a/li[text()='{question_title}']"
        super()._click(xpath)

    def get_text_of_first_listed_question(self) -> str:
        xpath = "//article[@id='profile']/ul/a[1]"
        return super()._get_element_inner_text_from_page(xpath)

    def get_listed_question(self, question_name: str) -> Locator:
        xpath = f"//article[@id='profile']/ul/a/li[text()='{question_name}']"
        return super()._get_element_locator(xpath)

    def get_all_my_posted_questions(self) -> list[str]:
        return super()._get_text_of_elements(self.__my_profile_my_questions_titles)
