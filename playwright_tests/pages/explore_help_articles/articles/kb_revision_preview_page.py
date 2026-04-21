from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBArticleRevisionsPreviewPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the 'Preview Revision' page."""
        self.preview_revision_page_header = page.locator("h1[class='sumo-page-heading']")

        """Locators belonging to the revision information section."""
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

        """Locators belonging to the revision source section."""
        self.revision_source_foldout_section = page.locator("//summary[text()='Revision Source']")
        self.revision_source_textarea = page.locator("div#doc-source textarea")

        """Locators belonging to the revision content section."""
        self.revision_content_foldout_section = page.locator(
            "//summary[text()='Revision Content']")
        self.revision_content_html_section = page.locator("div#doc-content")

    """Actions against the revision information section locators."""
    def click_on_revision_information_foldout_section(self):
        self._click(self.revision_information_foldout_section)

    def click_on_creator_link(self):
        self._click(self.creator)

    """
    This locator is available inside the page only when a review was performed.
    The text returned is the username extracted from the e-mail address.
    """
    def click_on_edit_article_based_on_this_revision_link(self):
        self._click(self.edit_article_based_on_revision_link)

    """Actions against the revision source section locators."""
    def click_on_revision_source_foldout_section(self):
        self._click(self.revision_source_foldout_section)

    """Actions against the revision content section locators."""
    def click_on_revision_content_foldout_section(self):
        self._click(self.revision_content_foldout_section)

