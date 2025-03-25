from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class MyProfileMyQuestionsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # My profile my questions page locators.
        self.questions_page_heading = page.locator("h2[class='sumo-page-subheading']")
        self.questions_no_question_message = page.locator("article#profile p")
        self.questions_list = page.locator("article#profile ul a")
        self.questions_titles = page.locator("article#profile ul a li")
        self.questions_by_index = lambda index: page.locator(
            f"//article[@id='profile']/ul/a[{index}]/li")
        self.question_by_name = lambda name: page.locator("article#profile ul a li").get_by_text(
            name, exact=True)

    # My profile my questions page actions.
    def get_list_of_profile_questions_locators(self) -> Locator:
        """Returns the locator of the question list."""
        return self.questions_list

    def get_list_of_profile_no_question_message_locator(self) -> Locator:
        """Returns the locator of the no question message."""
        return self.questions_no_question_message

    def get_text_of_no_question_message(self) -> str:
        """Returns the text of the no question message."""
        return self._get_text_of_element(self.questions_no_question_message)

    def get_number_of_questions(self) -> int:
        """Returns the number of questions listed on the page."""
        return len(self._get_element_handles(self.questions_list))

    def click_on_a_question_by_index(self, index_of_question: int):
        """Clicks on a question by its index."""
        self._click(self.questions_by_index(index_of_question))

    def click_on_a_question_by_name(self, question_title: str):
        """Clicks on a question by its title."""
        self._click(self.question_by_name(question_title))

    def get_text_of_first_listed_question(self) -> str:
        """Returns the text of the first listed question."""
        return self._get_element_inner_text_from_page(self.questions_by_index(1))

    def get_listed_question(self, question_name: str) -> Locator:
        """Returns the locator of a question by its name."""
        return self.question_by_name(question_name)

    def get_all_my_posted_questions(self) -> list[str]:
        """Returns a list of all the posted questions."""
        return self._get_text_of_elements(self.questions_titles)
