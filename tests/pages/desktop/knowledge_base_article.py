# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from pages.desktop.base import Base
from pages.page import Page
from selenium.webdriver.support.ui import WebDriverWait


class KnowledgeBase(Base):

    @property
    def navigation(self):
        return self.Navigation(self.base_url, self.selenium)

    @property
    def is_the_current_page(self):
        if self._page_title:
            page_title = self.page_title
            assert self._page_title in page_title

    class Navigation(Page):

        _article_locator = (By.XPATH, './/*[@id="doc-tools"]/ul/li[1]/ul/li[1]/a')
        _edit_article_locator = (By.XPATH, './/*[@id="doc-tools"]/ul/li[1]/ul/li[3]/a')
        _translate_article_locator = (By.XPATH, './/*[@id="doc-tools"]/ul/li[1]/ul/li[4]/a')
        _show_history_locator = (By.CSS_SELECTOR, '.sidebar-nav li a[href$="/history"]')
        _show_editing_tools_locator = (
            By.CSS_SELECTOR, '.sidebar-nav.sidebar-folding > li:first-child span')

        def show_editing_tools(self):
            if not self.is_element_visible(*self._edit_article_locator):
                self.selenium.find_element(*self._show_editing_tools_locator).click()
                self.wait_for_element_visible(*self._edit_article_locator)

        def click_article(self):
            self.show_editing_tools()
            self.selenium.find_element(*self._article_locator).click()
            return KnowledgeBaseArticle(self.base_url, self.selenium)

        def click_edit_article(self):
            self.selenium.find_element(*self._edit_article_locator).click()
            return KnowledgeBaseEditArticle(self.base_url, self.selenium)

        def click_translate_article(self):
            self.show_editing_tools()
            self.selenium.find_element(*self._translate_article_locator).click()
            return KnowledgeBaseTranslate(self.base_url, self.selenium)

        def click_show_history(self):
            self.show_editing_tools()
            self.selenium.find_element(*self._show_history_locator).click()
            return KnowledgeBaseShowHistory(self.base_url, self.selenium)


class KnowledgeBaseArticle(KnowledgeBase):

    _page_title = ' | How to | Mozilla Support'
    _title_locator = (By.CSS_SELECTOR, 'h1.title')

    @property
    def article_title(self):
        self.selenium.find_element(*self._title_locator).click()


class KnowledgeBaseEditArticle(KnowledgeBase):

    _page_title = 'Edit Article | '
    _description_form_toggle_locator = (By.CSS_SELECTOR, '#document-form summary')
    _description_form_save_locator = (By.CSS_SELECTOR, '#document-form button[type="submit"]')
    _article_keywords_box_locator = (By.ID, 'id_keywords')
    _article_summary_box_locator = (By.ID, 'id_summary')
    _article_content_object = 'window.highlighting.editor'
    _article_topic_expander_locator = (By.CSS_SELECTOR, '#accordion li strong')
    _article_topic_locator = (By.CSS_SELECTOR, 'input[name=topics]')
    _article_product_locator = (By.CSS_SELECTOR, 'input[name=products]')
    _article_submit_btn_locator = (By.CSS_SELECTOR, '.btn-submit')
    _comment_box_locator = (By.ID, 'id_comment')
    _comment_submit_btn_locator = (By.CSS_SELECTOR, '.kbox-wrap button[type="submit"]')

    @property
    def article_summary_text(self):
        return self.selenium.find_element(*self._article_summary_box_locator).text

    @property
    def article_contents_text(self):
        # widget doesn't respond well to selenium commands
        return self.selenium.execute_script("return %s.getValue()" %
                                            self._article_content_object)

    def edit_article(self, mock_article):
        """
            Edits an existing article.
        """
        # Edit the Description form
        self.open_description_form()
        # select a different topic & product than as selected for a new article
        self.check_article_topic(2)
        self.check_article_product(2)
        self.save_description_form()
        # Edit Content form
        self.set_article_keyword(mock_article['keyword'])
        self.set_article_summary(mock_article['summary'])
        self.set_article_content(mock_article['content'])
        self.submit_article()
        return self.set_article_comment_box()

    def set_article_keyword(self, keyword):
        element = self.selenium.find_element(*self._article_keywords_box_locator)
        element.clear()
        element.send_keys(keyword)

    def set_article_summary(self, summary):
        element = self.selenium.find_element(*self._article_summary_box_locator)
        element.clear()
        element.send_keys(summary)

    def set_article_content(self, content):
        # widget doesn't respond well to selenium commands
        self.selenium.execute_script("%s.setValue('%s')" %
                                     (self._article_content_object, content))

    def open_description_form(self):
        if not self.is_element_visible(*self._article_topic_locator):
            self.selenium.find_element(*self._description_form_toggle_locator).click()
            self.wait_for_element_visible(*self._article_topic_expander_locator)

    def save_description_form(self):
        self.selenium.find_element(*self._description_form_save_locator).click()

    def check_article_topic(self, index):
        index = index - 1
        self.selenium.find_element(*self._article_topic_expander_locator).click()
        self.wait_for_element_visible(*self._article_topic_locator)
        self.selenium.find_elements(*self._article_topic_locator)[index].click()

    def check_article_product(self, index):
        index = index - 1
        self.selenium.find_elements(*self._article_product_locator)[index].click()

    def set_article_comment_box(self, comment='default comment'):
        self.selenium.find_element(*self._comment_box_locator).send_keys(comment)
        self.selenium.find_element(*self._comment_submit_btn_locator).click()
        kb_article_history = KnowledgeBaseShowHistory(self.base_url, self.selenium)
        kb_article_history.is_the_current_page
        return kb_article_history

    def submit_article(self):
        self.selenium.find_element(*self._article_submit_btn_locator).click()
        self.wait_for_element_present(*self._comment_box_locator)


class KnowledgeBaseTranslate(KnowledgeBase):

    _page_title = 'Select language | '
    _description_title_locator = (By.ID, 'id_title')
    _description_slug_locator = (By.ID, 'id_slug')
    _search_result_summary_locator = (By.ID, 'id_summary')
    _submit_button_locator = (
        By.CSS_SELECTOR, '.buttons-and-preview > div.submit:first-of-type .btn-important')

    # 2 elements inside the modal popup
    _describe_changes_locator = (By.ID, 'id_comment')
    _submit_changes_button_locator = (By.CSS_SELECTOR, '#submit-modal > button')

    def click_translate_language(self, language):
        self.selenium.find_element(By.LINK_TEXT, language).click()
        self.header.dismiss_staging_site_warning_if_present()

    @property
    def is_type_title_visible(self):
        return self.is_element_visible(*self._description_title_locator)

    def type_title(self, text):
        self.selenium.find_element(*self._description_title_locator).send_keys(text)

    def type_slug(self, text):
        self.selenium.find_element(*self._description_slug_locator).send_keys(text)

    def type_search_result_summary(self, text):
        self.selenium.find_element(*self._search_result_summary_locator).send_keys(text)

    def click_submit_review(self):
        self.selenium.find_element(*self._submit_button_locator).click()

    def type_modal_describe_changes(self, text):
        self.selenium.find_element(*self._describe_changes_locator).send_keys(text)

    def click_modal_submit_changes_button(self):
        self.selenium.find_element(*self._submit_changes_button_locator).click()
        return KnowledgeBaseShowHistory(self.base_url, self.selenium)


class KnowledgeBaseShowHistory(KnowledgeBase):

    _page_title = 'Revision History | '

    _delete_document_link_locator = (By.CSS_SELECTOR, 'div#delete-doc > a[href*="delete"]')
    _delete_confirmation_btn_locator = (By.CSS_SELECTOR, '#delete-document input[type=submit]')

    _revision_history_language_locator = (By.CSS_SELECTOR, '#revision-history > div:nth-child(5)')

    # history of the test
    _top_revision_comment = (By.CSS_SELECTOR, '#revision-list li:nth-child(2) > div.comment')

    def delete_entire_article_document(self):
        self.click_delete_entire_article_document()
        self.click_delete_confirmation_button()
        WebDriverWait(self.selenium, self.timeout).until(
            lambda s: not self.is_element_present(*self._delete_confirmation_btn_locator))

    def click_delete_entire_article_document(self):
        self.selenium.find_element(*self._delete_document_link_locator).click()

    def click_delete_confirmation_button(self):
        self.selenium.find_element(*self._delete_confirmation_btn_locator).click()

    @property
    def most_recent_revision_comment(self):
        self.wait_for_element_visible(*self._top_revision_comment)
        return self.selenium.find_element(*self._top_revision_comment).text

    @property
    def revision_history(self):
        return self.selenium.find_element(*self._revision_history_language_locator).text
