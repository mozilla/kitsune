from playwright.sync_api import ElementHandle, Locator, Page
from playwright_tests.core.basepage import BasePage


class AAQFormPage(BasePage):

    def __init__(self, page: Page):
        super().__init__(page)
        self.__uploaded_image_title = ""
        self.premium_ticket_message = page.locator("ul[class='user-messages'] p")

        """"Locators belonging to the breadcrumbs section."""
        self.in_progress_item_label = page.locator(
            "li[class='progress--item is-current'] span[class='progress--label']")
        self.milestone_by_name = lambda milestone_name: page.locator(
            f'//span[@class="progress--label" and text()="{milestone_name}"]/../..')

        """Locators belonging to the AAQ form page."""
        self.aaq_page_logo = page.locator("img[class='page-heading--logo']")
        self.aaq_page_product_heading = page.locator("//div[@id='main-content']/article/h3")
        self.aaq_page_intro_text = page.locator("form#question-form p[class='sumo-page-intro']")
        self.aaq_page_info_card = page.locator("div[class*='info card']")

        """Locators belonging to the AAQ subject form field."""
        self.aaq_subject_input_field = page.locator("input#id_title")
        self.premium_aaq_subject_input_field = page.locator("input#id_subject")
        self.aaq_subject_input_field_error_message = page.locator("input#id_title + ul li")

        """Locators belonging to the loginless form."""
        self.loginless_contact_email_input_field = page.locator("input#id_email")

        """"Locators belonging to the product topic dropdown."""
        self.product_topic_options = page.locator("select#id_category option")
        self.product_topic_options_without_default_none = page.locator(
            "select#id_category option:not([value=''])")
        self.product_topic_select_dropdown = page.locator("select#id_category")
        self.product_topic_select_dropdown_error_message = page.locator(
            "select#id_category ~ ul[class='errorlist'] li"
        )

        """Locators belonging to the product os dropdown (Specific to Mozilla VPN)"""
        self.product_os_select_dropdown_options = page.locator("select#id_os option")
        self.product_os_select_dropdown = page.locator("select#id_os")

        """Locators belonging to the Thunderbird version input field"""
        self.thunderbird_version_field = page.locator("//input[@id='id_tb_version']")

        """Locators belonging to the update channel (Firefox for Enterprise product) dropdown"""
        self.update_channel_dropdown_options = page.locator(
            "//select[@id='id_update_channel']/option")
        self.update_channel_dropdown = page.locator("//select[@id='id_update_channel']")

        """Locators belonging to the ways of distributing policies (Firefox for enterprise product)
        dropdown.
        """
        self.distributing_policies_dropdown_options = page.locator(
            "//select[@id='id_policy_distribution']/option")
        self.distributing_policies_dropdown = page.locator("//select[@id='id_policy_distribution']")

        """Locators belonging to the how can we help textarea field."""
        self.how_can_we_help_textarea = page.locator("textarea#id_content")
        self.tell_us_more_premium_product_textarea = page.locator("textarea#id_description")
        self.how_can_we_help_textarea_error_field = page.locator(
            "//textarea[@id='id_content']/../following-sibling::ul/li")

        """Locators belonging to the 'Add Image' section."""
        self.add_image_browse_button = page.locator("//span[text()='Browse...']/..")
        self.uploaded_test_image_preview = page.locator("img[title='{__uploaded_image_title}']")
        self.uploaded_test_image_delete_button = page.locator(
            "form[class='upload-input'] input[class='delete']")
        self.uploaded_image = page.locator("a[class='image'] img")

        """Locators belonging to the Email me when someone answers the thread checkbox."""
        self.email_me_checkbox = page.locator("input#id_notifications")

        """"Locators belonging to the form buttons."""
        self.form_submit_button = page.get_by_role("button").filter(has_text="Submit")
        self.save_edit_question_button = page.get_by_role(
            "button", name="Save Question", exact=True)
        self.form_update_answer_button = page.get_by_role(
            "button", name="Update answer", exact=True)
        self.form_cancel_option = page.get_by_role("link").filter(has_text="Cancel")

        """Locators belonging to the Share Data section."""
        self.share_data_button = page.locator("button#share-data")
        self.troubleshooting_information_textarea = page.locator("textarea#id_troubleshooting")
        self.try_these_manual_steps_link = page.locator("div#troubleshooting-manual a")
        self.show_details_option = page.locator("a[class='show']")
        self.product_version_input = page.locator("input#id_ff_version")
        self.product_os = page.locator("input#id_os")

        """Locators belonging to the Helpful tip section."""
        self.helpful_tip_section = page.locator(
            "aside[class='sumo-l-two-col--sidebar'] div[class='large-only']")

    def fill_contact_email_field(self, text: str):
        self._fill(self.loginless_contact_email_input_field, text)

    """Actions against the breadcrumb locators."""
    def click_on_a_particular_completed_milestone(self, milestone_name: str):
        self._click(self.milestone_by_name(milestone_name))

    """Actions against the question subject locators."""
    def clear_subject_input_field(self):
        self._clear_field(self.aaq_subject_input_field)

    def add_text_to_aaq_form_subject_field(self, text: str):
        self._fill(self.aaq_subject_input_field, text)

    def add_text_to_premium_aaq_form_subject_field(self, text: str):
        self._fill(self.premium_aaq_subject_input_field, text)

    def add_text_to_premium_aaq_textarea_body_field(self, text: str):
        self._fill(self.tell_us_more_premium_product_textarea, text)

    """Actions against the question body locators."""
    def clear_the_question_body_textarea_field(self):
        self._clear_field(self.how_can_we_help_textarea)

    def add_text_to_aaq_textarea_field(self, text: str):
        self._fill(self.how_can_we_help_textarea, text)

    """Actions against the question image section locators."""
    def image_preview_element(self) -> ElementHandle:
        return self._get_element_handle(self.uploaded_test_image_preview)

    def uploaded_image_locator(self) -> Locator:
        try:
            self._wait_for_locator(self.uploaded_image)
        except TimeoutError:
            print("Uploaded image not displayed")
        return self.uploaded_image

    """Actions against the question topic locators."""
    def get_aaq_form_topic_options(self) -> list[str]:
        # Returns all the non-default selectable topic options.
        return self._get_text_of_elements(self.product_topic_options_without_default_none)

    def select_aaq_form_topic_value(self, value: str):
        self._select_option_by_value(self.product_topic_select_dropdown, value)

    def add_text_to_product_version_field(self, text: str):
        self._fill(self.product_version_input, text)

    def add_text_to_os_field(self, text: str):
        self._fill(self.product_os, text)

    """Actions against the Troubleshooting information section locators."""
    def add_text_to_troubleshooting_information_textarea(self, text: str):
        self._fill(self.troubleshooting_information_textarea, text)

    def is_os_dropdown_menu_visible(self) -> bool:
        return self._is_element_visible(self.product_os_select_dropdown)

    def is_thunderbird_version_field_visible(self) -> bool:
        return self._is_element_visible(self.thunderbird_version_field)

    def add_text_to_thunderbird_version_field(self, txt: str):
        self._fill(self.thunderbird_version_field, txt)

    def select_random_os_by_value(self):
        self._select_random_option_by_value(self.product_os_select_dropdown,
                                            self.product_os_select_dropdown_options)

    def select_random_topic_by_value(self):
        self._select_random_option_by_value(self.product_topic_select_dropdown,
                                            self.product_topic_options)

    def select_random_update_channel_by_value(self):
        self._select_random_option_by_value(self.update_channel_dropdown,
                                            self.update_channel_dropdown_options)

    def select_random_distributing_policies_by_value(self):
        self._select_random_option_by_value(self.distributing_policies_dropdown,
                                            self.distributing_policies_dropdown_options)

    def click_on_share_data_button(self):
        self._click(self.share_data_button)

    def click_on_show_details_option(self):
        self._click(self.show_details_option)

    """Actions against the email me when someone answers the thread section locators."""
    def click_aaq_form_cancel_button(self):
        self._click(self.form_cancel_option)

    def click_aaq_form_submit_button(self, expected_locator=None, with_force=False):
        self._click(self.form_submit_button, expected_locator=expected_locator,
                    with_force=with_force)

    """Actions against the edit question form page locators."""
    def click_aaq_edit_submit_button(self):
        self._click(self.save_edit_question_button)

    def click_on_update_answer_button(self):
        self._click(self.form_update_answer_button)
