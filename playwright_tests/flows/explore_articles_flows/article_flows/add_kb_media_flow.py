import os

from playwright.sync_api import Page, Locator

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.contribute.contributor_tools_pages.media_gallery import MediaGallery


class AddKbMediaFlow:
    def __init__(self, page: Page):
        self.media_gallery_page = MediaGallery(page)
        self.utilities = Utilities(page)

    def add_media_to_kb_article(self, file_type, file_name):
        if file_type == 'Videos':
            self.media_gallery_page.click_on_videos_filter()

        self.media_gallery_page.fill_search_modal_gallery_searchbox_input_field(file_name)
        self.media_gallery_page.select_media_file_from_list(file_name, is_modal=True)
        self.media_gallery_page.click_on_insert_media_button()

    def add_new_media_file_to_gallery(self, title: str, description:str, locale=None,
                                      path_to_file=None):
        """
        Add a new media file to the Media Gallery.
        Args:
            path_to_file (str): The path to the media item which is to be uploaded.
            title (str): The title given to the uploaded media item.
            description (str): The description given to the uploaded media item.
            locale (str): The locale under which the media item is to be uploaded
                          (defaults to en-US)
            submit (bool): If True the 'Upload' button from the Upload modal is clicked. If False
                           the 'Cancel' button from the Upload modal is clicked.
        """
        self.media_gallery_page.click_on_upload_a_new_media_file_button()
        self.utilities.upload_file(
            self.media_gallery_page.upload_modal_browse_button,
            path_to_file or os.path.abspath("test_data/test-image.png")
        )

        self.media_gallery_page.wait_for_image_preview()
        if locale:
            self.media_gallery_page.select_upload_modal_locale(locale)
        self.media_gallery_page.fill_upload_modal_title_field(title)
        self.media_gallery_page.fill_upload_modal_description_field(description)
        self.media_gallery_page.click_on_upload_media_button()

    def delete_media_file(self, media_file_title="None"):
        """
            Deletes and uploaded test image from the Media Gallery.
            Args:
                media_file_title (str): Optional. To be added if the current location is inside the
                media gallery and not inside the media preview.
        """
        if media_file_title:
            self.media_gallery_page.click_on_a_media_file_from_gallery(media_file_title)
        self.media_gallery_page.click_on_delete_this_image_button()
        self.media_gallery_page.click_on_delete_this_image_confirmation_button()

