from selenium.webdriver.common.by import By
from selenium_tests.core.base_page import BasePage
from selenium.webdriver.remote.webdriver import WebDriver


class QuestionPage(BasePage):
    # "Posted successfully" green banner
    __posted_questions_success_banner_message = (By.XPATH, "//ul[@class='user-messages']/li/p")
    __posted_questions_success_banner_my_questions_link = (
        By.XPATH,
        "//ul[@class='user-messages']/li/p/a",
    )
    __posted_questions_success_banner_close_button = (
        By.XPATH,
        "//ul[@class='user-messages']/li/button",
    )

    # Question
    __question_author = (By.XPATH, "//div[@class='question']//span[@class='display-name']")

    # Progress bar
    __complete_progress_items_label = (
        By.XPATH,
        "//li[@class='progress--item is-complete']//span[@class='progress--label']",
    )

    # Breadcrumbs
    __aaq_page_breadcrumbs = (By.XPATH, "//ol[@id='breadcrumbs']/li")

    # Question details
    __questions_header = (By.XPATH, "//article//h2")

    # Searchbar
    __search_support_searchbar = (By.XPATH, "//form[@id='support-search-sidebar']/input")
    __search_support_search_button = (By.XPATH, "//form[@id='support-search-sidebar']/button")

    # Still need help widget
    __still_need_help_ask_now_button = (By.XPATH, "//a[@data-event-label='aaq widget']")

    # Question Tools
    __edit_this_question_option = (By.XPATH, "//ul[@id='related-content']/li[@class='edit']/a")
    __stop_email_updates_option = (By.XPATH, "//ul[@id='related-content']/li[@class='email']/a")
    __subscribe_to_feed_option = (By.XPATH, "//ul[@id='related-content']/li[@class='rss']/a")
    __delete_this_question_option = (By.XPATH, "//ul[@id='related-content']//a[@class='delete']")

    # Tags section
    __question_tags_options = (By.XPATH, "//li[@class='tag']/a")

    # Post a reply section
    __post_a_reply_section_heading = (By.XPATH, "//h3[@class='sumo-card-heading']")
    __post_a_reply_textarea = (By.XPATH, "//textarea[@id='id_content']")
    __post_a_reply_textarea_bold_button = (By.XPATH, "//button[@title='Bold']")
    __post_a_reply_textarea_italic_button = (By.XPATH, "//button[@title='Italic']")
    __post_a_reply_textarea_link_button = (By.XPATH, "//button[@title='Insert a link...']")
    __post_a_reply_textarea_numbered_list_button = (By.XPATH, "//button[@title='Numbered List']")
    __post_a_reply_textarea_bulleted_list_button = (By.XPATH, "//button[@title='Bulleted List']")
    __common_responses_option = (By.XPATH, "//a[@title='Common responses']")

    # Needs more information from the user
    __needs_more_information_from_the_user_checkbox = (By.XPATH, "//input[@id='id_needs_info']")

    # Add images button

    # Preview Reply button
    __preview_reply_button = (By.XPATH, "//input[@id='preview']")

    # Post Reply button
    __post_reply_button = (By.XPATH, "//button[contains(text(),'Post Reply')]")

    # Delete question
    __delete_question_delete_button = (By.XPATH, "//input[@value='Delete']")
    __delete_question_cancel_button = (By.XPATH, "//a[contains(text(),'Cancel')]")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_question_author_name(self) -> str:
        return super()._get_text_of_element(self.__question_author)

    def add_text_to_post_a_reply_textarea(self, text: str):
        super()._type(self.__post_a_reply_textarea, text)

    def click_on_post_reply_button(self, repliant_username) -> str:
        xpath_display_name = (
            By.XPATH,
            f"//span[@class='display-name' and contains(text(), '{repliant_username}')]",
        )
        xpath_reply_id = (
            By.XPATH,
            f"//span[@class='display-name' and contains(text(),"
            f" '{repliant_username}')]/ancestor::div[@class='answer ']",
        )
        super()._click(self.__post_reply_button)
        super()._is_element_displayed(xpath_display_name)
        return super()._get_attribute_value_of_web_element(
            web_element=xpath_reply_id, attribute="id"
        )

    def click_on_solves_the_problem_button(self, target_reply_id: str):
        xpath = (
            By.XPATH,
            f"//div[@id='{target_reply_id}']/following-sibling::aside//input[" f"@type='submit']",
        )
        super()._click(xpath)

    def is_post_reply_button_visible(self) -> bool:
        return super()._is_element_displayed(self.__post_reply_button)

    def click_on_the_reply_author(self, reply_id: str):
        xpath = (By.XPATH, f"//div[@id='{reply_id}']//a[@class='author-name']")
        super()._click(xpath)

    def click_delete_this_question_question_tools_option(self):
        super()._click(self.__delete_this_question_option)

    def click_delete_this_question_button(self):
        super()._click(self.__delete_question_delete_button)
