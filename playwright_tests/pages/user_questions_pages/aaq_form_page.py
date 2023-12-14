from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class AAQFormPage(BasePage):
    __uploaded_image_title = ""
    __complete_progress_items = "//li[@class='progress--item is-complete']/a"
    __complete_progress_items_labels = ("//li[@class='progress--item is-complete']//span["
                                        "@class='progress--label']")
    __in_progress_item_label = ("//li[@class='progress--item is-current']//span["
                                "@class='progress--label']")
    __aaq_page_heading = "//h2[@class='sumo-page-heading']"
    __aaq_page_intro_text = "//form[@id='question-form']/p[@class='sumo-page-intro']"
    __aaq_page_info_card = "//div[contains(@class, 'info card')]"

    # AAQ Subject
    __aaq_subject_input_field = "//input[@id='id_title']"
    __aaq_subject_input_field_error_message = ("//input[@id='id_title']/../ul["
                                               "@class='errorlist']/li")

    # Product topic dropdown
    __product_topic_select_dropdown = "//select[@id='id_category']"
    __product_topic_select_dropdown_error_message = ("//select[@id='id_category']/../ul["
                                                     "@class='errorlist']/li")

    # How can we help textarea field
    __how_can_we_help_textarea = "//textarea[@id='id_content']"
    __how_can_we_help_textarea_error_field = ("//textarea[@id='id_content']/../following-sibling"
                                              "::ul/li")

    # Add Image
    __add_image_browse_button = "//input[@id='id_image']"
    __uploaded_test_image_preview = f"//img[@title='{__uploaded_image_title}']"
    __uploaded_test_image_delete_button = "//form[@class='upload-input']/input[@class='delete']"
    __uploaded_image = "//a[@class='image']/img"

    # Email me when someone answers the thread checkbox
    __email_me_checkbox = "//input[@id='id_notifications']"

    # form buttons
    __form_submit_button = "//button[contains(text(), 'Submit')]"
    __form_cancel_option = "//a[contains(text(),'Cancel')]"

    # Learn more button

    def __init__(self, page: Page):
        super().__init__(page)

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
        super()._fill(self.__aaq_subject_input_field, text)

    def select_aaq_form_topic_value(self, value: str):
        super()._select_option_by_value(self.__product_topic_select_dropdown, value)

    def add_text_to_aaq_textarea_field(self, text: str):
        super()._fill(self.__how_can_we_help_textarea, text)

    # def attach_image_to_question(self, image_path: str, image_title: str):
    # Need to update this when needed in tests
    # self.__uploaded_image_title = image_title
    # super()._upload_jpg_image(locator=self.__add_image_browse_button, path_to_image=image_path)

    def image_preview_element(self) -> ElementHandle:
        return super()._get_element_handle(self.__uploaded_test_image_preview)

    def uploaded_image_element(self) -> ElementHandle:
        return super()._get_element_handle(self.__uploaded_image)

    def click_on_email_me_when_someone_answers_the_thread_checkbox(self):
        super()._click(self.__email_me_checkbox)

    def click_aaq_form_cancel_button(self):
        super()._click(self.__form_cancel_option)

    def click_aaq_form_submit_button(self):
        super()._click(self.__form_submit_button)

    def delete_uploaded_image(self):
        super()._hover_over_element(self.__uploaded_image)
        super()._click(self.__uploaded_test_image_delete_button)
        super()._accept_dialog()
