import re

from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class ProductSupportForum(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # General page locators.
        self.ask_the_community_button = page.get_by_role("link").filter(
            has_text="Ask the Community")
        self.showing_questions_tagged_tag = page.locator("div#tagged a[class='tag']")
        self.show_all_questions_option = page.locator("a[class='show-all']")
        self.all_question_status_filters = page.locator("ul[class='tabs--list subtopics'] "
                                                        "li[class='tabs--item']")
        self.side_navbar_filter_options = page.locator("ul[class='sidebar-nav--list'] a")
        self.topic_dropdown_selected_option = page.locator(
            "select#products-topics-dropdown").get_by_role("option", selected=True)
        self.all_question_list_tags = page.locator("li[class='tag']")
        self.all_listed_articles = page.locator("div#questions-list article")
        self.question_tag_list = lambda question_id: page.locator(
            f"article#{question_id} li.tag")

    # Ask the Community actions
    def click_on_the_ask_the_community_button(self):
        super()._click(self.ask_the_community_button)

    def get_selected_topic_option(self) -> str:
        option = super()._get_text_of_element(self.topic_dropdown_selected_option)
        return re.sub(r'\s+', ' ', option).strip()

    # Showing Questions Tagged section actions
    def get_text_of_selected_tag_filter_option(self) -> str:
        return super()._get_text_of_element(self.showing_questions_tagged_tag)

    def click_on_the_show_all_questions_option(self):
        super()._click(self.show_all_questions_option)

    # Question list actions
    def get_all_question_list_tags(self, question_id: str) -> list[str]:
        question_tags = self._get_text_of_elements(self.question_tag_list(question_id))
        return question_tags

    def extract_question_ids(self) -> list[str]:
        elements = self.all_listed_articles.all()
        id_values = []
        for element in elements:
            id_values.append(
                super()._get_element_attribute_value(
                    element, attribute="id"
                )
            )
        return id_values
