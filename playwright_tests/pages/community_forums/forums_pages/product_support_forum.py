import re
from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class ProductSupportForum(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """General page locators."""
        self.ask_the_community_button = page.get_by_role("link").filter(
            has_text="Ask the Community")
        self.community_forum_header = page.locator("//span[@class='product-title-text']")

        """Locators belonging to the displayed questions."""
        self.showing_questions_tagged_tag = page.locator("div#tagged a[class='tag']")
        self.all_question_list_tags = page.locator("li[class='tag']")
        self.show_all_questions_option = page.locator("a[class='show-all']")
        self.question_in_forum = lambda question_id: page.locator(
            f"//article[@id='{question_id}']")
        self.all_listed_questions = page.locator("//div[@id='questions-list']//article")
        self.questions_section = page.locator("//section[@class='forum--question-list questions']")
        self.all_listed_question_names = page.locator(
            "//div[@id='questions-list']//h2[@class='forum--question-item-heading']/a")
        self.question_tag_list = lambda question_id: page.locator(
            f"article#{question_id} li.tag")
        self.is_spam_locator = page.locator("//div[@id='questions-list']//span[text()='Spam']")
        self.is_spam_locator_for_question = lambda question_id: page.locator(
            f"//div[@id='questions-list']//article[@id='{question_id}']//span[text()='Spam']")
        self.question_solved_indicator = lambda question_id: page.locator(
            f"//article[@id='{question_id}']//span[text()='Solved']")
        self.question_archived_indicator = lambda question_id: page.locator(
            f"//article[@id='{question_id}']//span[text()='Archived']")
        self.question_locked_indicator = lambda question_id: page.locator(
            f"//article[@id='{question_id}']//span[text()='Locked']")

        """Locators belonging to the filter options sections."""
        self.selected_tab_filter = page.locator(
            "//ul[@class='tabs--list subtopics']/li[@class='tabs--item']/a[@class='selected']")
        self.tab_filter_by_name = lambda filter_name: page.locator(
            f"//ul[@class='tabs--list subtopics']/li[@class='tabs--item']/a[normalize-space(."
            f")='{filter_name}']")
        self.side_navbar_filter_options = page.locator("ul[class='sidebar-nav--list'] a")
        self.topic_dropdown_selected_option = page.locator(
            "select#products-topics-dropdown").get_by_role("option", selected=True)


    """Actions against the general product community forum page locators."""
    def click_on_the_ask_the_community_button(self):
        """Click on the 'Ask the Community' button."""
        self._click(self.ask_the_community_button)

    """Actions against the filter tab section locators."""
    def click_on_a_certain_tab_filter(self, filter_name: str):
        """
        Click on a certain tab filter.
        Args:
            filter_name (str): The name of the tab filter.
        """
        self._click(self.tab_filter_by_name(filter_name))

    """Actions against the filter by tag section locators."""
    def click_on_the_show_all_questions_option(self):
        """Click on the 'Show all questions' option displayed when filtering by tags."""
        super()._click(self.show_all_questions_option)

