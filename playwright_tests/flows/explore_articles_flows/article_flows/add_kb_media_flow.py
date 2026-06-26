from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.contribute.contributor_tools_pages.media_gallery import MediaGallery


class AddKbMediaFlow:
    def __init__(self, page: Page):
        self.media_gallery_page = MediaGallery(page)
        self.utilities = Utilities(page)

    def add_media_to_kb_article(self, file_type, file_name):
        self.media_gallery_page.fill_search_modal_gallery_searchbox_input_field(file_name)
        self.media_gallery_page.select_media_file_from_list(file_name, is_modal=True)
        self.media_gallery_page.click_on_insert_media_button()

    def add_new_media_file_to_gallery(self, title: str, description:str, locale=None,
                                      path_to_file=None, submit=True, image_bytes=None,
                                      file_name=None):
        """
        Add a new media file to the Media Gallery.

        By default the uploaded image is generated in memory, so no image fixture needs to be
        committed to the project. Pass ``path_to_file`` to upload a specific on-disk image instead
        (e.g. when a test depends on the actual image content).
        Args:
            title (str): The title given to the uploaded media item.
            description (str): The description given to the uploaded media item.
            locale (str): The locale to select in the upload modal's locale dropdown. When omitted
                          the image is uploaded under the gallery page's current locale.
            path_to_file (str): Optional path to an on-disk image to upload instead of an in-memory
                                generated one.
            submit (bool): If True the 'Upload' button from the Upload modal is clicked. If False
                           the 'Cancel' button from the Upload modal is clicked.
            image_bytes (bytes): Optional in-memory image contents to upload (e.g. to control the
                                 file size). Ignored when ``path_to_file`` is provided.
            file_name (str): Optional filename to present when uploading in-memory bytes.
        """
        self.media_gallery_page.click_on_upload_a_new_media_file_button()
        if path_to_file is not None:
            # Upload a specific on-disk file under a unique filename so parallel runs uploading the
            # same image don't collide on the server-generated storage path (RenameFileStorage
            # derives the name from the upload's filename + a second-precision timestamp), which
            # can otherwise wipe out a sibling upload's file and 500 the finalize step.
            self.utilities.upload_file(
                self.media_gallery_page.upload_modal_browse_button, path_to_file, unique_name=True)
        else:
            # No fixture needed: generate the image in memory. upload_file falls back to a unique,
            # uuid-based filename when none is given, which likewise avoids the storage-path
            # collisions described above.
            self.utilities.upload_file(
                self.media_gallery_page.upload_modal_browse_button,
                file_buffer=image_bytes if image_bytes is not None
                else self.utilities.generate_in_memory_image(),
                file_name=file_name)

        self.media_gallery_page.wait_for_image_preview()
        if locale:
            self.media_gallery_page.select_upload_modal_locale(locale)
        self.media_gallery_page.fill_upload_modal_title_field(title)
        self.media_gallery_page.fill_upload_modal_description_field(description)
        if submit:
            self.media_gallery_page.click_on_upload_media_button()
        else:
            self.media_gallery_page.click_on_upload_modal_cancel_button()

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

