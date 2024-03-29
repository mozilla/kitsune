from playwright.sync_api import Page
from typing import Any
from playwright_tests.core.testutilities import TestUtilities
from playwright_tests.flows.explore_articles_flows.article_flows.add_kb_media_flow import \
    AddKbMediaFlow
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.pages.explore_help_articles.articles.submit_kb_article_page import (
    SubmitKBArticlePage)


class AddKbArticleFlow(TestUtilities, SubmitKBArticlePage, AddKbMediaFlow):

    def __init__(self, page: Page):
        super().__init__(page)

    def submit_simple_kb_article(self,
                                 article_title=None,
                                 article_slug=None,
                                 article_category=None,
                                 allow_discussion=True,
                                 allow_translations=True,
                                 selected_relevancy=True,
                                 selected_topics=True,
                                 search_summary=None,
                                 article_content=None,
                                 article_content_image='',
                                 submit_article=True,
                                 is_template=False,
                                 expiry_date=None,
                                 restricted_to_groups: list[str] = None,
                                 single_group=""
                                 ) -> dict[str, Any]:
        self._page.goto(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        kb_article_test_data = super().kb_article_test_data

        if restricted_to_groups is not None:
            for group in restricted_to_groups:
                super()._add_and_select_restrict_visibility_group(group)
        if single_group != "":
            super()._add_and_select_restrict_visibility_group(single_group)

        if article_title is None:
            if is_template:
                kb_article_title = (kb_article_test_data["kb_template_title"] + self.
                                    generate_random_number(0, 5000))
            else:
                kb_article_title = (kb_article_test_data["kb_article_title"] + self.
                                    generate_random_number(0, 5000))
        else:
            kb_article_title = article_title

        if kb_article_title != "":
            super()._add_text_to_article_form_title_field(
                kb_article_title
            )

        if (article_slug is not None) and (article_slug != ""):
            kb_article_slug = article_slug
            super()._add_text_to_article_slug_field(kb_article_slug)

        if article_category is None:
            if is_template:
                super()._select_category_option_by_text(
                    kb_article_test_data["kb_template_category"]
                )
            else:
                super()._select_category_option_by_text(kb_article_test_data["category_options"])
        else:
            super()._select_category_option_by_text(article_category)

        if not allow_translations:
            super()._check_allow_translations_checkbox()

        if selected_relevancy is True:
            super()._click_on_a_relevant_to_option_checkbox(
                kb_article_test_data["relevant_to_option"]
            )

        # Adding Article topic
        if selected_topics is True:
            super()._click_on_a_particular_parent_topic(
                kb_article_test_data["selected_parent_topic"]
            )
            super()._click_on_a_particular_child_topic_checkbox(
                kb_article_test_data["selected_parent_topic"],
                kb_article_test_data["selected_child_topic"],
            )

        # Interacting with Allow Discussion checkbox
        if (allow_discussion is True) and (super(

        )._is_allow_discussion_on_article_checkbox_checked() is False):
            super()._check_allow_discussion_on_article_checkbox()
        elif (allow_discussion is False) and (super(

        )._is_allow_discussion_on_article_checkbox_checked() is True):
            super()._check_allow_discussion_on_article_checkbox()

        super()._add_text_to_related_documents_field(kb_article_test_data["related_documents"])
        super()._add_text_to_keywords_field(kb_article_test_data["keywords"])

        if search_summary is None:
            super()._add_text_to_search_result_summary_field(
                kb_article_test_data["search_result_summary"]
            )

        if not super()._is_content_textarea_displayed():
            super()._click_on_toggle_syntax_highlight_option()

        if article_content is None:
            super()._add_text_to_content_textarea(kb_article_test_data["article_content"])

        if article_content_image != '':
            super()._click_on_insert_media_button()
            super().add_media_to_kb_article(
                file_type="Image",
                file_name=article_content_image
            )

        if expiry_date is not None:
            super()._add_text_to_expiry_date_field(expiry_date)

        # We need to evaluate in order to fetch the slug field value
        slug = self._page.evaluate(
            'document.getElementById("id_slug").value'
        )

        if submit_article is True:
            # If title and slug are empty we are not reaching the description field.
            if ((article_title != '') and (article_slug != '') and (
                    search_summary is None) and (article_content is None)):
                super()._click_on_submit_for_review_button()
                super()._add_text_to_changes_description_field(
                    kb_article_test_data["changes_description"]
                )
                super()._click_on_changes_submit_button()
            else:
                super()._click_on_submit_for_review_button()

        article_url = super()._get_article_page_url()

        return {"article_title": kb_article_title,
                "article_content": kb_article_test_data["article_content"],
                "article_content_html": kb_article_test_data['article_content_html_rendered'],
                "article_slug": slug,
                "article_child_topic": kb_article_test_data["selected_child_topic"],
                "article_review_description": kb_article_test_data["changes_description"],
                "keyword": kb_article_test_data["keywords"],
                "search_results_summary": kb_article_test_data["search_result_summary"],
                "expiry_date": kb_article_test_data["expiry_date"],
                "article_url": article_url
                }
