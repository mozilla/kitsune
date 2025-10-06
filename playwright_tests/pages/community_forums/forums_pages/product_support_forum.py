import re

from playwright.sync_api import Page, Locator

from playwright_tests.core.basepage import BasePage


class ProductSupportForum(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # General page locators.
        self.ask_the_community_button = page.get_by_role("link").filter(
            has_text="Ask the Community")
        self.community_forum_header = page.locator("//span[@class='product-title-text']")

        # Locators related to the displayed questions.
        self.showing_questions_tagged_tag = page.locator("div#tagged a[class='tag']")
        self.all_question_list_tags = page.locator("li[class='tag']")
        self.show_all_questions_option = page.locator("a[class='show-all']")
        self.all_listed_questions = page.locator("//div[@id='questions-list']//article")
        self.questions_section = page.locator("//section[@class='forum--question-list questions']")
        self.all_listed_question_names = page.locator(
            "//div[@id='questions-list']//h2[@class='forum--question-item-heading']/a")
        self.question_tag_list = lambda question_id: page.locator(
            f"article#{question_id} li.tag")
        self.is_spam_locator = page.locator("//div[@id='questions-list']//li[@class='is-spam']")
        self.is_spam_locator_for_question = lambda question_id: page.locator(
            f"//div[@id='questions-list']//article[@id='{question_id}']//li[@class='is-spam']")
        self.question_solved_indicator = lambda question_id: page.locator(
            f"//article[@id='{question_id}']//li[@class='thread-solved']")
        self.question_contributed_indicator = lambda question_id: page.locator(
            f"//article[@id='{question_id}']//li[@class='thread-contributed']")
        self.question_archived_indicator = lambda question_id: page.locator(
            f"//article[@id='{question_id}']//li[@class='thread-archived']")
        self.question_locked_indicator = lambda question_id: page.locator(
            f"//article[@id='{question_id}']//li[@class='thread-locked']")


        # Locators belonging to the filter options.
        self.selected_tab_filter = page.locator(
            "//ul[@class='tabs--list subtopics']/li[@class='tabs--item']/a[@class='selected']")
        self.tab_filter_by_name = lambda filter_name: page.locator(
            f"//ul[@class='tabs--list subtopics']/li[@class='tabs--item']/a[normalize-space(."
            f")='{filter_name}']")
        self.side_navbar_filter_options = page.locator("ul[class='sidebar-nav--list'] a")
        self.topic_dropdown_selected_option = page.locator(
            "select#products-topics-dropdown").get_by_role("option", selected=True)


    # General product community forum actions.
    def get_text_of_product_community_forum_header(self) -> str:
        """Get the text of the product community forum header."""
        return self._get_text_of_element(self.community_forum_header)

    def click_on_the_ask_the_community_button(self):
        """Click on the 'Ask the Community' button."""
        self._click(self.ask_the_community_button)

    # Actions against the filter tab section.
    def get_text_of_selected_tab_filter(self) -> str:
        """Get the text of the currently selected tab filter."""
        return self._get_text_of_element(self.selected_tab_filter)

    def click_on_a_certain_tab_filter(self, filter_name: str):
        """
        Click on a certain tab filter.
        Args:
            filter_name (str): The name of the tab filter.
        """
        self._click(self.tab_filter_by_name(filter_name))

    def is_tab_filter_displayed(self, filter_name: str) -> bool:
        """
        Returning whether the tab filter option is displayed or not.
        Args:
            filter_name (str): Tab filter name.
        """
        return self._is_element_visible(self.tab_filter_by_name(filter_name))

    # Actions against the filter section.
    def get_selected_topic_option(self) -> str:
        """Get the selected topic filter option."""
        option = super()._get_text_of_element(self.topic_dropdown_selected_option)
        return re.sub(r'\s+', ' ', option).strip()

    # Actions against the filter by tag section.
    def get_text_of_selected_tag_filter_option(self) -> str:
        """Get the text of the applied tag filter option."""
        return super()._get_text_of_element(self.showing_questions_tagged_tag)

    def click_on_the_show_all_questions_option(self):
        """Click on the 'Show all questions' option displayed when filtering by tags."""
        super()._click(self.show_all_questions_option)

    # Actions against the displayed questions.
    def get_all_question_list_tags(self, question_id: str) -> list[str]:
        """
        Get the tags associated with a particular question.
        Args:
            question_id (str): The Question ID of the targeted question.
        """
        question_tags = self._get_text_of_elements(self.question_tag_list(question_id))
        return question_tags

    def extract_question_ids(self) -> list[str]:
        """Extract the ID's of the listed questions."""
        elements = self.all_listed_questions.all()
        id_values = []
        for element in elements:
            id_values.append(
                super()._get_element_attribute_value(
                    element, attribute="id"
                )
            )
        return id_values

    def get_text_of_all_listed_questions(self) -> list[str]:
        """Get the titles of all listed questions."""
        if self._is_element_visible(self.questions_section):
            return self._get_text_of_elements(self.all_listed_question_names)
        else:
            """
            If the questions locator is not visible we are returning an empty list because it means
             that there are no questions available inside the current tab filter.
            """
            return []


    def get_ids_of_all_listed_questions(self) -> list[str]:
        """Get the question ID's for all listed questions."""
        if self._is_element_visible(self.questions_section):
            return self._get_element_attribute_value(self.all_listed_questions.all(), "id")
        else:
            """
            If the questions locator is not visible we are returning an empty list because it means
            that there are no questions available inside the current tab filter.
            """
            return []

    def get_list_of_is_spam_locators(self) -> list[Locator]:
        """Get the list of spam locators"""
        return self.is_spam_locator.all()

    def is_spam_flag_for_question(self, question_id: str) -> bool:
        """
        Return if the is-spam flag is set for a certain question or not.
        Args:
            question_id (str): The question ID.
        """
        return self._is_element_visible(self.is_spam_locator_for_question(question_id))

    def is_question_solved_indicator_displayed(self, question_id: str) -> bool:
        """
        Return if the solved indicator is displayed for a certain question or not.
        Args:
            question_id (str): The question ID.
        """
        return self._is_element_visible(self.question_solved_indicator(question_id))

    def is_question_contributed_indicator_displayed(self, question_id: str) -> bool:
        """
        Return if the contributed indicator is displayed for a certain question or not.
        Args:
            question_id (str): The question ID.
        """
        return self._is_element_visible(self.question_contributed_indicator(question_id))

    def is_question_archived_indicator_displayed(self, question_id: str) -> bool:
        """
        Return if the archived indicator is displayed for a certain question or not.
        Args:
            question_id (str): The question ID.
        """
        return self._is_element_visible(self.question_archived_indicator(question_id))

    def is_question_locked_indicator_displayed(self, question_id: str) -> bool:
        """
        Return if the locked indicator is displayed for a certain question or not.
        Args:
            question_id (str): The question ID.
        """
        return self._is_element_visible(self.question_locked_indicator(question_id))

