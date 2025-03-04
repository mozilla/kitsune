from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage


class AAQFormPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.__uploaded_image_title = ""
        self.premium_ticket_message = page.locator("ul[class='user-messages'] p")

        # Breadcrumb locators.
        self.in_progress_item_label = page.locator(
            "li[class='progress--item is-current'] span[class='progress--label']")
        self.milestone_by_name = lambda milestone_name: page.locator(
            f'//span[@class="progress--label" and text()="{milestone_name}"]/../..')

        # AAQ form page content locators.
        self.aaq_page_logo = page.locator("img[class='page-heading--logo']")
        self.aaq_page_product_heading = page.locator("//div[@id='main-content']/article/h3")
        self.aaq_page_intro_text = page.locator("form#question-form p[class='sumo-page-intro']")
        self.aaq_page_info_card = page.locator("div[class*='info card']")

        # AAQ Subject locators.
        self.aaq_subject_input_field = page.locator("input#id_title")
        self.premium_aaq_subject_input_field = page.locator("input#id_subject")
        self.aaq_subject_input_field_error_message = page.locator("input#id_title + ul li")

        # Loginless form locators.
        self.loginless_contact_email_input_field = page.locator("input#id_email")

        # Product topic dropdown locators.
        self.product_topic_options = page.locator("select#id_category option")
        self.product_topic_options_without_default_none = page.locator(
            "select#id_category option:not([value=''])")
        self.product_topic_select_dropdown = page.locator("select#id_category")
        self.product_topic_select_dropdown_error_message = page.locator(
            "select#id_category ~ ul[class='errorlist'] li"
        )

        # Product os dropdown locators (Available for Mozilla VPN product only).
        self.product_os_select_dropdown_options = page.locator("select#id_os option")
        self.product_os_select_dropdown = page.locator("select#id_os")

        # How can we help textarea field locators.
        self.how_can_we_help_textarea = page.locator("textarea#id_content")
        self.tell_us_more_premium_product_textarea = page.locator("textarea#id_description")
        self.how_can_we_help_textarea_error_field = page.locator(
            "//textarea[@id='id_content']/../following-sibling::ul/li")

        # Add Image locators.
        self.add_image_browse_button = page.locator("//span[text()='Browse...']/..")
        self.uploaded_test_image_preview = page.locator("img[title='{__uploaded_image_title}']")
        self.uploaded_test_image_delete_button = page.locator(
            "form[class='upload-input'] input[class='delete']")
        self.uploaded_image = page.locator("a[class='image'] img")

        # Email me when someone answers the thread checkbox locators.
        self.email_me_checkbox = page.locator("input#id_notifications")

        # Form buttons locators.
        self.form_submit_button = page.get_by_role("button").filter(has_text="Submit")
        self.save_edit_question_button = page.get_by_role(
            "button", name="Save Question", exact=True)
        self.form_update_answer_button = page.get_by_role(
            "button", name="Update answer", exact=True)
        self.form_cancel_option = page.get_by_role("link").filter(has_text="Cancel")

        # Share Data locators.
        self.share_data_button = page.locator("button#share-data")
        self.troubleshooting_information_textarea = page.locator("textarea#id_troubleshooting")
        self.try_these_manual_steps_link = page.locator("p#troubleshooting-manual a")
        self.show_details_option = page.locator("a[class='show']")
        self.product_version_input = page.locator("input#id_ff_version")
        self.product_os = page.locator("input#id_os")

        # Helpful Tip section locators.
        self.helpful_tip_section = page.locator(
            "aside[class='sumo-l-two-col--sidebar'] div[class='large-only']")

        # Learn more button locators.
        self.learn_more_button = page.locator("aside[class='sumo-l-two-col--sidebar'] a")

    def fill_contact_email_field(self, text: str):
        self._fill(self.loginless_contact_email_input_field, text)

    def get_premium_card_submission_message(self) -> str:
        return self._get_text_of_element(self.premium_ticket_message)

    # Breadcrumb actions.
    def get_in_progress_item_label(self) -> str:
        return self._get_text_of_element(self.in_progress_item_label)

    def click_on_a_particular_completed_milestone(self, milestone_name: str):
        self._click(self.milestone_by_name(milestone_name))

    # Question subject actions.
    def get_value_of_subject_input_field(self) -> str:
        return self._get_element_input_value(self.aaq_subject_input_field)

    def clear_subject_input_field(self):
        self._clear_field(self.aaq_subject_input_field)

    def get_aaq_form_subject_error(self) -> str:
        return self._get_text_of_element(self.aaq_subject_input_field_error_message)

    def add_text_to_aaq_form_subject_field(self, text: str):
        self._fill(self.aaq_subject_input_field, text)

    def add_text_to_premium_aaq_form_subject_field(self, text: str):
        self._fill(self.premium_aaq_subject_input_field, text)

    def add_text_to_premium_aaq_textarea_body_field(self, text: str):
        self._fill(self.tell_us_more_premium_product_textarea, text)

    # Question body actions.
    def get_value_of_question_body_textarea_field(self) -> str:
        return self._get_element_input_value(self.how_can_we_help_textarea)

    def clear_the_question_body_textarea_field(self):
        self._clear_field(self.how_can_we_help_textarea)

    def get_aaq_form_body_error(self) -> str:
        return self._get_text_of_element(self.how_can_we_help_textarea_error_field)

    def add_text_to_aaq_textarea_field(self, text: str):
        self._fill(self.how_can_we_help_textarea, text)

    # Question image actions.
    def image_preview_element(self) -> ElementHandle:
        return self._get_element_handle(self.uploaded_test_image_preview)

    def uploaded_image_locator(self) -> Locator:
        try:
            self._wait_for_locator(self.uploaded_image)
        except TimeoutError:
            print("Uploaded image not displayed")
        return self.uploaded_image

    def uploaded_images_handles(self) -> list[ElementHandle]:
        return self._get_element_handles(self.uploaded_image)

    def get_upload_image_button_locator(self) -> Locator:
        return self.add_image_browse_button

    # Page content actions.
    def get_product_image_locator(self) -> Locator:
        return self.aaq_page_logo

    def get_aaq_form_page_heading(self) -> str:
        return self._get_text_of_element(self.aaq_page_product_heading)

    def get_aaq_form_page_intro_text(self) -> str:
        return self._get_text_of_element(self.aaq_page_intro_text)

    def get_aaq_form_info_card_text(self) -> str:
        return self._get_text_of_element(self.aaq_page_info_card)

    def get_learn_more_button_locator(self) -> Locator:
        return self.learn_more_button

    def get_helpful_tip_locator(self) -> Locator:
        return self.helpful_tip_section

    # Question topic actions.
    def get_aaq_form_topic_select_error(self) -> str:
        return self._get_text_of_element(self.product_topic_select_dropdown_error_message)

    # Returns all the non-default selectable topic options.
    def get_aaq_form_topic_options(self) -> list[str]:
        return self._get_text_of_elements(self.product_topic_options_without_default_none)

    def select_aaq_form_topic_value(self, value: str):
        self._select_option_by_value(self.product_topic_select_dropdown, value)

    def add_text_to_product_version_field(self, text: str):
        self._fill(self.product_version_input, text)

    def add_text_to_os_field(self, text: str):
        self._fill(self.product_os, text)

    def select_aaq_form_os_value(self, value: str):
        self._select_option_by_value(self.product_os_select_dropdown_options, value)

    # Troubleshooting information actions.
    def add_text_to_troubleshooting_information_textarea(self, text: str):
        self._fill(self.troubleshooting_information_textarea, text)

    def click_on_learn_more_button(self):
        self._click(self.learn_more_button)

    def is_os_dropdown_menu_visible(self) -> bool:
        return self._is_element_visible(self.product_os_select_dropdown)

    def select_random_os_by_value(self):
        self._select_random_option_by_value(self.product_os_select_dropdown,
                                            self.product_os_select_dropdown_options)

    def select_random_topic_by_value(self):
        self._select_random_option_by_value(self.product_topic_select_dropdown,
                                            self.product_topic_options)

    def click_on_share_data_button(self):
        self._click(self.share_data_button)

    def click_on_show_details_option(self):
        self._click(self.show_details_option)

    # Instead of clicking on the 'Try these manual steps' button we are going to perform the
    # assertion by checking that the element has the correct href value. Navigating to prod can
    # yield a 429 error which we want to avoid.
    def get_try_these_manual_steps_link(self) -> str:
        return self._get_element_attribute_value(self.try_these_manual_steps_link, "href")

    # Email me when someone answers the thread section actions.
    def click_on_email_me_when_someone_answers_the_thread_checkbox(self):
        self._click(self.email_me_checkbox)

    def click_aaq_form_cancel_button(self):
        self._click(self.form_cancel_option)

    def click_aaq_form_submit_button(self, expected_locator=None):
        self._click(self.form_submit_button, expected_locator=expected_locator)

    # Edit question form actions.
    def click_aaq_edit_submit_button(self):
        self._click(self.save_edit_question_button)

    def click_on_update_answer_button(self):
        self._click(self.form_update_answer_button)
