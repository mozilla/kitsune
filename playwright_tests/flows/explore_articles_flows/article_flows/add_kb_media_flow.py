from playwright.sync_api import Page

from playwright_tests.pages.contribute.contributor_tools_pages.media_gallery import MediaGallery


class AddKbMediaFlow(MediaGallery):
    def __init__(self, page: Page):
        super().__init__(page)

    def add_media_to_kb_article(self, file_type, file_name):
        if file_type == 'Videos':
            super()._click_on_videos_filter()

        super()._fill_search_modal_gallery_searchbox_input_field(file_name)
        super()._click_on_search_modal_gallery_search_button()
        super()._select_media_file_from_list(file_name)
        super()._click_on_insert_media_button()
