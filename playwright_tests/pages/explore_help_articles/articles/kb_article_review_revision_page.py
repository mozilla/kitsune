from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBArticleReviewRevisionPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """"General Review revision page locators."""
        self.revision_header = page.locator("h1[class='sumo-page-heading']")
        self.reviewing_revision_text = page.locator(
            "//article[@id='review-revision']//a[text()='Back to History']/..")
        self.back_to_history_link = page.locator("article#review-revision").get_by_role(
            "link", name="Back to History", exact=True)

        # For single revision on the document
        self.no_current_rev_header = page.locator(
            "//a[contains(text(),'Back to History')]/../following-sibling::p")

        # For multiple revisions on the same document
        self.unreviewed_revision_header = page.locator("div[class='unreviewed-revision']")
        self.unreviewed_revision_section = page.locator("ul[class='revision-comment'] li")
        self.review_revision_link = page.get_by_role("link").filter(has_text="Review Revision")
        self.keywords_header = page.get_by_role("heading", name="Keywords:", exact=True)
        self.keywords_content = page.locator("div#revision-keywords")
        self.search_results_summary_header = page.get_by_role(
            "heading", name="Search results summary:", exact=True)

        self.search_results_summary_content = page.locator("div#revision-summary")
        self.revision_source_header = page.get_by_role(
            "heading", name="Revision source:", exact=True)
        self.revision_source_content_locator = page.locator("div#revision-content pre")
        self.revision_rendered_html_header = page.get_by_role(
            "heading", name="Revision rendered html:", exact=True)
        self.revision_rendered_html_content = page.locator("div#doc-content p")
        self.defer_revision_button = page.locator("button#btn-reject")
        self.approve_revision_button = page.locator("button#btn-approve")

        """Locators belonging to the defer revision modal."""
        self.defer_button = page.locator("form#reject-modal button")
        self.cancel_defer = page.locator("form#reject-modal a")

        """Locators belonging to the approve revision modal."""
        self.accept_revision_modal_header = page.locator("div[class='kbox-title']")

        # Need to add locators for approving own edit revision warning.
        self.ready_for_localization_modal_checkbox = page.locator(
            "input#id_is_ready_for_localization")
        self.needs_change_modal_checkbox = page.locator("input#id_needs_change")
        self.needs_change_comment_textarea = page.locator("textarea#id_needs_change_comment")
        self.modal_accept_button = page.locator("form#approve-modal div button")
        self.modal_cancel_button = page.locator("form#approve-modal div a")

        """Locators belonging to the revision significance section."""
        self.minor_significance = page.locator("input#id_significance_0")
        self.normal_significance = page.locator("input#id_significance_1")
        self.major_significance = page.locator("input#id_significance_2")

    """Actions against the general review revision page locators."""
    def get_revision_header(self) -> str:
        return self._get_text_of_element(self.revision_header)

    def get_reviewing_revision_text(self) -> str:
        return self._get_text_of_element(self.reviewing_revision_text)

    def click_on_back_to_history_option(self):
        self._click(self.back_to_history_link)

    # For single revision on the same kb article
    def get_no_current_revision_header(self) -> str:
        return self._get_text_of_element(self.no_current_rev_header)

    # For multiple revisions on the same kb article
    def get_unreviewed_revision_text(self) -> str:
        return self._get_text_of_element(self.unreviewed_revision_header)

    def get_unreviewed_revision_section_text(self) -> str:
        return self._get_text_of_element(self.unreviewed_revision_section)

    def click_on_review_revision_option(self):
        self._click(self.review_revision_link)

    def is_keywords_header_visible(self) -> bool:
        return self._is_element_visible(self.keywords_header)

    def get_keywords_content(self) -> str:
        return self._get_text_of_element(self.keywords_content)

    def is_search_results_summary_visible(self) -> bool:
        return self._is_element_visible(self.search_results_summary_header)

    def get_search_results_summary_content(self) -> str:
        return self._get_text_of_element(self.search_results_summary_content)

    def is_revision_source_visible(self) -> bool:
        return self._is_element_visible(self.revision_source_header)

    def revision_source_content(self) -> str:
        return self._get_text_of_element(self.revision_source_content_locator)

    def is_revision_rendered_html_header_visible(self) -> bool:
        return self._is_element_visible(self.revision_rendered_html_header)

    def get_revision_rendered_html_content(self) -> str:
        return self._get_text_of_element(self.revision_rendered_html_content)

    def click_on_defer_revision_button(self):
        self._click(self.defer_revision_button)

    def click_on_defer_confirm_button(self):
        self._click(self.defer_button)

    def click_on_cancel_defer_button(self):
        self._click(self.cancel_defer)

    def click_on_approve_revision_button(self):
        self._click(self.approve_revision_button)

    """Actions against the review revision modal locators."""
    def get_accept_revision_modal_header(self) -> str:
        return self._get_text_of_element(self.accept_revision_modal_header)

    def click_accept_revision_accept_button(self):
        self._click(self.modal_accept_button)

    def check_ready_for_localization_checkbox(self):
        self._click(self.ready_for_localization_modal_checkbox)

    def is_needs_change_checkbox_checked(self) -> bool:
        return self._is_checkbox_checked(self.needs_change_modal_checkbox)

    def click_on_needs_change_checkbox(self):
        self._click(self.needs_change_modal_checkbox)

    def add_text_to_needs_change_comment(self, text: str):
        self._fill(self.needs_change_comment_textarea, text)

    def click_on_minor_significance_option(self):
        self._click(self.minor_significance)

    def click_on_normal_significance_option(self):
        self._click(self.normal_significance)

    def click_on_major_significance_option(self):
        self._click(self.major_significance)
