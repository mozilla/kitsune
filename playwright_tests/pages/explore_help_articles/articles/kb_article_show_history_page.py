from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class KBArticleShowHistoryPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the show history section."""
        self.show_history_page_header = page.locator("h1[class='title sumo-page-subheading']")
        self.show_history_category_link = page.locator(
            "//dt[text()='Category:']/following-sibling::dd/a")
        self.show_history_revision_history_for = page.locator(
            "//dt[text()='Revision history for:']/following-sibling::dd[1]")
        self.ready_for_l10_modal_submit_button = page.locator("button#submit-l10n")
        self.l10n_modal = page.locator("div[class='mzp-c-modal-window']")
        self.revision_editor = lambda revision_id, username: page.locator(
            f"tr#{revision_id}").get_by_role("link").filter(has_text=username)
        self.revision_creator = lambda revision_id: page.locator(
            f"//tr[@id='{revision_id}']//td[@class='creator']/a"
        )
        self.ready_for_localization_button = lambda revision_id: page.locator(
            f"tr#{revision_id} td[class='l10n'] a")
        self.ready_for_localization_status = lambda revision_id: page.locator(
            f"tr#{revision_id} td[class='l10n'] a[class='yes']")
        self.revision_date = lambda revision_id: page.locator(
            f"tr#{revision_id} td[class='date'] a")
        self.revision_time = lambda revision_id: page.locator(
            f"tr#{revision_id} td[class='date'] a time")
        self.revision_status = lambda revision_id: page.locator(
            f"tr#{revision_id} td[class='status'] span")
        self.revision_current_status = lambda revision_id: page.locator(
            f"//tr[@id='{revision_id}']/td[@class='status']/span[@class='current']")
        self.revision_ready_for_l10n_status = lambda revision_id: page.locator(
            f"//tr[@id='{revision_id}']/td[@class='l10n']/a[@class='yes']")
        self.revision = lambda revision_id: page.locator(f"tr#{revision_id}")
        self.reviewable_revision = lambda revision_id: page.locator(
            f"tr#{revision_id} td[class='status'] a")
        self.delete_revision = lambda revision_id: page.locator(
            f"tr#{revision_id} td[class='delete'] a")
        self.revision_significance = lambda revision_id: page.locator(
            f"tr#{revision_id} td[class='significance']")

        """Locators belonging to the document contributors section."""
        self.show_history_page_banner = page.locator(
            "li[class='mzp-c-notification-bar mzp-t-success'] p")
        self.all_contributors_list_items = page.locator("ul[class='avatar-wrap'] li")
        self.all_contributors_usernames = page.locator("ul[class='avatar-wrap'] a span")
        self.edit_contributors_option = page.locator("section#contributors a[class='edit']")
        self.add_contributor_input_field = page.locator("input#token-input-id_users")
        self.add_contributor_button = page.locator("input[value='Add Contributor']")
        self.delete_contributor_confirmation_page_header = page.locator(
            "h1[class='title sumo-page-subheading']")
        self.delete_contributor_confirmation_page_cancel_button = page.get_by_role(
            "link", name="Cancel", exact=True)
        self.delete_contributor_confirmation_page_submit_button = page.locator(
            "input[value='Remove contributor']")
        self.new_contributor_search_button = lambda username: page.locator(
            f"//div[@class='name_search']/b[contains(text(), '{username}')]")
        self.contributor = lambda username: page.locator(f"//span[text()='{username}']/..")
        self.delete_contributor = lambda username: page.locator(
            f"//span[text()='{username}']/../..//a[@class='remove-button']")

        """Locators belonging to the delete document locators."""
        self.delete_this_document_button = page.locator("div#delete-doc a")
        self.delete_this_document_confirmation_delete_button = page.locator(
            "div[class='submit'] input")
        self.delete_this_document_confirmation_cancel_button = page.locator(
            "div[class='submit'] a")
        self.article_deleted_confirmation_message = page.locator("article#delete-document h1")
        self.article_revision_list_items = page.locator(
            "//div[@id='revision-list']//tbody/tr[contains(@id, 'rev-list')]")
        self.unable_to_delete_revision_page_header = page.locator("article#delete-revision h1")
        self.unable_to_delete_revision_page_subheader = page.locator("article#delete-revision p")
        self.unable_to_delete_revision_page_go_back_to_document_history = page.locator(
            "div[class='submit'] a")

    """Actions against the Show History page locators."""
    def get_show_history_page_banner(self) -> str:
        return self._get_text_of_element(self.show_history_page_banner)

    def get_show_history_page_title(self) -> str:
        return self._get_text_of_element(self.show_history_page_header)

    def get_show_history_category_text(self) -> str:
        return self._get_text_of_element(self.show_history_category_link)

    def click_on_show_history_category(self):
        self._click(self.show_history_category_link)

    def get_show_history_revision_for_locale_text(self) -> str:
        return self._get_text_of_element(self.show_history_revision_history_for)

    def click_on_a_particular_revision_editor(self, revision_id: str, username: str):
        self._click(self.revision_editor(revision_id, username))

    def click_on_ready_for_l10n_option(self, revision_id: str):
        self._click(self.ready_for_localization_button(revision_id))

    def click_on_submit_l10n_readiness_button(self, revision_id: str):
        """
        Click on the submit button for the ready for l10n panel.
        Args:
            revision_id (str): The revision ID. Used to check if the l10n status for that revision
            was changed or not.
        """
        self._click(self.ready_for_l10_modal_submit_button,
                    expected_locator=self.revision_ready_for_l10n_status(revision_id))

    """Actions against the delete document section locators."""
    def click_on_delete_this_document_button(self):
        self._click(self.delete_this_document_button)

    def is_delete_button_displayed(self) -> bool:
        return self._is_element_visible(self.delete_this_document_button)

    def click_on_confirmation_delete_button(self):
        self._click(self.delete_this_document_confirmation_delete_button)

    def click_on_confirmation_cancel_button(self):
        self._click(self.delete_this_document_confirmation_cancel_button)

    def get_last_revision_id(self) -> str:
        self._wait_for_locator(self.article_revision_list_items.first)
        revisions = self.article_revision_list_items.all()
        return self._get_element_attribute_value(
            revisions[0], "id"
        )

    """# For unreviewed revisions but user session doesn't permit review."""
    def click_on_a_revision_date(self, revision_id):
        self._click(self.revision_date(revision_id))

    def is_revision_displayed(self, revision_id) -> bool:
        return self._is_element_visible(self.revision(revision_id))

    def get_revision_time(self, revision_id) -> str:
        return self._get_text_of_element(self.revision_time(revision_id))

    def get_revision_status(self, revision_id) -> str:
        return self._get_text_of_element(self.revision_status(revision_id))

    def is_revision_current(self, revision_id: str) -> bool:
        """
        Return whether the given revision id is the current one or not.
        Args:
            revision_id (str): The revision id.
        """
        return self._is_element_visible(self.revision_current_status(revision_id))

    # For unreviewed revisions but user session permits review.
    """# For unreviewed revisions but user session permits review."""
    def get_status_of_reviewable_revision(self, revision_id):
        return self._get_text_of_element(self.reviewable_revision(revision_id))

    def click_on_review_revision(self, revision_id):
        self._click(self.reviewable_revision(revision_id))

    def click_on_delete_revision_button(self, revision_id):
        return self._click(self.delete_revision(revision_id))

    def get_unable_to_delete_revision_header(self) -> str:
        return self._get_text_of_element(self.unable_to_delete_revision_page_header)

    def get_unable_to_delete_revision_subheader(self) -> str:
        return self._get_text_of_element(self.unable_to_delete_revision_page_subheader)

    def click_go_back_to_document_history_option(self):
        self._click(self.unable_to_delete_revision_page_go_back_to_document_history)

    """Actions against the article contribution section locators."""
    def click_on_edit_contributors_option(self):
        self._click(self.edit_contributors_option)

    def add_a_new_contributor_inside_the_contributor_field(self, text: str):
        # Adding contributor username inside the contributor field.
        self._type(self.add_contributor_input_field, text, 100)

    def click_on_new_contributor_search_result(self, username: str):
        self._click(self.new_contributor_search_button(username))

    def click_on_add_contributor_button(self):
        self._click(self.add_contributor_button)

    def click_on_a_particular_contributor(self, username: str):
        self._click(self.contributor(username))

    def click_on_delete_button_for_a_particular_contributor(self, username: str):
        self._click(self.delete_contributor(username))

    def get_list_of_all_contributors(self) -> list[str]:
        return self._get_text_of_elements(self.all_contributors_usernames)

    def get_delete_contributor_confirmation_page_header(self) -> str:
        return self._get_text_of_element(self.delete_contributor_confirmation_page_header)

    def click_on_delete_contributor_confirmation_page_cancel_button(self):
        self._click(self.delete_contributor_confirmation_page_cancel_button)

    def click_on_delete_contributor_confirmation_page_confirm_button(self):
        self._click(self.delete_contributor_confirmation_page_submit_button)

    def get_revision_significance(self, revision_id: str) -> str:
        return self._get_text_of_element(self.revision_significance(revision_id)).strip()

    def get_revision_creator(self, revision_id: str) -> str:
        """Get the revision creator based on the revision id."""
        return self._get_text_of_element(self.revision_creator(revision_id))
