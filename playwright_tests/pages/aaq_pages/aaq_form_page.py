from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage


class AAQFormPage(BasePage):
    __uploaded_image_title = ""

    # Breadcrumb locators.
    __in_progress_item_label = ("//li[@class='progress--item is-current']//span["
                                "@class='progress--label']")
    # AAQ form page content locators.
    __aaq_page_logo = "//img[@class='page-heading--logo']"
    __aaq_page_product_heading = "//div[@id='main-content']/article/h3"
    __aaq_page_intro_text = "//form[@id='question-form']/p[@class='sumo-page-intro']"
    __aaq_page_info_card = "//div[contains(@class, 'info card')]"

    # AAQ Subject locators.
    __aaq_subject_input_field = "//input[@id='id_title']"
    __aaq_subject_input_field_error_message = "//input[@id='id_title']/following-sibling::ul/li"

    # Product topic dropdown locators.
    __product_topic_options = "//select[@id='id_category']/option"
    __product_topic_options_without_default_none = ('//select[@id="id_category"]/option[not('
                                                    '@value="")]')
    __product_topic_select_dropdown = "//select[@id='id_category']"
    __product_topic_select_dropdown_error_message = ("//select[@id='id_category']/../ul["
                                                     "@class='errorlist']/li")

    # Product os dropdown locators (Available for Mozilla VPN product only).
    __product_os_select_dropdown = "//select[@id='id_os']"

    # How can we help textarea field locators.
    __how_can_we_help_textarea = "//textarea[@id='id_content']"
    __how_can_we_help_textarea_error_field = ("//textarea[@id='id_content']/../following-sibling"
                                              "::ul/li")

    # Add Image locators.
    __add_image_browse_button = "//span[text()='Browse...']/.."
    __uploaded_test_image_preview = f"//img[@title='{__uploaded_image_title}']"
    __uploaded_test_image_delete_button = "//form[@class='upload-input']/input[@class='delete']"
    __uploaded_image = "//a[@class='image']/img"

    # Email me when someone answers the thread checkbox locators.
    __email_me_checkbox = "//input[@id='id_notifications']"

    # Form buttons locators.
    __form_submit_button = "//button[contains(text(), 'Submit')]"
    __save_edit_question_button = "//button[text()='Save Question']"
    __form_cancel_option = "//a[contains(text(),'Cancel')]"

    # Share Data locators.
    __share_data_button = "//button[@id='share-data']"
    __troubleshooting_information_textarea = "//textarea[@id='id_troubleshooting']"
    __try_these_manual_steps_link = "//p[@id='troubleshooting-manual']/a"
    __show_details_option = "//a[@class='show']"
    __product_version_input = "//input[@id='id_ff_version']"
    __product_os = "//input[@id='id_os']"

    # Helpful Tip section locators.
    __helpful_tip_section = "//aside[@class='sumo-l-two-col--sidebar']/div[@class='large-only']"

    # Learn more button locators.
    __learn_more_button = "//aside[@class='sumo-l-two-col--sidebar']//a"

    def __init__(self, page: Page):
        super().__init__(page)

    # Breadcrumb actions.
    def get_in_progress_item_label(self) -> str:
        return super()._get_text_of_element(self.__in_progress_item_label)

    def click_on_a_particular_completed_milestone(self, milestone_name: str):
        xpath = f'//span[@class="progress--label" and text()="{milestone_name}"]/../..'
        super()._click(xpath)

    # Question subject actions.
    def get_value_of_subject_input_field(self) -> str:
        return super()._get_element_input_value(self.__aaq_subject_input_field)

    def clear_subject_input_field(self):
        super()._clear_field(self.__aaq_subject_input_field)

    def get_aaq_form_subject_error(self) -> str:
        return super()._get_text_of_element(self.__aaq_subject_input_field_error_message)

    def add_text_to_aaq_form_subject_field(self, text: str):
        super()._fill(self.__aaq_subject_input_field, text)

    # Question body actions.
    def get_value_of_question_body_textarea_field(self) -> str:
        return super()._get_element_input_value(self.__how_can_we_help_textarea)

    def clear_the_question_body_textarea_field(self):
        super()._clear_field(self.__how_can_we_help_textarea)

    def get_aaq_form_body_error(self) -> str:
        return super()._get_text_of_element(self.__how_can_we_help_textarea_error_field)

    def add_text_to_aaq_textarea_field(self, text: str):
        super()._fill(self.__how_can_we_help_textarea, text)

    # Question image actions.
    def image_preview_element(self) -> ElementHandle:
        return super()._get_element_handle(self.__uploaded_test_image_preview)

    def uploaded_image_locator(self) -> Locator:
        try:
            super()._wait_for_selector(self.__uploaded_image)
        except TimeoutError:
            print("Uploaded image not displayed")
        return super()._get_element_locator(self.__uploaded_image)

    def uploaded_images_handles(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__uploaded_image)

    def get_upload_image_button_locator(self) -> Locator:
        return super()._get_element_locator(self.__add_image_browse_button)

    # Page content actions.
    def get_product_image_locator(self) -> Locator:
        return super()._get_element_locator(self.__aaq_page_logo)

    def get_aaq_form_page_heading(self) -> str:
        return super()._get_text_of_element(self.__aaq_page_product_heading)

    def get_aaq_form_page_intro_text(self) -> str:
        return super()._get_text_of_element(self.__aaq_page_intro_text)

    def get_aaq_form_info_card_text(self) -> str:
        return super()._get_text_of_element(self.__aaq_page_info_card)

    def get_learn_more_button_locator(self) -> Locator:
        return super()._get_element_locator(self.__learn_more_button)

    def get_helpful_tip_locator(self) -> Locator:
        return super()._get_element_locator(self.__helpful_tip_section)

    # Question topic actions.
    def get_aaq_form_topic_select_error(self) -> str:
        return super()._get_text_of_element(self.__product_topic_select_dropdown_error_message)

    # Returns all the non-default selectable topic options.
    def get_aaq_form_topic_options(self) -> list[str]:
        return super()._get_text_of_elements(self.__product_topic_options_without_default_none)

    def select_aaq_form_topic_value(self, value: str):
        super()._select_option_by_value(self.__product_topic_select_dropdown, value)

    def add_text_to_product_version_field(self, text: str):
        super()._fill(self.__product_version_input, text)

    def add_text_to_os_field(self, text: str):
        super()._fill(self.__product_os, text)

    def select_aaq_form_os_value(self, value: str):
        super()._select_option_by_value(self.__product_os_select_dropdown, value)

    # Troubleshooting information actions.
    def add_text_to_troubleshooting_information_textarea(self, text: str):
        super()._fill(self.__troubleshooting_information_textarea, text)

    def click_on_learn_more_button(self):
        super()._click(self.__learn_more_button)

    def click_on_share_data_button(self):
        super()._click(self.__share_data_button)

    def click_on_show_details_option(self):
        super()._click(self.__show_details_option)

    def click_on_try_these_manual_steps_link(self):
        super()._click(self.__try_these_manual_steps_link)

    # Email me when someone answers the thread section actions.
    def click_on_email_me_when_someone_answers_the_thread_checkbox(self):
        super()._click(self.__email_me_checkbox)

    def click_aaq_form_cancel_button(self):
        super()._click(self.__form_cancel_option)

    def click_aaq_form_submit_button(self):
        super()._click(self.__form_submit_button)

    # Edit question form actions.
    def click_aaq_edit_submit_button(self):
        super()._click(self.__save_edit_question_button)
