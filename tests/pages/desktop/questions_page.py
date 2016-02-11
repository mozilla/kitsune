# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from pages.page import Page
from pages.desktop.base import Base


class QuestionsPage(Base):
    """
    'Ask a Question' landing page.
    """

    URL_TEMPLATE = '{locale}/questions'

    _page_title = 'Support Forum | Mozilla Support'

    _ask_question_link_locator = '/en-US/questions/new'

    _all_products_locator = (By.CSS_SELECTOR, '.product a[href$="/all"]')
    _questions_done_tab_locator = (By.CSS_SELECTOR, '#owner-tabs > a[href*="done"]')
    _all_questions_tab_locator = (By.CSS_SELECTOR, '#owner-tabs > a[href*="show=all"]')
    _sort_solved_link_locator = (By.CSS_SELECTOR, 'a[href*="filter=solved"]')
    _sort_unanswered_locator = (
        By.CSS_SELECTOR, '.questions-sidebar ul > li > a[href*="unanswered"]')
    _questions_list_block_locator = (By.CSS_SELECTOR, '.questions > section[id*="question"]')
    _questions_list_locator = (By.CSS_SELECTOR, 'article.questions > section[class="cf"]')

    def click_ask_new_questions_link(self):
        self.selenium.find_element(*self._ask_question_link_locator).click()
        return AskNewQuestionsPage(self.base_url, self.selenium)

    def go_to_thread(self, url):
        self.open(url)

    def click_any_question(self, question_number):
        return self.questions[question_number - 1].click_question_link()

    def click_questions_done_tab(self):
        self.selenium.find_element(*self._questions_done_tab_locator).click()

    def click_all_questions_tab(self):
        self.selenium.find_element(*self._all_questions_tab_locator).click()

    def click_sort_by_unanswered_questions(self):
        # Prevent Selenium automatically scrolling this element to the top of
        # the page, which can lead to unintented  clicks on the banner
        element = self.selenium.find_element(*self._sort_unanswered_locator)
        self.selenium.execute_script('arguments[0].scrollIntoView(false);', element)
        element.click()

    def click_sort_by_solved_questions(self):
        # Prevent Selenium automatically scrolling this element to the top of
        # the page, which can lead to unintented  clicks on the banner
        element = self.selenium.find_element(*self._sort_solved_link_locator)
        self.selenium.execute_script('arguments[0].scrollIntoView(false);', element)
        element.click()

    def click_all_products(self):
        self.selenium.find_element(*self._all_products_locator).click()

    @property
    def are_questions_present(self):
        return self.is_element_present(*self._questions_list_block_locator)

    @property
    def questions_count(self):
        return len(self.selenium.find_elements(*self._questions_list_locator))

    @property
    def questions(self):
        return [self.Question(self.base_url, self.selenium, el) for el in
                self.selenium.find_elements(*self._questions_list_locator)]

    class Question(Page):

        _solved_question_locator = (By.CSS_SELECTOR, '.thread-solved')
        _replies_number_locator = (By.CSS_SELECTOR, 'div.replies > h4')
        _question_link_locator = (By.CSS_SELECTOR, 'a')
        _product_name_locator = (By.CSS_SELECTOR, '.content ul.tag-list li:nth-child(1)')

        def __init__(self, base_url, selenium, element):
            Page.__init__(self, base_url, selenium)
            self._root_element = element

        @property
        def solved_questions_filter(self):
            return self._root_element.find_element(
                *self._solved_question_locator).get_attribute('class')

        @property
        def number_of_replies(self):
            return int(self._root_element.find_element(*self._replies_number_locator).text)

        @property
        def product_name(self):
            return self._root_element.find_element(*self._product_name_locator).text

        def click_question_link(self):
            question_title = self.title
            product_name = self.product_name
            # Prevent Selenium automatically scrolling this element to the top
            # of the page, which can lead to unintented  clicks on the banner
            element = self._root_element.find_element(*self._question_link_locator)
            self.selenium.execute_script('arguments[0].scrollIntoView(false);', element)
            element.click()
            view_question_pg = ViewQuestionPage(self.base_url, self.selenium)
            view_question_pg.is_the_current_page(question_title, product_name)
            return view_question_pg

        @property
        def title(self):
            return self._root_element.find_element(*self._question_link_locator).text


class AskNewQuestionsPage(Base):
    """
    'Ask a New Question' page.
    Child class of Questions Page
    """

    URL_TEMPLATE = '{locale}/questions/new'

    _page_title = 'Ask a Question | Mozilla Support'
    _firefox_product_first_link_locator = (
        By.CSS_SELECTOR, '#product-picker li:nth-child(1) > a.cf > span.title')
    _category_prob_first_link_locator = (By.CSS_SELECTOR, 'ul.select-one > li > a')
    _type_question_box_locator = (By.NAME, 'search')
    _ask_this_button_locator = (By.CSS_SELECTOR, '#ask-search-form .btn.btn-important')
    _none_of_these_button_locator = (By.CSS_SELECTOR, 'form .btn.btn-submit')
    _q_content_box_locator = (By.ID, 'id_content')
    _q_trouble_link_locator = (By.CSS_SELECTOR, '#troubleshooting-manual a')
    _q_post_button_locator = (By.CSS_SELECTOR, '#question-form button.btn-submit')
    _close_stage_banner_locator = (By.CLASS_NAME, 'close-button')
    _selected_product_locator = (By.CSS_SELECTOR, '#selected-product span')

    def click_firefox_product_link(self):
        self.selenium.find_element(*self._firefox_product_first_link_locator).click()

    def click_category_problem_link(self):
        self.selenium.find_element(*self._category_prob_first_link_locator).click()

    def type_question(self, question_to_ask):
        self.selenium.find_element(*self._type_question_box_locator).send_keys(question_to_ask)
        self.selenium.find_element(*self._ask_this_button_locator).click()

    def click_none_of_these_solve_my_problem_button(self):
        self.selenium.find_element(*self._none_of_these_button_locator).click()

    @property
    def selected_product(self):
        return self.selenium.find_element(*self._selected_product_locator).text

    def fill_up_questions_form(self, question_to_ask, q_text='details', q_site='www.example.com'):
        self.header.dismiss_staging_site_warning_if_present()
        self.selenium.find_element(*self._q_content_box_locator).send_keys(q_text)
        self.header.dismiss_staging_site_warning_if_present()
        self.selenium.find_element(*self._q_trouble_link_locator).click()
        selected_product = self.selected_product == "Firefox for Desktop" and \
            "Firefox" or self.selected_product
        self.header.dismiss_staging_site_warning_if_present()
        self.selenium.find_element(*self._q_post_button_locator).click()
        WebDriverWait(self.selenium, self.timeout).until(
            lambda s: not self.is_element_present(*self._q_post_button_locator))
        view_question_pg = ViewQuestionPage(self.base_url, self.selenium)
        view_question_pg.is_the_current_page(question_to_ask, selected_product)
        return view_question_pg

    def close_stage_site_banner(self):
        self.selenium.find_element(*self._close_stage_banner_locator).click()


class ViewQuestionPage(Base):

    _question_locator = (By.CSS_SELECTOR, 'h2.summary')
    _detail_locator = (By.CSS_SELECTOR, 'div.main-content p')
    _problem_too_button_locator = (By.CSS_SELECTOR, 'div.me-too > form > button.btn')
    _problem_count_text_locator = (By.CSS_SELECTOR, 'div.question-meta > ul.cf > li:nth-child(2)')
    _no_thanks_link_locator = (By.LINK_TEXT, 'No Thanks')
    _thread_content_box_locator = (By.ID, 'id_content')
    _reply_button_locator = (By.CSS_SELECTOR, "button[class='btn btn-submit big']")
    _answers_locator = (By.CSS_SELECTOR, '.answer.grid_9')
    _post_author_locator = (By.CSS_SELECTOR, '.asked-by > a')
    _post_content_locator = (By.CSS_SELECTOR, 'div > p')
    _page_title = ' Support Forum | Mozilla Support'

    def is_the_current_page(self, question_name, product_name):
        if self._page_title:
            expected_title = question_name + ' | ' + product_name + self._page_title
            WebDriverWait(self.selenium, self.timeout).until(
                lambda s: self.page_title == expected_title)

    @property
    def question(self):
        return self.selenium.find_element(*self._question_locator).text

    @property
    def question_detail(self):
        return self.selenium.find_element(*self._detail_locator).text

    def click_problem_too_button(self):
        # Prevent Selenium automatically scrolling this element to the top of
        # the page, which can lead to unintented  clicks on the banner
        element = self.selenium.find_element(*self._problem_too_button_locator)
        self.selenium.execute_script('arguments[0].scrollIntoView(false);', element)
        element.click()
        self.wait_for_element_present(*self._no_thanks_link_locator)

    @property
    def problem_count(self):
        count_text = self.selenium.find_element(*self._problem_count_text_locator).text
        count_text = count_text.split()
        return int(count_text[0])

    def post_reply(self, reply_text):
        self.selenium.find_element(*self._thread_content_box_locator).send_keys(reply_text)
        self.selenium.find_element(*self._reply_button_locator).click()

    def is_reply_text_present(self, username, reply_text):
        is_reply_present = False
        # get a list of answers
        answers = reversed(self.selenium.find_elements(*self._answers_locator))
        # check if there exists a reply the user replied as "reply"
        for answer in answers:
            # name of the person who authored a post (name of a replyer)
            post_author_name = answer.find_element(*self._post_author_locator).text.lower()
            # content of the post
            post_content = answer.find_element(*self._post_content_locator).text
            # there should exist a post, whose content is "reply" and
            # the author is the person who logged in with username
            if username.lower() == post_author_name and post_content == reply_text:
                is_reply_present = True
                break
        return is_reply_present
