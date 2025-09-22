from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class MediaGallery(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """General page locators belonging to the Media Gallery page."""
        self.upload_a_new_media_file_button = page.locator("a#btn-upload")
        self.search_gallery_searchbox = page.locator("form#gallery-search input")
        self.search_gallery_search_button = page.locator("form#gallery-search button")
        self.media_file = lambda media_file_name: page.locator(
            f"//ol[@id='media-list']//a[@title='{media_file_name}']")

        """Locators belonging to the Upload media modal."""
        self.upload_modal_image_preview = page.locator("//img[@class='preview']")
        self.upload_modal_delete_image = page.locator("//input[@value='Delete this image']")
        self.upload_modal_browse_button = page.locator("//input[@id='id_file']")
        self.upload_modal_locale_dropdown = page.locator("//select[@id='id_locale']")
        self.upload_modal_title_input_field = page.locator("//input[@id='id_title']")
        self.upload_modal_description_field = page.locator("//textarea[@id='id_description']")
        self.upload_modal_cancel_button = page.locator("//input[@value='Cancel']")
        self.upload_modal_upload_button = page.locator("//input[@value='Upload']")
        self.cancel_image_upload_during_upload_progress_button = page.locator(
            "//div[@class='field progress file off']//a[text()='Cancel']")

        """Locators belonging to the Edit Media description page."""
        self.edit_image_description_textarea = page.locator("//textarea[@id='id_description']")
        self.edit_image_save_image_button = page.locator("//button[text()='Save image']")

        """Locators belonging to the media item preview page."""
        self.image_heading = page.locator("h1[class='sumo-page-heading']")
        self.image_creator = page.locator("ul#media-meta li[class='creator'] a")
        self.image_description = page.locator("div[class='description'] p")
        self.articles_subtext = page.locator("div[class='documents'] p")
        self.image_in_documents_list = page.locator("div[class='documents'] li a")
        self.delete_this_image_button = page.locator("form#media-actions button")
        self.edit_this_image_button = page.locator("form#media-actions a")

        """Locators belonging to the insert media functionality at KB article level."""
        self.insert_media_panel = page.locator("div#media-modal")
        self.search_gallery_searchbox_modal = page.locator("form#gallery-modal-search input")
        self.search_gallery_search_button_modal = page.locator("form#gallery-modal-search button")
        self.show_images_filter = page.locator("div[class='type'] ol").get_by_role(
            "listitem", name="Images", exact=True)
        self.show_videos_filter = page.locator("div[class='type'] ol").get_by_role(
            "listitem", name="Videos", exact=True)
        self.cancel_media_insert_button = page.locator("a[href='#cancel']")
        self.upload_media_button = page.locator("//form[@id='gallery-upload-image']//"
                                                "input[@value='Upload']")
        self.insert_media_button = page.get_by_role("button", name="Insert Media", exact=True)
        self.linked_in_document = lambda document_name: page.locator(
            "div[class='documents'] li").get_by_role("link", name=document_name, exact=True)
        self.media_file = lambda media_file_name: page.locator(
            f"ol#media-list li a[title='{media_file_name}']")

        """Locators belonging to the delete image confirmation page."""
        self.delete_this_image_button = page.locator("//button[text()='Delete this image']")


    """General actions against the Media Gallery page."""
    def click_on_upload_a_new_media_file_button(self):
        """Click on the 'Upload' button inside the Media Gallery page."""
        self._click(self.upload_a_new_media_file_button)

    def is_image_media_file_displayed_in_gallery(self, media_file_name: str) -> bool:
        """
        Checks if a media file is displayed inside the Media Gallery page.
        Args:
            media_file_name (str): The name of the media file.
        """
        return self._is_element_visible(self.media_file(media_file_name))


    def click_on_a_media_file_from_gallery(self, media_file_name: str):
        """
        Click on a media file displayed inside the Media Gallery page.
        Args:
            media_file_name (str): The name of the media file.
        """

    """Actions against the 'Upload' media modal."""
    def click_on_upload_modal_delete_this_image_button(self):
        """Clicking on the 'Delete this Image' button from the 'Upload' media modal."""
        self._click(self.upload_modal_delete_image)

    def select_upload_modal_locale(self, locale: str):
        """
        Selects a locale (based on value) from the 'Locale' dropdown inside the 'Upload' modal.
        Args:
            locale (str): Locale value.
        """
        self._select_option_by_value(self.upload_modal_locale_dropdown, locale)

    def fill_upload_modal_title_field(self, title: str):
        """
        Fill data inside the 'Title' field from the 'Upload' modal.
        Args:
            title (str): The title to be given to the newly uploaded media file.
        """
        self._fill(self.upload_modal_title_input_field, title)

    def fill_upload_modal_description_field(self, description: str):
        """
        Fill data inside the 'Description' field from the 'Upload' modal.
        Args:
            description (str): The description to be given to the newly uploaded media file.
        """
        self._fill(self.upload_modal_description_field, description)

    def click_on_upload_modal_cancel_button(self):
        """Click on the 'Cancel' button from the 'Upload' modal."""
        self._click(self.upload_modal_cancel_button)

    def click_on_upload_modal_upload_button(self):
        """Click on the 'Upload' button from the 'Upload' modal."""
        self._click(self.upload_modal_upload_button)

    def click_on_cancel_button_during_upload_progress(self):
        """
        Click on the 'Cancel' button which is displayed during the image upload progress inside
        the 'Upload' modal. (Note that this button is displayed briefly until the image preview was
        successfully rendered)
        """
        self._click(self.cancel_image_upload_during_upload_progress_button)

    def is_cancel_button_during_upload_progress_displayed(self) -> bool:
        """
        Checks if the 'Cancel' button which is displayed during the image upload progress inside
        the 'Upload' modal is displayed or not. (Note that this button is displayed briefly until
        the image preview was successfully rendered)
        """
        return self._is_element_visible(self.cancel_image_upload_during_upload_progress_button)

    def is_upload_image_preview_rendered(self) -> bool:
        """
        Checks if the newly uploaded image preview is successfully rendered inside the 'Upload'
        modal.
        """
        return self._is_element_visible(self.upload_modal_image_preview)

    def wait_for_image_preview(self):
        self._wait_for_locator(self.upload_modal_image_preview)

    """Actions against the media preview page."""
    def get_image_heading(self) -> str:
        """Get the previewed image heading."""
        return self._get_text_of_element(self.image_heading)

    def get_image_creator_text(self) -> str:
        """Get the name of the image creator displayed inside the image preview page."""
        return self._get_text_of_element(self.image_creator)

    def click_on_image_creator_link(self):
        """Click on the image creator link inside the image preview page."""
        self._click(self.image_creator)

    def get_image_description(self) -> str:
        """Get the image description displayed inside the image preview page."""
        return self._get_text_of_element(self.image_description)

    def get_articles_section_subtext(self) -> str:
        """Get the text displayed inside the 'Articles' section from the image preview page."""
        return self._get_text_of_element(self.articles_subtext)

    def get_image_in_documents_list_items_text(self) -> list[str]:
        """
        Get a list of all documents listed inside the 'Articles' section from the image preview
        page.
        """
        return self._get_text_of_elements(self.image_in_documents_list)

    def click_on_a_linked_in_document(self, document_name: str):
        """
        Click on a document listed under the 'Articles' section from the image preview page.
        Args:
             document_name (str): Document name.
        """
        self._click(self.linked_in_document(document_name))

    def click_on_delete_this_image_button(self):
        """Click on the 'Delete this Image' button from the image preview page."""
        self._click(self.delete_this_image_button)

    def click_on_edit_this_image_button(self):
        """Click on the 'Edit this Image' button from the image preview page."""
        self._click(self.edit_this_image_button)

    """Actions against the image description edit page."""
    def fill_into_image_description_edit_textarea(self, text: str):
        """
            Fill data inside the 'Description' textarea from the edit image description page.
            Args:
                text (str): The new image description to be added.
        """
        self._clear_field(self.edit_image_description_textarea)
        self._fill(self.edit_image_description_textarea, text)

    def click_on_image_description_edit_save_button(self):
        """Click on the 'Save image' button from the edit image description page."""
        self._click(self.edit_image_save_image_button)

    """Actions against the Media Gallery's search functionality."""
    def fill_search_media_gallery_searchbox_input_field(self, text: str):
        """
            Fill data inside the Media Gallery's search box.
            Args:
                text (str): Search string.
        """
        self._fill(self.search_gallery_searchbox, text)

    def click_on_media_gallery_searchbox_search_button(self):
        """Click on the search button next to the Media Gallery's search box."""
        self._click(self.search_gallery_search_button)

    """Actions against the 'Insert Media...' kb panel."""
    def fill_search_modal_gallery_searchbox_input_field(self, text: str):
        """
        Fill data inside search box available inside the 'Insert media...' panel.
        Args:
            text(): Search string.
        """
        self._fill(self.search_gallery_searchbox_modal, text)

    def click_on_search_modal_gallery_search_button(self):
        """
        Click on the search button next to the search box available inside the 'Insert media...'
        panel.
        """
        self._click(self.search_gallery_search_button_modal)

    def click_on_images_filter(self):
        """Click on the 'Images' filter form the 'Insert media...' modal."""
        self._click(self.show_images_filter)

    def click_on_videos_filter(self):
        """Click on the 'Videos' filter from the 'Insert media...' modal."""
        self._click(self.show_videos_filter)

    def click_on_cancel_media_insert(self):
        """Click on the 'Cancel' button from the 'Insert media...' modal."""
        self._click(self.insert_media_button)

    def click_on_insert_media_button(self):
        """Click on the 'Insert Media' button from the 'Insert media...' modal."""
        self._click(self.insert_media_button)

    def click_on_upload_media_button(self):
        """Click on the 'Upload Media' button from the 'Insert media...' modal."""
        self._click(self.upload_media_button)

    def select_media_file_from_list(self, media_file_name: str, is_modal=False):
        """
        Select a media item from the 'Insert media...' modal.
        Args:
            media_file_name (str): The name of the media item to be selected.
            is_modal (bool): If (True) we are targeting the 'Insert media...'kb article panel. If
            (False) we are targeting the search box available inside the 'Media Gallery' page.
        """
        if is_modal:
            self.click_on_search_modal_gallery_search_button()
        else:
            self.click_on_media_gallery_searchbox_search_button()
        # We need to wait a bit so that the list finishes to update in case of search.
        self._wait_for_given_timeout(1000)
        self._click(self.media_file(media_file_name))


    """Actions against the media file deletion confirmation page."""
    def click_on_delete_this_image_confirmation_button(self):
        self.click_on_delete_this_image_button()
