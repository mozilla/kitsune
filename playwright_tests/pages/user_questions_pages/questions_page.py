from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class QuestionPage(BasePage):
    # "Posted successfully" green banner
    __posted_questions_success_banner_message = "//ul[@class='user-messages']/li/p"
    __posted_questions_success_banner_my_questions_link = "//ul[@class='user-messages']/li/p/a"
    __posted_questions_success_banner_close_button = "//ul[@class='user-messages']/li/button"

    # Question
    __question_author = "//div[@class='question']//span[@class='display-name']"

    # Progress bar
    __complete_progress_items_label = ("//li[@class='progress--item is-complete']//span["
                                       "@class='progress--label']")

    # Breadcrumbs
    __aaq_page_breadcrumbs = "//ol[@id='breadcrumbs']/li"

    # Question details
    __questions_header = "//article//h2"

    # Searchbar
    __search_support_searchbar = "//form[@id='support-search-sidebar']/input"
    __search_support_search_button = "//form[@id='support-search-sidebar']/button"

    # Still need help widget
    __still_need_help_ask_now_button = "//a[@data-event-label='aaq widget']"

    # Question Tools
    __edit_this_question_option = "//ul[@id='related-content']/li[@class='edit']/a"
    __stop_email_updates_option = "//ul[@id='related-content']/li[@class='email']/a"
    __subscribe_to_feed_option = "//ul[@id='related-content']/li[@class='rss']/a"
    __delete_this_question_option = "//ul[@id='related-content']//a[@class='delete']"

    # Tags section
    __question_tags_options = "//li[@class='tag']/a"

    # Post a reply section
    __post_a_reply_section_heading = "//h3[@class='sumo-card-heading']"
    __post_a_reply_textarea = "//textarea[@id='id_content']"
    __post_a_reply_textarea_bold_button = "//button[@title='Bold']"
    __post_a_reply_textarea_italic_button = "//button[@title='Italic']"
    __post_a_reply_textarea_link_button = "//button[@title='Insert a link...']"
    __post_a_reply_textarea_numbered_list_button = "//button[@title='Numbered List']"
    __post_a_reply_textarea_bulleted_list_button = "//button[@title='Bulleted List']"
    __common_responses_option = "//a[@title='Common responses']"

    # Needs more information from the user
    __needs_more_information_from_the_user_checkbox = "//input[@id='id_needs_info']"

    # Add images button

    # Preview Reply button
    __preview_reply_button = "//input[@id='preview']"

    # Post Reply button
    __post_reply_button = "//button[contains(text(),'Post Reply')]"

    # Delete question
    __delete_question_delete_button = "//input[@value='Delete']"
    __delete_question_cancel_button = "//a[contains(text(),'Cancel')]"

    def __init__(self, page: Page):
        super().__init__(page)

    def get_question_author_name(self) -> str:
        return super()._get_text_of_element(self.__question_author)

    def add_text_to_post_a_reply_textarea(self, text: str):
        super()._fill(self.__post_a_reply_textarea, text)

    def click_on_post_reply_button(self, repliant_username) -> str:
        xpath_display_name = \
            f"//span[@class='display-name' and contains(text(), '{repliant_username}')]"

        xpath_reply_id = (f"//span[@class='display-name' and contains(text(), "
                          f"'{repliant_username}')]/ancestor::div[@class='answer ']")
        super()._click(self.__post_reply_button)
        super()._wait_for_selector(xpath_display_name)
        return super()._get_element_attribute_value(xpath_reply_id, "id")

    def click_on_solves_the_problem_button(self, target_reply_id: str):
        xpath = f"//div[@id='{target_reply_id}']/following-sibling::aside//input[@type='submit']"

        super()._click(xpath)

    def is_post_reply_button_visible(self) -> ElementHandle:
        super()._wait_for_selector(self.__post_reply_button)
        return super()._get_element_handle(self.__post_reply_button)

    def click_on_the_reply_author(self, reply_id: str):
        xpath = f"//div[@id='{reply_id}']//a[@class='author-name']"
        super()._click(xpath)

    def click_delete_this_question_question_tools_option(self):
        super()._click(self.__delete_this_question_option)

    def click_delete_this_question_button(self):
        super()._click(self.__delete_question_delete_button)
