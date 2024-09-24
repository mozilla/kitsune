from playwright.sync_api import Page

from playwright_tests.pages.contribute.contributor_tools_pages.media_gallery import MediaGallery


class AddKbMediaFlow:
    def __init__(self, page: Page):
        self.media_gallery_page = MediaGallery(page)

    def add_media_to_kb_article(self, file_type, file_name):
        if file_type == 'Videos':
            self.media_gallery_page.click_on_videos_filter()

        self.media_gallery_page.fill_search_modal_gallery_searchbox_input_field(file_name)
        self.media_gallery_page.select_media_file_from_list(file_name, is_modal=True)
        self.media_gallery_page.click_on_insert_media_button()
