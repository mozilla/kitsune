from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class KBArticleRevisionsPreviewPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Preview Revision page locators.
        self.preview_revision_page_header = page.locator("h1[class='sumo-page-heading']")

        # Revision Information locators.
        self.revision_information_foldout_section = page.locator(
            "//summary[text()='Revision Information']")
        self.revision_information_content = page.locator("div[class='revision-info']")
        self.revision_id = page.locator("//strong[text()='Revision id:']/following-sibling::span")
        self.created_date = page.locator(
            "//strong[text()='Created:']/following-sibling::span/time")
        self.creator = page.locator("//strong[text()='Creator:']/following-sibling::span/a")
        self.comment = page.locator("//strong[text()='Comment:']/following-sibling::span")
        self.reviewed = page.locator(
            "//strong[text()='Reviewed:']/following-sibling::span[not(child::time)]")
        self.reviewed_time = page.locator(
            "//strong[text()='Reviewed:']/following-sibling::span/time")
        self.reviewed_by = page.locator("//strong[text()='Reviewed by:']/following-sibling::span")
        self.is_approved = page.locator("//strong[text()='Is approved?']/following-sibling::span")
        self.is_current_revision = page.locator(
            "//strong[text()='Is current revision?']/following-sibling::span")
        self.ready_for_localization = page.locator(
            "//strong[text()='Ready for localization:']/following-sibling::span")
        self.readied_for_localization_date = page.locator(
            "//strong[text()='Readied for localization:']/following-sibling::span"
        )
        self.readied_for_localization_by = page.locator(
            "//strong[text()='Readied for localization by:']/following-sibling::span")
        self.edit_article_based_on_revision_link = page.get_by_role(
            "link", name="Edit article based on this revision", exact=True)

        # Revision Source locators.
        self.revision_source_foldout_section = page.locator("//summary[text()='Revision Source']")
        self.revision_source_textarea = page.locator("div#doc-source textarea")

        # Revision Content locators.
        self.revision_content_foldout_section = page.locator(
            "//summary[text()='Revision Content']")
        self.revision_content_html_section = page.locator("div#doc-content")

    # Preview Revision page actions.
    def get_preview_revision_header(self) -> str:
        return self._get_text_of_element(self.preview_revision_page_header)

    # Revision Information actions.
    def click_on_revision_information_foldout_section(self):
        self._click(self.revision_information_foldout_section)

    def get_revision_information_content_locator(self) -> Locator:
        return self.revision_information_content

    def get_preview_revision_id_text(self) -> str:
        return self._get_text_of_element(self.revision_id)

    def get_preview_revision_created_date_text(self) -> str:
        return self._get_text_of_element(self.created_date)

    def get_preview_revision_creator_text(self) -> str:
        return self._get_text_of_element(self.creator)

    def click_on_creator_link(self):
        self._click(self.creator)

    def get_preview_revision_comment_text(self) -> str:
        return self._get_text_of_element(self.comment)

    def get_preview_revision_reviewed_text(self) -> str:
        return self._get_text_of_element(self.reviewed)

    # This locator is available inside the page only when a review was performed.
    def get_preview_revision_reviewed_date_locator(self) -> Locator:
        return self.reviewed_time

    # This locator is available inside the page only when a review was performed.
    # The text returned is the username extracted from the e-mail address.
    def get_reviewed_by_text(self) -> str:
        return self._get_text_of_element(self.reviewed_by)

    def get_reviewed_by_locator(self) -> Locator:
        return self.reviewed_by

    def get_is_approved_text(self) -> str:
        return self._get_text_of_element(self.is_approved)

    def get_is_approved_text_locator(self) -> Locator:
        return self.is_approved

    def get_is_current_revision_text(self) -> str:
        return self._get_text_of_element(self.is_current_revision)

    def is_current_revision_locator(self) -> Locator:
        return self.is_current_revision

    def get_preview_revision_ready_for_localization_text(self) -> str:
        return self._get_text_of_element(self.ready_for_localization)

    # Is displayed only if the revision was marked as ready for localization
    def ready_for_localization_date(self) -> Locator:
        return self.readied_for_localization_date

    def readied_for_localization_by_text(self) -> str:
        return self._get_text_of_element(self.readied_for_localization_by)

    def readied_for_localization_by_locator(self) -> Locator:
        return self.readied_for_localization_by

    def get_edit_article_based_on_this_revision_link_locator(self) -> Locator:
        return self.edit_article_based_on_revision_link

    def click_on_edit_article_based_on_this_revision_link(self):
        self._click(self.edit_article_based_on_revision_link)

    # Revision Source actions.
    def click_on_revision_source_foldout_section(self):
        self._click(self.revision_source_foldout_section)

    def get_preview_revision_source_textarea_content(self) -> str:
        return self._get_element_input_value(self.revision_source_textarea)

    def get_preview_revision_source_textarea_locator(self) -> Locator:
        return self.revision_source_textarea

    # Revision Content actions.
    def click_on_revision_content_foldout_section(self):
        self._click(self.revision_content_foldout_section)

    def get_revision_content_html_locator(self) -> Locator:
        return self.revision_content_html_section
