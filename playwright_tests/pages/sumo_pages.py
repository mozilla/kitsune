from functools import cached_property

from playwright.sync_api import Page

from playwright_tests.flows.ask_a_question_flows.aaq_flows.aaq_flow import AAQFlow
from playwright_tests.flows.auth_flows.auth_flow import AuthFlowPage
from playwright_tests.flows.contributor_threads_flows.contributor_threads_flows import (
    ContributorThreadFlow,
)
from playwright_tests.flows.explore_articles_flows.article_flows.add_kb_article_flow import (
    AddKbArticleFlow,
)
from playwright_tests.flows.explore_articles_flows.article_flows.add_kb_media_flow import (
    AddKbMediaFlow,
)
from playwright_tests.flows.explore_articles_flows.article_flows.delete_kb_article_flow import (
    DeleteKbArticleFlow,
)
from playwright_tests.flows.explore_articles_flows.article_flows.edit_article_meta_flow import (
    EditArticleMetaFlow,
)
from playwright_tests.flows.explore_articles_flows.article_flows.kb_article_threads_flow import (
    KbThreads,
)
from playwright_tests.flows.explore_articles_flows.article_flows.kb_localization_flow import (
    KbArticleTranslationFlow,
)
from playwright_tests.flows.messaging_system_flows.messaging_system_flow import (
    MessagingSystemFlows,
)
from playwright_tests.flows.user_groups_flows.user_group_flow import UserGroupFlow
from playwright_tests.flows.user_profile_flows.edit_profile_data_flow import EditProfileDataFlow
from playwright_tests.pages.ask_a_question.aaq_pages.aaq_form_page import AAQFormPage
from playwright_tests.pages.ask_a_question.contact_support_pages.contact_support_page import (
    ContactSupportPage,
)
from playwright_tests.pages.ask_a_question.posted_question_pages.questions_page import QuestionPage
from playwright_tests.pages.ask_a_question.product_solutions_pages.product_solutions_page import (
    ProductSolutionsPage,
)
from playwright_tests.pages.ask_a_question.product_topics_pages.product_topics_page import (
    ProductTopicPage,
)
from playwright_tests.pages.auth_page import AuthPage
from playwright_tests.pages.common_elements.common_web_elements import CommonWebElements
from playwright_tests.pages.community_forums.forums_pages.product_support_forum import (
    ProductSupportForum,
)
from playwright_tests.pages.community_forums.forums_pages.all_community_forums_page import (
    SupportForumsPage,
)
from playwright_tests.pages.contribute.contribute_pages.contribute_page import ContributePage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.\
    contributor_discussions_page import ContributorDiscussionPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.\
    delete_thread_post_page import DeleteThreadPostPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.\
    edit_thread_post_page import EditThreadPostPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.\
    edit_thread_title_page import EditThreadTitle
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.\
    forum_discussions_page import ForumDiscussionsPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.forum_thread_page import (
    ForumThreadPage,
)
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions.new_thread_page import (
    NewThreadPage,
)
from playwright_tests.pages.contribute.contribute_pages.ways_to_contribute_pages import (
    WaysToContributePages,
)
from playwright_tests.pages.contribute.contributor_tools_pages.article_discussions_page import (
    ArticleDiscussionsPage,
)
from playwright_tests.pages.contribute.contributor_tools_pages.community_hub_page import \
    CommunityHubPage
from playwright_tests.pages.contribute.contributor_tools_pages.kb_dashboard_page import KBDashboard
from playwright_tests.pages.contribute.contributor_tools_pages.l10n_most_visited_translations import (
    MostVisitedTranslations,
)
from playwright_tests.pages.contribute.contributor_tools_pages.l10n_unreviewed import (
    UnreviewedLocalizationPage,
)
from playwright_tests.pages.contribute.contributor_tools_pages.media_gallery import MediaGallery
from playwright_tests.pages.contribute.contributor_tools_pages.moderate_forum_content import (
    ModerateForumContent,
)
from playwright_tests.pages.contribute.contributor_tools_pages.recent_revisions_page import (
    RecentRevisions,
)
from playwright_tests.pages.contribute.groups_page import GroupsPage
from playwright_tests.pages.explore_help_articles.articles.kb_article_discussion_page import (
    KBArticleDiscussionPage,
)
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_article_review_revision_page import (
    KBArticleReviewRevisionPage,
)
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import (
    KBArticleShowHistoryPage,
)
from playwright_tests.pages.explore_help_articles.articles.kb_category_page import KBCategoryPage
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_meta import (
    KBArticleEditMetadata,
)
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_page import (
    EditKBArticlePage,
)
from playwright_tests.pages.explore_help_articles.articles.kb_revision_preview_page import (
    KBArticleRevisionsPreviewPage,
)
from playwright_tests.pages.explore_help_articles.articles.kb_translate_article_page import (
    TranslateArticlePage,
)
from playwright_tests.pages.explore_help_articles.articles.kb_what_links_here_page import (
    WhatLinksHerePage,
)
from playwright_tests.pages.explore_help_articles.articles.products_page import ProductsPage
from playwright_tests.pages.explore_help_articles.articles.submit_kb_article_page import (
    SubmitKBArticlePage,
)
from playwright_tests.pages.explore_help_articles.explore_by_topic_page import ExploreByTopicPage
from playwright_tests.pages.explore_help_articles.product_support_page import ProductSupportPage
from playwright_tests.pages.footer import FooterSection
from playwright_tests.pages.homepage import Homepage
from playwright_tests.pages.messaging_system_pages.inbox_page import InboxPage
from playwright_tests.pages.messaging_system_pages.mess_system_user_navbar import (
    MessagingSystemUserNavbar,
)
from playwright_tests.pages.messaging_system_pages.new_message import NewMessagePage
from playwright_tests.pages.messaging_system_pages.sent_messages import SentMessagePage
from playwright_tests.pages.search.search_page import SearchPage
from playwright_tests.pages.top_navbar import TopNavbar
from playwright_tests.pages.user_pages.my_profile_answers_page import MyProfileAnswersPage
from playwright_tests.pages.user_pages.my_profile_documents_page import MyProfileDocumentsPage
from playwright_tests.pages.user_pages.my_profile_edit import MyProfileEdit
from playwright_tests.pages.user_pages.my_profile_edit_contribution_areas_page import (
    MyProfileEditContributionAreasPage,
)
from playwright_tests.pages.user_pages.my_profile_edit_settings_page import (
    MyProfileEditSettingsPage,
)
from playwright_tests.pages.user_pages.my_profile_my_questions_page import MyProfileMyQuestionsPage
from playwright_tests.pages.user_pages.my_profile_page import MyProfilePage
from playwright_tests.pages.user_pages.my_profile_user_navbar import UserNavbar


class SumoPages:
    def __init__(self, page: Page):
        self._page = page

    # Auth Page.
    @cached_property
    def auth_page(self):
        return AuthPage(self._page)

    # Search Page.
    @cached_property
    def search_page(self):
        return SearchPage(self._page)

    # Homepage.
    @cached_property
    def homepage(self):
        return Homepage(self._page)

    # Ways to contribute_messages pages.
    @cached_property
    def ways_to_contribute_pages(self):
        return WaysToContributePages(self._page)

    # Footer.
    @cached_property
    def footer_section(self):
        return FooterSection(self._page)

    # top-navbar.
    @cached_property
    def top_navbar(self):
        return TopNavbar(self._page)

    # Profile pages.
    @cached_property
    def my_profile_page(self):
        return MyProfilePage(self._page)

    @cached_property
    def my_answers_page(self):
        return MyProfileAnswersPage(self._page)

    @cached_property
    def my_questions_page(self):
        return MyProfileMyQuestionsPage(self._page)

    @cached_property
    def question_page(self):
        return QuestionPage(self._page)

    @cached_property
    def my_documents_page(self):
        return MyProfileDocumentsPage(self._page)

    @cached_property
    def edit_my_profile_page(self):
        return MyProfileEdit(self._page)

    @cached_property
    def edit_my_profile_settings_page(self):
        return MyProfileEditSettingsPage(self._page)

    @cached_property
    def edit_my_profile_con_areas_page(self):
        return MyProfileEditContributionAreasPage(self._page)

    @cached_property
    def user_navbar(self):
        return UserNavbar(self._page)

    # Messaging System.
    @cached_property
    def sent_message_page(self):
        return SentMessagePage(self._page)

    @cached_property
    def new_message_page(self):
        return NewMessagePage(self._page)

    @cached_property
    def inbox_page(self):
        return InboxPage(self._page)

    @cached_property
    def mess_system_user_navbar(self):
        return MessagingSystemUserNavbar(self._page)

    # Contribute page.
    @cached_property
    def contribute_page(self):
        return ContributePage(self._page)

    # Community hub page.
    @cached_property
    def community_hub_page(self):
        return CommunityHubPage(self._page)

    # AAQ Pages
    @cached_property
    def aaq_form_page(self):
        return AAQFormPage(self._page)

    # Explore our help articles products page.
    @cached_property
    def products_page(self):
        return ProductsPage(self._page)

    @cached_property
    def explore_by_topic_page(self):
        return ExploreByTopicPage(self._page)

    # KB Articles.
    @cached_property
    def kb_submit_kb_article_form_page(self):
        return SubmitKBArticlePage(self._page)

    @cached_property
    def kb_article_page(self):
        return KBArticlePage(self._page)

    @cached_property
    def kb_edit_article_page(self):
        return EditKBArticlePage(self._page)

    @cached_property
    def kb_article_discussion_page(self):
        return KBArticleDiscussionPage(self._page)

    @cached_property
    def kb_article_show_history_page(self):
        return KBArticleShowHistoryPage(self._page)

    @cached_property
    def kb_article_review_revision_page(self):
        return KBArticleReviewRevisionPage(self._page)

    @cached_property
    def kb_article_preview_revision_page(self):
        return KBArticleRevisionsPreviewPage(self._page)

    @cached_property
    def kb_article_edit_article_metadata_page(self):
        return KBArticleEditMetadata(self._page)

    @cached_property
    def kb_what_links_here_page(self):
        return WhatLinksHerePage(self._page)

    @cached_property
    def kb_category_page(self):
        return KBCategoryPage(self._page)

    @cached_property
    def translate_article_page(self):
        return TranslateArticlePage(self._page)

    # Product Topics page
    @cached_property
    def product_topics_page(self):
        return ProductTopicPage(self._page)

    # Product Solutions page.
    @cached_property
    def product_solutions_page(self):
        return ProductSolutionsPage(self._page)

    # Product Support page.
    @cached_property
    def product_support_page(self):
        return ProductSupportPage(self._page)

    # Contact Support page.
    @cached_property
    def contact_support_page(self):
        return ContactSupportPage(self._page)

    # Forums
    @cached_property
    def all_community_forums_page(self):
        return SupportForumsPage(self._page)

    @cached_property
    def product_support_forum(self):
        return ProductSupportForum(self._page)

    # User Groups
    @cached_property
    def user_groups(self):
        return GroupsPage(self._page)

    # Article Discussions page.
    @cached_property
    def article_discussions_page(self):
        return ArticleDiscussionsPage(self._page)

    # Dashboard pages.
    @cached_property
    def kb_dashboard_page(self):
        return KBDashboard(self._page)

    @cached_property
    def recent_revisions_page(self):
        return RecentRevisions(self._page)

    @cached_property
    def localization_unreviewed_page(self):
        return UnreviewedLocalizationPage(self._page)

    @cached_property
    def most_visited_translations_page(self):
        return MostVisitedTranslations(self._page)

    # Media Gallery page.
    @cached_property
    def media_gallery(self):
        return MediaGallery(self._page)

    # Moderate Forum Page
    @cached_property
    def moderate_forum_content_page(self):
        return ModerateForumContent(self._page)

    # Discussions pages
    @cached_property
    def contributor_discussions_page(self):
        return ContributorDiscussionPage(self._page)

    @cached_property
    def forum_discussions_page(self):
        return ForumDiscussionsPage(self._page)

    @cached_property
    def new_thread_page(self):
        return NewThreadPage(self._page)

    @cached_property
    def edit_thread_title_page(self):
        return EditThreadTitle(self._page)

    @cached_property
    def edit_post_thread_page(self):
        return EditThreadPostPage(self._page)

    @cached_property
    def delete_thread_post_page(self):
        return DeleteThreadPostPage(self._page)

    @cached_property
    def forum_thread_page(self):
        return ForumThreadPage(self._page)

    # Discussion Threads flow.
    @cached_property
    def contributor_thread_flow(self):
        return ContributorThreadFlow(self._page)

    # Auth flow Page.
    @cached_property
    def auth_flow_page(self):
        return AuthFlowPage(self._page)

    # AAQ Flow.
    @cached_property
    def aaq_flow(self):
        return AAQFlow(self._page)

    # Messaging System Flows.
    @cached_property
    def messaging_system_flow(self):
        return MessagingSystemFlows(self._page)

    # Edit profile flow
    @cached_property
    def edit_profile_flow(self):
        return EditProfileDataFlow(self._page)

    # KB article Flow
    @cached_property
    def submit_kb_article_flow(self):
        return AddKbArticleFlow(self._page)

    # KB article translation Flow
    @cached_property
    def submit_kb_translation_flow(self):
        return KbArticleTranslationFlow(self._page)

    # KB article deletion Flow
    @cached_property
    def kb_article_deletion_flow(self):
        return DeleteKbArticleFlow(self._page)

    # KB article edit metadata Flow
    @cached_property
    def edit_article_metadata_flow(self):
        return EditArticleMetaFlow(self._page)

    # KB add article media Flow
    @cached_property
    def add_kb_media_flow(self):
        return AddKbMediaFlow(self._page)

    # User Group Flow
    @cached_property
    def user_group_flow(self):
        return UserGroupFlow(self._page)

    # KB article threads Flow
    @cached_property
    def kb_article_thread_flow(self):
        return KbThreads(self._page)

    # Common Web Elements
    @cached_property
    def common_web_elements(self):
        return CommonWebElements(self._page)
