from playwright.sync_api import Page
from typing import Any

from slugify import slugify

from playwright_tests.core.utilities import Utilities
from playwright_tests.flows.explore_articles_flows.article_flows.add_kb_media_flow import \
    AddKbMediaFlow
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_article_review_revision_page import \
    KBArticleReviewRevisionPage
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import \
    KBArticleShowHistoryPage
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_page import \
    EditKBArticlePage
from playwright_tests.pages.explore_help_articles.articles.submit_kb_article_page import (
    SubmitKBArticlePage)


class AddKbArticleFlow:

    def __init__(self, page: Page):
        self.page = page
        self.utilities = Utilities(page)
        self.submit_kb_article_page = SubmitKBArticlePage(page)
        self.add_media_flow = AddKbMediaFlow(page)
        self.kb_article_page = KBArticlePage(page)
        self.kb_article_show_history_page = KBArticleShowHistoryPage(page)
        self.kb_article_review_revision_page = KBArticleReviewRevisionPage(page)
        self.edit_kb_article_page = EditKBArticlePage(page)

    def submit_simple_kb_article(self, **kwargs):
        return self.utilities.re_call_function_on_error(
            lambda: self._submit_simple_kb_article(**kwargs)
        )

    def _submit_simple_kb_article(self,
                                  article_title=None,
                                  article_slug=None,
                                  article_category=None,
                                  article_keyword=None,
                                  allow_discussion=True,
                                  allow_translations=True,
                                  selected_product=True,
                                  selected_topics=True,
                                  search_summary=None,
                                  article_content=None,
                                  article_content_image='',
                                  submit_article=True,
                                  is_template=False,
                                  expiry_date=None,
                                  restricted_to_groups: list[str] = None,
                                  single_group="",
                                  approve_first_revision=False,
                                  ready_for_localization=False
                                  ) -> dict[str, Any]:
        self.utilities.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)

        kb_article_test_data = self.utilities.kb_article_test_data

        if restricted_to_groups is not None:
            for group in restricted_to_groups:
                self.submit_kb_article_page.add_and_select_restrict_visibility_group(group)
        if single_group != "":
            self.submit_kb_article_page.add_and_select_restrict_visibility_group(single_group)

        if article_title is None:
            if is_template:
                kb_article_title = (kb_article_test_data["kb_template_title"] + self.utilities.
                                    generate_random_number(0, 5000))
            else:
                kb_article_title = (kb_article_test_data["kb_article_title"] + self.utilities.
                                    generate_random_number(0, 5000))
        else:
            kb_article_title = article_title

        if kb_article_title != "":
            self.submit_kb_article_page.add_text_to_article_form_title_field(
                kb_article_title
            )

        if (article_slug is not None) and (article_slug != ""):
            kb_article_slug = article_slug
            self.submit_kb_article_page.add_text_to_article_slug_field(kb_article_slug)

        if article_category is None:
            if is_template:
                article_category = kb_article_test_data["kb_template_category"]
                self.submit_kb_article_page.select_category_option_by_text(
                    article_category
                )
            else:
                article_category = kb_article_test_data["category_options"]
                self.submit_kb_article_page.select_category_option_by_text(article_category)
        else:
            self.submit_kb_article_page.select_category_option_by_text(article_category)

        if not allow_translations:
            self.submit_kb_article_page.check_allow_translations_checkbox()

        product = kb_article_test_data["relevant_to_product"]
        if selected_product is True:
            self.submit_kb_article_page.click_on_a_particular_product(product)

        article_topic = [
            kb_article_test_data["selected_parent_topic"],
            kb_article_test_data["selected_child_topic"]
        ]

        # Adding Article topic
        if selected_topics is True:
            self.submit_kb_article_page.click_on_a_particular_parent_topic_checkbox(
                article_topic[0]
            )
            self.submit_kb_article_page.click_on_a_particular_child_topic_checkbox(
                article_topic[0],
                article_topic[1],
            )

        # Interacting with Allow Discussion checkbox
        if (allow_discussion is True) and (
            self.submit_kb_article_page
                .is_allow_discussion_on_article_checkbox_checked() is False):
            self.submit_kb_article_page.check_allow_discussion_on_article_checkbox()
        elif (allow_discussion is False) and (
            self.submit_kb_article_page
                .is_allow_discussion_on_article_checkbox_checked() is True):
            self.submit_kb_article_page.check_allow_discussion_on_article_checkbox()

        self.submit_kb_article_page.add_text_to_related_documents_field(
            kb_article_test_data["related_documents"])

        keyword = None
        if article_keyword is None:
            self.submit_kb_article_page.add_text_to_keywords_field(
                kb_article_test_data["keywords"])
            keyword = kb_article_test_data["keywords"]
        else:
            self.submit_kb_article_page.add_text_to_keywords_field(article_keyword)
            keyword = article_keyword

        summary = None
        if search_summary is None:
            self.submit_kb_article_page.add_text_to_search_result_summary_field(
                kb_article_test_data["search_result_summary"]
            )
            summary = kb_article_test_data["search_result_summary"]
        else:
            self.submit_kb_article_page.add_text_to_search_result_summary_field(
                search_summary
            )
            summary = search_summary

        if not self.submit_kb_article_page.is_content_textarea_displayed():
            self.submit_kb_article_page.click_on_toggle_syntax_highlight_option()

        if article_content is None:
            self.submit_kb_article_page.add_text_to_content_textarea(
                kb_article_test_data["article_content"])
        else:
            self.submit_kb_article_page.add_text_to_content_textarea(article_content)

        if article_content_image != '':
            self.submit_kb_article_page.click_on_insert_media_button()
            self.add_media_flow.add_media_to_kb_article(
                file_type="Image",
                file_name=article_content_image
            )

        if expiry_date is not None:
            self.submit_kb_article_page.add_text_to_expiry_date_field(expiry_date)

        # We need to evaluate in order to fetch the slug field value
        slug = self.page.evaluate(
            'document.getElementById("id_slug").value'
        )

        first_revision_id = None
        if submit_article is True:
            # If title and slug are empty we are not reaching the description field.
            if ((article_title != '') and (article_slug != '') and (
                    search_summary != "") and (article_content != "")):
                self.submit_kb_article_page.click_on_submit_for_review_button()
                self.submit_kb_article_page.add_text_to_changes_description_field(
                    kb_article_test_data["changes_description"]
                )
                self.submit_kb_article_page.click_on_changes_submit_button()
                try:
                    first_revision_id = self.kb_article_show_history_page.get_last_revision_id()
                except IndexError:
                    print("Chances are that the form was not submitted successfully")
            else:
                self.submit_kb_article_page.click_on_submit_for_review_button()

        article_url = self.submit_kb_article_page.get_article_page_url()

        if approve_first_revision:
            self.kb_article_page.click_on_show_history_option()
            if ready_for_localization:
                self.approve_kb_revision(revision_id=first_revision_id, ready_for_l10n=True)
            else:
                self.approve_kb_revision(revision_id=first_revision_id)

        return {"article_title": kb_article_title,
                "article_content": kb_article_test_data["article_content"],
                "article_content_html": kb_article_test_data['article_content_html_rendered'],
                "article_slug": slug,
                "article_child_topic": kb_article_test_data["selected_child_topic"],
                "article_category": article_category,
                "article_product": product,
                "article_topic": article_topic,
                "article_review_description": kb_article_test_data["changes_description"],
                "keyword": keyword,
                "search_results_summary": summary,
                "expiry_date": kb_article_test_data["expiry_date"],
                "article_url": article_url,
                "first_revision_id": first_revision_id
                }

    def approve_kb_revision(self, **kwargs):
        return self.utilities.re_call_function_on_error(
            lambda: self._approve_kb_revision(**kwargs)
        )

    def _approve_kb_revision(self, revision_id: str,
                             revision_needs_change=False,
                             ready_for_l10n=False,
                             significance_type=''):
        if (KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT not in
                self.utilities.get_page_url()):
            self.kb_article_page.click_on_show_history_option()

        self.kb_article_show_history_page.click_on_review_revision(
            revision_id
        )
        self.kb_article_review_revision_page.click_on_approve_revision_button()

        if revision_needs_change:
            if not self.kb_article_review_revision_page.is_needs_change_checkbox_checked():
                self.kb_article_review_revision_page.click_on_needs_change_checkbox()
            self.kb_article_review_revision_page.add_text_to_needs_change_comment(
                self.utilities.kb_revision_test_data['needs_change_message']
            )

        if ready_for_l10n:
            self.kb_article_review_revision_page.check_ready_for_localization_checkbox()

        if significance_type != '':
            if significance_type == 'minor':
                self.kb_article_review_revision_page.click_on_minor_significance_option()
            if significance_type == 'normal':
                self.kb_article_review_revision_page.click_on_normal_significance_option()
            if significance_type == 'major':
                self.kb_article_review_revision_page.click_on_major_significance_option()

        self.kb_article_review_revision_page.click_accept_revision_accept_button()

    def submit_new_kb_revision(self, **kwargs):
        return self.utilities.re_call_function_on_error(
            lambda: self._submit_new_kb_revision(**kwargs)
        )

    def _submit_new_kb_revision(self,
                                keywords=None,
                                search_result_summary=None,
                                content=None,
                                expiry_date=None,
                                changes_description=None,
                                is_admin=False,
                                approve_revision=False,
                                revision_needs_change=False,
                                ready_for_l10n=False,
                                significance_type=''
                                ) -> dict[str, Any]:

        self.kb_article_page.click_on_edit_article_option()

        # Only admin accounts can update article keywords.
        if is_admin:
            # Keywords step.
            if keywords is None:
                self.edit_kb_article_page.fill_edit_article_keywords_field(
                    self.utilities.kb_article_test_data['updated_keywords']
                )
            else:
                self.edit_kb_article_page.fill_edit_article_keywords_field(keywords)

        # Search Result Summary step.
        if search_result_summary is None:
            self.edit_kb_article_page.fill_edit_article_search_result_summary_field(
                self.utilities.kb_article_test_data['updated_search_result_summary']
            )
        else:
            self.edit_kb_article_page.fill_edit_article_search_result_summary_field(
                search_result_summary)

        # Content step.
        if content is None:
            self.edit_kb_article_page.fill_edit_article_content_field(
                self.utilities.kb_article_test_data['updated_article_content']
            )
        else:
            self.edit_kb_article_page.fill_edit_article_content_field(content)

        # Expiry date step.
        if expiry_date is None:
            self.edit_kb_article_page.fill_edit_article_expiry_date(
                self.utilities.kb_article_test_data['updated_expiry_date']
            )
        else:
            self.edit_kb_article_page.fill_edit_article_expiry_date(expiry_date)

        # Submitting for preview steps
        self.edit_kb_article_page.click_submit_for_review_button()

        if changes_description is None:
            self.edit_kb_article_page.fill_edit_article_changes_panel_comment(
                self.utilities.kb_article_test_data['changes_description']
            )
        else:
            self.edit_kb_article_page.fill_edit_article_changes_panel_comment(changes_description)

        self.edit_kb_article_page.click_edit_article_changes_panel_submit_button()

        revision_id = self.kb_article_show_history_page.get_last_revision_id()

        if approve_revision:
            self.approve_kb_revision(revision_id=revision_id, ready_for_l10n=ready_for_l10n,
                                     significance_type=significance_type)

        revision_time = self.kb_article_show_history_page.get_revision_time(revision_id)

        return {"revision_id": revision_id,
                "revision_time": revision_time,
                "changes_description": self.utilities.kb_article_test_data['changes_description']
                }

    def kb_article_creation_via_api(self, page: Page, approve_revision=False,
                                    is_template=False, product=None, topic=None, category=None
                                    ) -> dict[str, Any]:
        """
        Create a new KB article via API.
        :param page: Page object.
        :param approve_revision: Approve the first revision of the article.
        :param is_template: Create a KB template.
        :param product: Product ID.
        :param topic: Topic ID.
        :param category: Category ID.
        """
        kb_article_test_data = self.utilities.kb_article_test_data
        self.utilities.navigate_to_link(KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL)
        if is_template or category == "60":
            kb_title = (kb_article_test_data["kb_template_title"] + self.utilities.
                        generate_random_number(0, 5000))
            category = "60"
        elif category is None:
            kb_title = (kb_article_test_data["kb_article_title"] + self.utilities.
                        generate_random_number(0, 5000))
            category = "10"
        else:
            kb_title = (kb_article_test_data["kb_article_title"] + self.utilities.
                        generate_random_number(0, 5000))

        topic = topic if topic is not None else "383"
        product = product if product is not None else "1"
        slug = slugify(kb_title)

        form_data = {
            "csrfmiddlewaretoken": self.utilities.get_csrfmiddlewaretoken(),
            "title": kb_title,
            "slug": slug,
            "category": category,
            "is_localizable": "on",
            "products": product,
            "topics": topic,
            "allow_discussion": "on",
            "keywords": kb_article_test_data["keywords"],
            "summary": kb_article_test_data["search_result_summary"],
            "content": kb_article_test_data["article_content"],
            "expires": "",
            "based_on": "",
            "comment": kb_article_test_data["changes_description"]
        }

        response = self.utilities.post_api_request(
            page, KBArticlePageMessages.CREATE_NEW_KB_ARTICLE_STAGE_URL, data=form_data
        )

        print(response)
        self.utilities.navigate_to_link(response.url)

        first_revision_id = self.kb_article_show_history_page.get_last_revision_id()
        if approve_revision:
            self.approve_kb_revision(revision_id=first_revision_id)

        return {"article_title": kb_title,
                "article_content": kb_article_test_data["article_content"],
                "article_slug": slug,
                "keyword": kb_article_test_data["keywords"],
                "search_results_summary": kb_article_test_data["search_result_summary"],
                "article_url": response.url.removesuffix("/history"),
                "article_show_history_url": self.utilities.get_page_url(),
                "first_revision_id": first_revision_id,
                "article_review_description": kb_article_test_data["changes_description"]
                }

    def defer_revision(self, revision_id: str):
        self.kb_article_show_history_page.click_on_review_revision(revision_id)
        self.kb_article_review_revision_page.click_on_defer_revision_button()
        self.kb_article_review_revision_page.click_on_defer_confirm_button()
