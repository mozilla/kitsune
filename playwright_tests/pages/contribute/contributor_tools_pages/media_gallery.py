from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page


class MediaGallery(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Media Gallery page locators.
        self.upload_a_new_media_file_button = page.locator("a#btn-upload")
        self.search_gallery_searchbox = page.locator("form#gallery-search input")
        self.search_gallery_search_button = page.locator("form#gallery-search button")

        # Media preview locators.
        self.image_heading = page.locator("h1[class='sumo-page-heading']")
        self.image_creator = page.locator("ul#media-meta li[class='creator'] a")
        self.image_description = page.locator("div[class='description'] p")
        self.image_in_documents_text = page.locator("div[class='documents'] p")
        self.image_in_documents_list = page.locator("div[class='documents'] li a")
        self.delete_this_image_button = page.locator("form#media-actions button")
        self.edit_this_image_button = page.locator("form#media-actions a")

        # Insert media... modal locators.
        self.insert_media_panel = page.locator("div#media-modal")
        self.search_gallery_searchbox_modal = page.locator("form#gallery-modal-search input")
        self.search_gallery_search_button_modal = page.locator("form#gallery-modal-search button")
        self.show_images_filter = page.locator("div[class='type'] ol").get_by_role(
            "listitem", name="Images", exact=True)
        self.show_videos_filter = page.locator("div[class='type'] ol").get_by_role(
            "listitem", name="Videos", exact=True)
        self.cancel_media_insert_button = page.locator("a[href='#cancel']")
        self.upload_media_button = page.get_by_role("link", name="Upload Media", exact=True)
        self.insert_media_button = page.get_by_role("button", name="Insert Media", exact=True)
        self.linked_in_document = lambda document_name: page.locator(
            "div[class='documents'] li").get_by_role("link", name=document_name, exact=True)
        self.media_file = lambda media_file_name: page.locator(
            f"ol#media-list li a[title='{media_file_name}']")

    # Media Gallery page actions.
    def click_on_upload_a_new_media_file_button(self):
        self._click(self.upload_a_new_media_file_button)

    # Media Gallery image preview actions.
    def get_image_heading(self) -> str:
        return self._get_text_of_element(self.image_heading)

    def get_image_creator_text(self) -> str:
        return self._get_text_of_element(self.image_creator)

    def click_on_image_creator_link(self):
        self._click(self.image_creator)

    def get_image_description(self) -> str:
        return self._get_text_of_element(self.image_description)

    def get_image_in_documents_text(self) -> str:
        return self._get_text_of_element(self.image_in_documents_text)

    def get_image_in_documents_list_items_text(self) -> list[str]:
        return self._get_text_of_elements(self.image_in_documents_list)

    def click_on_a_linked_in_document(self, document_name: str):
        self._click(self.linked_in_document(document_name))

    def click_on_delete_this_image_button(self):
        self._click(self.delete_this_image_button)

    def click_on_edit_this_image_button(self):
        self._click(self.edit_this_image_button)

    # Media Gallery search
    def fill_search_media_gallery_searchbox_input_field(self, text: str):
        self._fill(self.search_gallery_searchbox, text)

    def click_on_media_gallery_searchbox_search_button(self):
        self._click(self.search_gallery_search_button)

    # Modal search.
    def fill_search_modal_gallery_searchbox_input_field(self, text: str):
        self._fill(self.search_gallery_searchbox_modal, text)

    def click_on_search_modal_gallery_search_button(self):
        self._click(self.search_gallery_search_button_modal)

    # Insert Media... kb panel actions.
    def click_on_images_filter(self):
        self._click(self.show_images_filter)

    def click_on_videos_filter(self):
        self._click(self.show_videos_filter)

    def click_on_cancel_media_insert(self):
        self._click(self.insert_media_button)

    def click_on_upload_media_button(self):
        self._click(self.upload_media_button)

    def select_media_file_from_list(self, media_file_name: str, is_modal=False):
        if is_modal:
            self.click_on_search_modal_gallery_search_button()
        else:
            self.click_on_media_gallery_searchbox_search_button()
        # We need to wait a bit so that the list finishes to update in case of search.
        self._wait_for_given_timeout(1000)
        self._click(self.media_file(media_file_name))

    def click_on_insert_media_button(self):
        self._click(self.insert_media_button)
