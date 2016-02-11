# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from pages.desktop.knowledge_base_article import KnowledgeBaseShowHistory
from pages.desktop.base import Base


class KnowledgeBaseNewArticle(Base):
    """
    'Create New Article' Page is where the form
    for creating new knowledge base article is found.
    """

    URL_TEMPLATE = '{locale}/kb/new'

    @property
    def _page_title(self):
        return self.format_page_title('Create a New Article', 'Knowledge Base')

    _article_title_box_locator = (By.ID, 'id_title')
    _article_category_menu_locator = (By.ID, 'id_category')
    _article_keywords_box_locator = (By.ID, 'id_keywords')
    _article_summary_box_locator = (By.ID, 'id_summary')
    _article_content_object = 'window.highlighting.editor'
    _article_slug_box_locator = (By.ID, 'id_slug')
    _first_article_topic_heading = (By.ID, 'ui-accordion-accordion-header-0')
    _first_article_topics_panel = (
        By.CSS_SELECTOR, '#ui-accordion-accordion-panel-0.ui-accordion-content-active')
    _article_topic_expander_locator = (By.CSS_SELECTOR, '#accordion li strong')
    _first_article_topic_locator = (
        By.CSS_SELECTOR, '#ui-accordion-accordion-panel-0 input[name=topics]')
    _article_product_locator = (By.CSS_SELECTOR, 'input[name=products]')
    _article_product_label_locator = (By.CSS_SELECTOR, 'label[for*="id_products_"]')
    _article_preview_btn_locator = (By.CSS_SELECTOR, 'div.submit > .btn-preview')
    _article_preview_content_locator = (By.CSS_SELECTOR, 'div#preview > div#doc-content')
    _article_submit_btn_locator = (By.CSS_SELECTOR, '.btn.btn-important.btn-submit')
    _comment_box_locator = (By.ID, 'id_comment')
    _comment_submit_btn_locator = (By.CSS_SELECTOR, '.kbox-wrap .btn.btn-important')

    def open(self, username, password):
        self.selenium.get(self.canonical_url)
        from pages.desktop.login_page import LoginPage
        page = LoginPage(self.base_url, self.selenium).wait_for_page_to_load()
        page.log_in(username, password)
        self.wait_for_page_to_load()
        return self

    def set_article(self, mock_article):
        """
            creates a new article
        """
        self.set_article_title(mock_article['title'])
        self.set_article_slug(mock_article['slug'])
        self.set_article_category(mock_article['category'])
        self.check_first_article_topic()
        self.check_article_product(mock_article['product'])
        self.set_article_keyword(mock_article['keyword'])
        self.set_article_summary(mock_article['summary'])
        self.set_article_content(mock_article['content'])

    def set_article_title(self, title):
        self.selenium.find_element(*self._article_title_box_locator).send_keys(title)

    def set_article_slug(self, text):
        self.selenium.find_element(*self._article_slug_box_locator).send_keys(text)

    def set_article_category(self, category):
        select_box = Select(self.selenium.find_element(*self._article_category_menu_locator))
        select_box.select_by_visible_text(category)

    def check_first_article_topic(self):
        self.wait_for_element_visible(*self._first_article_topic_heading)
        self.selenium.find_element(*self._article_topic_expander_locator).click()
        self.wait_for_element_visible(*self._first_article_topics_panel)
        WebDriverWait(self.selenium, self.timeout).until(
            lambda s: 'overflow:hidden' not in s.find_element(
                *self._first_article_topics_panel).get_attribute('style'))
        self.selenium.find_element(*self._first_article_topic_locator).click()

    def check_article_product(self, product):
        self._check_element_by_label_text(
            product, self._article_product_locator, self._article_product_label_locator)

    def _check_element_by_label_text(self, text_to_match, input_locator, label_locator):
        inputs = self.selenium.find_elements(*input_locator)
        labels = [e.text for e in self.selenium.find_elements(*label_locator)]
        for i in xrange(len(labels)):
            if labels[i].lower() == text_to_match.lower():
                inputs[i].click()
                break

    def set_article_keyword(self, keyword):
        self.selenium.find_element(*self._article_keywords_box_locator).send_keys(keyword)

    def set_article_summary(self, summary):
        self.selenium.find_element(*self._article_summary_box_locator).send_keys(summary)

    def set_article_content(self, content):
        # widget doesn't respond well to selenium commands
        self.selenium.execute_script("%s.setValue('%s')" %
                                     (self._article_content_object, content))

    def set_article_comment_box(self, comment='automated test'):
        self.selenium.find_element(*self._comment_box_locator).send_keys(comment)
        self.selenium.find_element(*self._comment_submit_btn_locator).click()
        kb_article_history = KnowledgeBaseShowHistory(self.base_url, self.selenium)
        kb_article_history.is_the_current_page
        return kb_article_history

    def submit_article(self):
        self.selenium.find_element(*self._article_submit_btn_locator).click()
        self.wait_for_element_present(*self._comment_box_locator)

    def click_article_preview_button(self):
        self.selenium.find_element(*self._article_preview_btn_locator).click()
        self.wait_for_element_present(*self._article_preview_content_locator)

    @property
    def article_preview_text(self):
        return self.selenium.find_element(*self._article_preview_content_locator).text
