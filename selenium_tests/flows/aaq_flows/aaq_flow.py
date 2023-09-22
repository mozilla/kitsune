from selenium_tests.core.test_utilities import TestUtilities
from selenium_tests.pages.product_solutions_pages.product_solutions_page import (
    ProductSolutionsPage,
)
from selenium_tests.pages.top_navbar import TopNavbar
from selenium_tests.pages.user_questions_pages.aaq_form_page import AAQFormPage
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.pages.user_questions_pages.questions_page import QuestionPage


class AAQFlow(AAQFormPage, ProductSolutionsPage, TopNavbar, TestUtilities, QuestionPage):
    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def submit_valid_firefox_product_question_via_ask_now_fx_solutions(self) -> dict:
        random_number = str(super().generate_random_number(min_value=0, max_value=1000))
        super().click_on_ask_a_question_firefox_browser_option()
        super().click_ask_now_button()
        aaq_question_data = super().aaq_question_test_data
        aaq_subject = aaq_question_data["valid_firefox_question"]["subject"] + " " + random_number
        super().add_text_to_aaq_form_subject_field(aaq_subject)
        super().select_aaq_form_topic_value(
            aaq_question_data["valid_firefox_question"]["topic_value"]
        )
        super().add_text_to_aaq_textarea_field(
            aaq_question_data["valid_firefox_question"]["question_body"]
        )

        # Investigate why image upload is not working

        super().click_aaq_form_submit_button()
        super().is_post_reply_button_visible()
        current_page_url = super().current_url()

        return {"aaq_subject": aaq_subject, "question_page_url": current_page_url}
