from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page


class MediaGallery(BasePage):
    # Media Gallery page locators.
    __upload_a_new_media_file_button = "//a[@id='btn-upload']"
    __search_gallery_searchbox = "//form[@id='gallery-search']/input"
    __search_gallery_search_button = "//form[@id='gallery-search']/button"
    # Media preview locators.
    __image_heading = "//h1[@class='sumo-page-heading']"
    __image_creator = "//ul[@id='media-meta']/li[@class='creator']/a"
    __image_description = "//div[@class='description']/p"
    __image_in_documents_text = "//div[@class='documents']/p"
    __image_in_documents_list = "//div[@class='documents']//li/a"
    __delete_this_image_button = "//form[@id='media-actions']//button"
    __edit_this_image_button = "//form[@id='media-actions']//a"
    # Insert media... modal locators.
    __insert_media_panel = "//div[@id='media-modal']"
    __search_gallery_searchbox_modal = "//form[@id='gallery-modal-search']/input"
    __search_gallery_search_button_modal = "//form[@id='gallery-modal-search']/button"
    __show_images_filter = "//div[@class='type']/ol/li[text()='Images']"
    __show_videos_filter = "//div[@class='type']/ol/li[text()='Videos']"
    __cancel_media_insert_button = "//a[@href='#cancel']"
    __upload_media_button = "//a[text()='Upload Media']"
    __insert_media_button = "//button[text()='Insert Media']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Media Gallery page actions.
    def _click_on_upload_a_new_media_file_button(self):
        super()._click(self.__upload_a_new_media_file_button)

    # Media Gallery image preview actions.
    def _get_image_heading(self) -> str:
        return super()._get_text_of_element(self.__image_heading)

    def _get_image_creator_text(self) -> str:
        return super()._get_text_of_element(self.__image_creator)

    def _click_on_image_creator_link(self):
        super()._click(self.__image_creator)

    def _get_image_description(self) -> str:
        return super()._get_text_of_element(self.__image_description)

    def _get_image_in_documents_text(self) -> str:
        return super()._get_text_of_element(self.__image_in_documents_text)

    def _get_image_in_documents_list_items_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__image_in_documents_list)

    def _click_on_a_linked_in_document(self, document_name: str):
        super()._click(f"//div[@class='documents']//li/a[text()='{document_name}']")

    def _click_on_delete_this_image_button(self):
        super()._click(self.__delete_this_image_button)

    def _click_on_edit_this_image_button(self):
        super()._click(self.__edit_this_image_button)

    # Media Gallery search
    def _fill_search_media_gallery_searchbox_input_field(self, text: str):
        super()._fill(self.__search_gallery_searchbox, text)

    def _click_on_media_gallery_searchbox_search_button(self):
        super()._click(self.__search_gallery_search_button)

    # Modal search.
    def _fill_search_modal_gallery_searchbox_input_field(self, text: str):
        super()._fill(self.__search_gallery_searchbox_modal, text)

    def _click_on_search_modal_gallery_search_button(self):
        super()._click(self.__search_gallery_search_button_modal)

    # Insert Media... kb panel actions.
    def _click_on_images_filter(self):
        super()._click(self.__show_images_filter)

    def _click_on_videos_filter(self):
        super()._click(self.__show_videos_filter)

    def _click_on_cancel_media_insert(self):
        super()._click(self.__insert_media_button)

    def _click_on_upload_media_button(self):
        super()._click(self.__upload_media_button)

    def _select_media_file_from_list(self, media_file_name: str):
        # We need to wait a bit so that the list finishes to update in case of search.
        super()._wait_for_given_timeout(1000)
        super()._click(f"//ol[@id='media-list']/li/a[@title='{media_file_name}']")

    def _click_on_insert_media_button(self):
        super()._click(self.__insert_media_button)
