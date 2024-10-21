from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileMyQuestionsPage(BasePage):
    # My profile my questions page locators.
    MY_PROFILE_QUESTIONS_LOCATORS = {
        "my_profile_my_questions_page_heading": "//h2[@class='sumo-page-subheading']",
        "my_profile_my_questions_no_question_message": "//article[@id='profile']/p",
        "my_profile_my_questions_list": "//article[@id='profile']/ul/a",
        "my_profile_my_questions_titles": "//article[@id='profile']/ul/a/li"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # My profile my questions page actions.
    def get_list_of_profile_questions_locators(self) -> Locator:
        """Returns the locator of the question list."""
        return self._get_element_locator(
            self.MY_PROFILE_QUESTIONS_LOCATORS["my_profile_my_questions_list"])

    def get_list_of_profile_no_question_message_locator(self) -> Locator:
        """Returns the locator of the no question message."""
        return self._get_element_locator(
            self.MY_PROFILE_QUESTIONS_LOCATORS["my_profile_my_questions_no_question_message"])

    def get_text_of_no_question_message(self) -> str:
        """Returns the text of the no question message."""
        return self._get_text_of_element(
            self.MY_PROFILE_QUESTIONS_LOCATORS["my_profile_my_questions_no_question_message"])

    def get_number_of_questions(self) -> int:
        """Returns the number of questions listed on the page."""
        return len(self._get_element_handles(
            self.MY_PROFILE_QUESTIONS_LOCATORS["my_profile_my_questions_list"]))

    def click_on_a_question_by_index(self, index_of_question: int):
        """Clicks on a question by its index."""
        self._click(f"//article[@id='profile']/ul/a[{index_of_question}]/li")

    def click_on_a_question_by_name(self, question_title: str):
        """Clicks on a question by its title."""
        self._click(f"//article[@id='profile']/ul/a/li[text()='{question_title}']")

    def get_text_of_first_listed_question(self) -> str:
        """Returns the text of the first listed question."""
        return self._get_element_inner_text_from_page("//article[@id='profile']/ul/a[1]")

    def get_listed_question(self, question_name: str) -> Locator:
        """Returns the locator of a question by its name."""
        return self._get_element_locator(f"//article[@id='profile']/ul/a/"
                                         f"li[text()='{question_name}']")

    def get_all_my_posted_questions(self) -> list[str]:
        """Returns a list of all the posted questions."""
        return self._get_text_of_elements(self.MY_PROFILE_QUESTIONS_LOCATORS["my_profile_my_"
                                                                             "questions_titles"])
