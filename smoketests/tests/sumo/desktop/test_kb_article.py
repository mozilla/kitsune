#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittestzero import Assert
from pages.desktop.page_provider import PageProvider
from mocks.mock_article import MockArticle


class TestKnowledgeBaseArticle:

    def test_that_article_can_be_created(self, mozwebqa, variables):
        """
           Creates a new knowledge base article.
           Verifies creation.
           Deletes the article
        """
        user = variables['users']['admin']
        kb_new_article = PageProvider(mozwebqa).new_kb_article_page(
            user['username'], user['password'])

        # create a new article
        mock_article = MockArticle()
        kb_new_article.set_article(mock_article)
        kb_new_article.submit_article()
        kb_article_history = kb_new_article.set_article_comment_box(mock_article['comment'])

        # verify article contents
        kb_edit_article = kb_article_history.navigation.click_edit_article()

        actual_summary_text = str(kb_edit_article.article_summary_text)
        Assert.equal(mock_article['summary'], actual_summary_text)

        actual_contents_text = str(kb_edit_article.article_contents_text)
        Assert.equal(mock_article['content'], actual_contents_text)

        # delete the same article
        kb_article = kb_edit_article.navigation.click_show_history()
        kb_article.delete_entire_article_document()

    def test_that_article_can_be_edited(self, mozwebqa, variables):
        """
           Creates a new knowledge base article.
           Verifies creation.
           Edits the article, verifies the edition.
           Deletes the article
        """
        user = variables['users']['admin']
        kb_new_article = PageProvider(mozwebqa).new_kb_article_page(
            user['username'], user['password'])

        # create a new article
        mock_article = MockArticle()
        kb_new_article.set_article(mock_article)
        kb_new_article.submit_article()
        kb_article_history = kb_new_article.set_article_comment_box(mock_article['comment'])

        # edit that same article (keep the title the same as original)
        mock_article_edited = MockArticle(suffix="_edited", title=mock_article['title'])

        kb_edit_article = kb_article_history.navigation.click_edit_article()
        kb_article_history = kb_edit_article.edit_article(mock_article_edited)

        kb_edit_article = kb_article_history.navigation.click_edit_article()

        # verify the contents of the edited article
        actual_page_title = kb_edit_article.page_title
        Assert.contains(mock_article_edited['title'], actual_page_title)

        actual_summary_text = kb_edit_article.article_summary_text
        Assert.equal(mock_article_edited['summary'], actual_summary_text)

        actual_content_text = kb_edit_article.article_contents_text
        Assert.equal(mock_article_edited['content'], actual_content_text)

        # delete the same article
        kb_article_history = kb_edit_article.navigation.click_show_history()
        kb_article_history.delete_entire_article_document()

    def test_that_article_can_be_deleted(self, mozwebqa, variables):
        """
           Creates a new knowledge base article.
           Deletes the article.
           Verifies the deletion.
        """
        user = variables['users']['admin']
        kb_new_article = PageProvider(mozwebqa).new_kb_article_page(
            user['username'], user['password'])

        # create a new article
        mock_article = MockArticle()
        kb_new_article.set_article(mock_article)
        kb_new_article.submit_article()
        kb_article_history = kb_new_article.set_article_comment_box(mock_article['comment'])

        # go to article and get URL
        kb_article = kb_article_history.navigation.click_article()
        article_url = kb_article.url_current_page

        # delete the same article
        kb_article_history = kb_article.navigation.click_show_history()
        kb_article_history.delete_entire_article_document()

        kb_article_history.selenium.get(article_url)
        actual_page_title = kb_article_history.page_title
        Assert.contains("Page Not Found", actual_page_title)

    def test_that_article_can_be_previewed_before_submitting(self, mozwebqa, variables):
        """
            Start a new knowledge base article.
            Preview.
            Verify the contents in the preview
        """
        user = variables['users']['default']
        kb_new_article = PageProvider(mozwebqa).new_kb_article_page(
            user['username'], user['password'])

        # create a new article
        mock_article = MockArticle()
        kb_new_article.set_article(mock_article)

        kb_new_article.click_article_preview_button()
        actual_preview_text = kb_new_article.article_preview_text

        Assert.equal(mock_article['content'], actual_preview_text)

        # Does not need to be deleted as it does not commit the article

    def test_that_article_can_be_translated(self, mozwebqa, variables):
        """
           Creates a new knowledge base article.
           Translate article
        """
        user = variables['users']['admin']
        kb_new_article = PageProvider(mozwebqa).new_kb_article_page(
            user['username'], user['password'])

        # create a new article
        mock_article = MockArticle()
        kb_new_article.set_article(mock_article)
        kb_new_article.submit_article()
        kb_article_history = kb_new_article.set_article_comment_box(mock_article['comment'])

        # translating
        kb_translate_pg = kb_article_history.navigation.click_translate_article()
        kb_translate_pg.click_translate_language('Deutsch (de)')

        # enter the translation
        mock_article_deutsch = MockArticle(suffix="_deutsch")
        kb_translate_pg.type_title(mock_article_deutsch['title'])
        kb_translate_pg.type_slug(mock_article_deutsch['slug'])
        kb_translate_pg.type_search_result_summary(mock_article_deutsch['summary'])
        kb_translate_pg.click_submit_review()

        change_comment = mock_article_deutsch['comment']
        kb_translate_pg.type_modal_describe_changes(change_comment)
        kb_article_history = kb_translate_pg.click_modal_submit_changes_button()

        # verifying
        Assert.equal(change_comment, kb_article_history.most_recent_revision_comment)
        Assert.contains('Deutsch', kb_article_history.revision_history)

        # deleting
        kb_article_history.delete_entire_article_document()
