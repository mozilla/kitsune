from typing import Any
import pytest
from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.flows.explore_articles_flows.article_flows.add_kb_article_flow import \
    AddKbArticleFlow
from playwright_tests.flows.explore_articles_flows.article_flows.delete_kb_article_flow import \
    DeleteKbArticleFlow


@pytest.fixture
def create_delete_article(request, page: Page):
    utilities = Utilities(page)
    submit_kb_article_flow = AddKbArticleFlow(page)
    kb_article_deletion_flow = DeleteKbArticleFlow(page)
    auto_close = True
    marker = request.node.get_closest_marker("create_delete_article")
    if marker is not None:
        auto_close = marker.args[0]
    created_articles_url = []

    def _create_delete_article(username: str, data: dict[str, Any] = {}) -> (
            tuple)[dict[str, Any], str]:
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts[username]
        ))
        defaults = {
            'article_title': None,
            'article_slug': None,
            'article_category': None,
            'article_keyword': None,
            'allow_discussion': True,
            'allow_translations': True,
            'selected_relevancy': True,
            'selected_topics': True,
            'search_summary': None,
            'article_content': None,
            'article_content_image': '',
            'submit_article': True,
            'is_template': False,
            'expiry_date': None,
            'restricted_to_groups': None,
            'single_group': '',
            'approve_first_revision': False,
            'ready_for_localization': False
        }
        article_data = {**defaults, **data}
        article_info = submit_kb_article_flow.submit_simple_kb_article(**article_data)
        created_articles_url.append(article_info['article_url'])
        return article_info, utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
        )

    yield _create_delete_article

    if auto_close:
        utilities.delete_cookies()
        for article_link in created_articles_url:
            utilities.navigate_to_link(article_link)
            utilities.start_existing_session(
                utilities.username_extraction_from_email(
                    utilities.user_secrets_accounts['TEST_ACCOUNT_MODERATOR']
                ))
            kb_article_deletion_flow.delete_kb_article()
