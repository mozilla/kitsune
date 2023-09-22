from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class AAQFormPage(BasePage):
    __uploaded_image_title = ""

    __complete_progress_items = (By.XPATH, "//li[@class='progress--item is-complete']/a")
    __complete_progress_items_labels = (
        By.XPATH,
        "//li[@class='progress--item is-complete']//span[" "@class='progress--label']",
    )
    __in_progress_item_label = (
        By.XPATH,
        "//li[@class='progress--item is-current']//span[@class='progress--label']",
    )
    __aaq_page_heading = (By.XPATH, "//h2[@class='sumo-page-heading']")
    __aaq_page_intro_text = (By.XPATH, "//form[@id='question-form']/p[@class='sumo-page-intro']")
    __aaq_page_info_card = (By.XPATH, "//div[contains(@class, 'info card')]")

    # AAQ Subject
    __aaq_subject_input_field = (By.XPATH, "//input[@id='id_title']")
    __aaq_subject_input_field_error_message = (
        By.XPATH,
        "//input[@id='id_title']/../ul[@class='errorlist']/li",
    )

    # Product topic dropdown
    __product_topic_select_dropdown = (By.XPATH, "//select[@id='id_category']")
    __product_topic_select_dropdown_error_message = (
        By.XPATH,
        "//select[@id='id_category']/../ul[@class='errorlist']/li",
    )

    # How can we help textarea field
    __how_can_we_help_textarea = (By.XPATH, "//textarea[@id='id_content']")
    __how_can_we_help_textarea_error_field = (
        By.XPATH,
        "//textarea[@id='id_content']/../following-sibling::ul/li",
    )

    # Add Image
    __add_image_browse_button = (By.XPATH, "//input[@id='id_image']")
    __uploaded_test_image_preview = (By.XPATH, f"//img[@title='{__uploaded_image_title}']")
    __uploaded_test_image_delete_button = (
        By.XPATH,
        "//form[@class='upload-input']/input[@class='delete']",
    )
    __uploaded_image = (By.XPATH, "//a[@class='image']/img")
    # Email me when someone answers the thread checkbox
    __email_me_checkbox = (By.XPATH, "//input[@id='id_notifications']")

    # form buttons
    __form_submit_button = (By.XPATH, "//button[contains(text(), 'Submit')]")
    __form_cancel_option = (By.XPATH, "//a[contains(text(),'Cancel')]")

    # Learn more button

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_complete_progress_item_labels(self) -> list[str]:
        return super()._get_text_of_elements(self.__complete_progress_items_labels)

    def get_in_progress_item_label(self) -> str:
        return super()._get_text_of_element(self.__in_progress_item_label)

    def get_aaq_form_page_heading(self) -> str:
        return super()._get_text_of_element(self.__aaq_page_heading)

    def get_aaq_form_page_intro_text(self) -> str:
        return super()._get_text_of_element(self.__aaq_page_intro_text)

    def get_aaq_form_info_card_text(self) -> str:
        return super()._get_text_of_element(self.__aaq_page_info_card)

    def get_aaq_form_subject_error(self) -> str:
        return super()._get_text_of_element(self.__aaq_subject_input_field_error_message)

    def get_aaq_form_topic_select_error(self) -> str:
        return super()._get_text_of_element(self.__product_topic_select_dropdown_error_message)

    def add_text_to_aaq_form_subject_field(self, text: str):
        super()._type(self.__aaq_subject_input_field, text)

    def select_aaq_form_topic_value(self, value: str):
        super()._select_option_by_value(self.__product_topic_select_dropdown, value)

    def add_text_to_aaq_textarea_field(self, text: str):
        super()._type(self.__how_can_we_help_textarea, text)

    def attach_image_to_question(self, image_path: str, image_title: str):
        self.__uploaded_image_title = image_title
        super()._upload_jpg_image(locator=self.__add_image_browse_button, path_to_image=image_path)

    def is_image_preview_displayed(self) -> bool:
        return super()._is_element_displayed(self.__uploaded_test_image_preview)

    def is_uploaded_image_displayed(self) -> bool:
        return super()._is_element_displayed(self.__uploaded_image)

    def click_on_email_me_when_someone_answers_the_thread_checkbox(self):
        super()._click(self.__email_me_checkbox)

    def click_aaq_form_cancel_button(self):
        super()._click(self.__form_cancel_option)

    def click_aaq_form_submit_button(self):
        super()._click(self.__form_submit_button)

    def delete_uploaded_image(self):
        super()._mouseover_element(self.__uploaded_image)
        super()._click(self.__uploaded_test_image_delete_button)
        super()._accept_alert()
