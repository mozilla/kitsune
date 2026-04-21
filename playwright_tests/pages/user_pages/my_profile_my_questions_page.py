from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MyProfileMyQuestionsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the My Questions profile page."""
        self.questions_page_heading = page.locator("h2[class='sumo-page-subheading']")
        self.questions_no_question_message = page.locator("//p[@class='my-questions--empty']")
        self.questions_list = page.locator("//a[@class='question-entry--title-link']")
        self.questions_titles = page.locator("//h3[@class='question-entry--title']")
        self.question_by_name = lambda name: page.locator(
            f"//a[@class='question-entry--title-link' and text()='{name}']")

    """Actions against the My Questions profile page locators."""
    def click_on_a_question_by_index(self, index_of_question: int):
        """Clicks on a question by its index."""
        self._click(self.questions_titles.nth(index_of_question))

    def click_on_a_question_by_name(self, question_title: str):
        """Clicks on a question by its title."""
        self._click(self.question_by_name(question_title))
