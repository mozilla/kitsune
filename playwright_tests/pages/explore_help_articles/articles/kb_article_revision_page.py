from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class KBArticleRevisionPage(BasePage):
    __revision_header = "//h1[@class='sumo-page-heading']"
    __reviewing_revision_text = "//article[@id='review-revision']//a[text()='Back to History']/.."
    __back_to_history_link = "//article[@id='review-revision']//a[text()='Back to History']"

    # For single revision on the document
    __no_current_rev_header = "//a[contains(text(),'Back to History')]/../following-sibling::p"

    # For multiple revisions on the same document
    __unreviewed_revision_header = "//div[@class='unreviewed-revision']"
    __unreviewed_revision_section = "//ul[@class='revision-comment']/li"
    __review_revision_link = "//a[contains(text(),'Review Revision')]"

    __keywords_header = "//h3[text()='Keywords:']"
    __keywords_content = "//div[@id='revision-keywords']"
    __search_results_summary_header = "//h3[text()='Search results summary:']"
    __search_results_summary_content = "//div[@id='revision-summary']"

    __revision_source_header = "//h3[text()='Revision source:']"
    __revision_source_content = "//div[@id='revision-content']/pre"

    __revision_rendered_html_header = "//h3[text()='Revision rendered html:']"
    __revision_rendered_html_content = "//div[@id='doc-content']/p"

    __approve_revision_button = "//button[@id='btn-approve']"

    # Approve revision modal
    __accept_revision_modal_header = "//div[@class='kbox-title']"

    # Need to add locators for approving own edit revision warning.
    __ready_for_localization_modal_checkbox = "//input[@id='id_is_ready_for_localization']"
    __needs_change_modal_checkbox = "//input[@id='id_needs_change']"
    __modal_accept_button = "//button[text()='Accept']"
    __modal_cancel_button = "//form[@id='approve-modal']//a[text()='Cancel']"

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_revision_header(self) -> str:
        return super()._get_text_of_element(self.__revision_header)

    def _get_reviewing_revision_text(self) -> str:
        return super()._get_text_of_element(self.__reviewing_revision_text)

    def _click_on_back_to_history_option(self):
        super()._click(self.__back_to_history_link)

    # For single revision on the same kb article
    def _get_no_current_revision_header(self) -> str:
        return super()._get_text_of_element(self.__no_current_rev_header)

    # For multiple revisions on the same kb article
    def _get_unreviewed_revision_text(self) -> str:
        return super()._get_text_of_element(self.__unreviewed_revision_header)

    def _get_unreviewed_revision_section_text(self) -> str:
        return super()._get_text_of_element(self.__unreviewed_revision_section)

    def _click_on_review_revision_option(self):
        super()._click(self.__review_revision_link)

    def _is_keywords_header_visible(self) -> bool:
        return super()._is_element_visible(self.__keywords_header)

    def _get_keywords_content(self) -> str:
        return super()._get_text_of_element(self.__keywords_content)

    def _is_search_results_summary_visible(self) -> bool:
        return super()._is_element_visible(self.__search_results_summary_header)

    def _get_search_results_summary_content(self) -> str:
        return super()._get_text_of_element(self.__search_results_summary_content)

    def _is_revision_source_visible(self) -> bool:
        return super()._is_element_visible(self.__revision_source_header)

    def _revision_source_content(self) -> str:
        return super()._get_text_of_element(self.__revision_source_content)

    def _is_revision_rendered_html_header_visible(self) -> bool:
        return super()._is_element_visible(self.__revision_rendered_html_header)

    def _get_revision_rendered_html_content(self) -> str:
        return super()._get_text_of_element(self.__revision_rendered_html_content)

    def _click_on_approve_revision_button(self):
        super()._click(self.__approve_revision_button)

    # Modal actions
    def _get_accept_revision_modal_header(self) -> str:
        return super()._get_text_of_element(self.__accept_revision_modal_header)

    def _click_accept_revision_accept_button(self):
        super()._click(self.__modal_accept_button)
