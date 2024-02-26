from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class KBArticleRevisionsPreviewPage(BasePage):
    # Preview Revision page locators.
    __preview_revision_page_header = "//h1[@class='sumo-page-heading']"
    # Revision Information locators.
    __revision_information_foldout_section = "//summary[text()='Revision Information']"
    __revision_information_content = "//div[@class='revision-info']"
    __revision_id = "//strong[text()='Revision id:']/following-sibling::span"
    __created_date = "//strong[text()='Created:']/following-sibling::span/time"
    __creator = "//strong[text()='Creator:']/following-sibling::span/a"
    __comment = "//strong[text()='Comment:']/following-sibling::span"
    __reviewed = "//strong[text()='Reviewed:']/following-sibling::span[not(child::time)]"
    __reviewed_time = "//strong[text()='Reviewed:']/following-sibling::span/time"
    __reviewed_by = "//strong[text()='Reviewed by:']/following-sibling::span"
    __is_approved = "//strong[text()='Is approved?']/following-sibling::span"
    __is_current_revision = "//strong[text()='Is current revision?']/following-sibling::span"
    __ready_for_localization = "//strong[text()='Ready for localization:']/following-sibling::span"
    __readied_for_localization_date = ("//strong[text()='Readied for "
                                       "localization:']/following-sibling::span")
    __readied_for_localization_by = ("//strong[text()='Readied for localization "
                                     "by:']/following-sibling::span")
    __edit_article_based_on_revision_link = "//a[text()='Edit article based on this revision']"
    # Revision Source locators.
    __revision_source_foldout_section = "//summary[text()='Revision Source']"
    __revision_source_textarea = "//div[@id='doc-source']/textarea"
    # Revision Content locators.
    __revision_content_foldout_section = "//summary[text()='Revision Content']"
    __revision_content_html_section = "//div[@id='doc-content']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Preview Revision page actions.
    def _get_preview_revision_header(self) -> str:
        return super()._get_text_of_element(self.__preview_revision_page_header)

    # Revision Information actions.
    def _click_on_revision_information_foldout_section(self):
        super()._click(self.__revision_information_foldout_section)

    def _get_revision_information_content_locator(self) -> Locator:
        return super()._get_element_locator(self.__revision_information_content)

    def _get_preview_revision_id_text(self) -> str:
        return super()._get_text_of_element(self.__revision_id)

    def _get_preview_revision_created_date_text(self) -> str:
        return super()._get_text_of_element(self.__created_date)

    def _get_preview_revision_creator_text(self) -> str:
        return super()._get_text_of_element(self.__creator)

    def _click_on_creator_link(self):
        super()._click(self.__creator)

    def _get_preview_revision_comment_text(self) -> str:
        return super()._get_text_of_element(self.__comment)

    def _get_preview_revision_reviewed_text(self) -> str:
        return super()._get_text_of_element(self.__reviewed)

    # This locator is available inside the page only when a review was performed.
    def _get_preview_revision_reviewed_date_locator(self) -> Locator:
        return super()._get_element_locator(self.__reviewed_time)

    # This locator is available inside the page only when a review was performed.
    # The text returned is the username extracted from the e-mail address.
    def _get_reviewed_by_text(self) -> str:
        return super()._get_text_of_element(self.__reviewed_by)

    def _get_reviewed_by_locator(self) -> Locator:
        return super()._get_element_locator(self.__reviewed_by)

    def _get_is_approved_text(self) -> str:
        return super()._get_text_of_element(self.__is_approved)

    def _get_is_approved_text_locator(self) -> Locator:
        return super()._get_element_locator(self.__is_approved)

    def _get_is_current_revision_text(self) -> str:
        return super()._get_text_of_element(self.__is_current_revision)

    def _is_current_revision_locator(self) -> Locator:
        return super()._get_element_locator(self.__is_current_revision)

    def _get_preview_revision_ready_for_localization_text(self) -> str:
        return super()._get_text_of_element(self.__ready_for_localization)

    # Is displayed only if the revision was marked as ready for localization
    def _ready_for_localization_date(self) -> Locator:
        return super()._get_element_locator(self.__readied_for_localization_date)

    def _readied_for_localization_by_text(self) -> str:
        return super()._get_text_of_element(self.__readied_for_localization_by)

    def _readied_for_localization_by_locator(self) -> Locator:
        return super()._get_element_locator(self.__readied_for_localization_by)

    def _get_edit_article_based_on_this_revision_link_locator(self) -> Locator:
        return super()._get_element_locator(self.__edit_article_based_on_revision_link)

    def _click_on_edit_article_based_on_this_revision_link(self):
        super()._click(self.__edit_article_based_on_revision_link)

    # Revision Source actions.
    def _click_on_revision_source_foldout_section(self):
        super()._click(self.__revision_source_foldout_section)

    def _get_preview_revision_source_textarea_content(self) -> str:
        return super()._get_element_input_value(self.__revision_source_textarea)

    def _get_preview_revision_source_textarea_locator(self) -> Locator:
        return super()._get_element_locator(self.__revision_source_textarea)

    # Revision Content actions.
    def _click_on_revision_content_foldout_section(self):
        super()._click(self.__revision_content_foldout_section)

    def _get_revision_content_html_locator(self) -> Locator:
        return super()._get_element_locator(self.__revision_content_html_section)
