from playwright.sync_api import Page

from playwright_tests.flows.ask_a_question_flows.aaq_flows.aaq_flow import AAQFlow
from playwright_tests.flows.explore_articles_flows.article_flows.add_kb_article_flow import (
    AddKbArticleFlow)
from playwright_tests.flows.auth_flows.auth_flow import AuthFlowPage
from playwright_tests.flows.explore_articles_flows.article_flows.kb_localization_flow import \
    KbArticleTranslationFlow
from playwright_tests.flows.explore_articles_flows.article_flows.add_kb_media_flow import \
    AddKbMediaFlow
from playwright_tests.flows.explore_articles_flows.article_flows.delete_kb_article_flow import \
    DeleteKbArticleFlow
from playwright_tests.flows.explore_articles_flows.article_flows.edit_article_meta_flow import \
    EditArticleMetaFlow
from playwright_tests.flows.explore_articles_flows.article_flows.kb_article_threads_flow import \
    KbThreads
from playwright_tests.flows.messaging_system_flows.messaging_system_flow import (
    MessagingSystemFlows)
from playwright_tests.flows.user_groups_flows.user_group_flow import UserGroupFlow
from playwright_tests.flows.user_profile_flows.edit_profile_data_flow import EditProfileDataFlow
from playwright_tests.pages.ask_a_question.aaq_pages.aaq_form_page import AAQFormPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions_pages.\
    contributor_discussions_page import ContributorDiscussionPage
from playwright_tests.pages.contribute.contribute_pages.contributor_discussions_pages.\
    discussions_page import DiscussionsPage
from playwright_tests.pages.contribute.contributor_tools_pages.article_discussions_page import \
    ArticleDiscussionsPage
from playwright_tests.pages.contribute.contributor_tools_pages.kb_dashboard_page import KBDashboard
from playwright_tests.pages.contribute.contributor_tools_pages.l10n_most_visited_translations \
    import MostVisitedTranslations
from playwright_tests.pages.contribute.contributor_tools_pages.l10n_unreviewed import \
    UnreviewedLocalizationPage
from playwright_tests.pages.contribute.contributor_tools_pages.media_gallery import MediaGallery
from playwright_tests.pages.contribute.contributor_tools_pages.moderate_forum_content import \
    ModerateForumContent
from playwright_tests.pages.contribute.contributor_tools_pages.recent_revisions_page import \
    RecentRevisions
from playwright_tests.pages.contribute.groups_page import GroupsPage
from playwright_tests.pages.explore_help_articles.articles.kb_article_discussion_page import \
    KBArticleDiscussionPage
from playwright_tests.pages.explore_help_articles.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_article_review_revision_page import \
    KBArticleReviewRevisionPage
from playwright_tests.pages.explore_help_articles.articles.kb_category_page import KBCategoryPage
from playwright_tests.pages.explore_help_articles.articles.kb_revision_preview_page import \
    KBArticleRevisionsPreviewPage
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import (
    KBArticleShowHistoryPage)
from playwright_tests.pages.auth_page import AuthPage
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_meta import \
    KBArticleEditMetadata
from playwright_tests.pages.explore_help_articles.articles.kb_edit_article_page import \
    EditKBArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_translate_article_page import \
    TranslateArticlePage
from playwright_tests.pages.explore_help_articles.articles.kb_what_links_here_page import \
    WhatLinksHerePage
from playwright_tests.pages.explore_help_articles.articles.products_page import ProductsPage
from playwright_tests.pages.explore_help_articles.articles.submit_kb_article_page import \
    SubmitKBArticlePage
from playwright_tests.pages.ask_a_question.contact_support_pages.contact_support_page import (
    ContactSupportPage)
from playwright_tests.pages.contribute.contribute_pages.contribute_page import ContributePage
from playwright_tests.pages.contribute.contribute_pages.ways_to_contribute_pages import (
    WaysToContributePages)
from playwright_tests.pages.explore_help_articles.explore_by_topic_page import ExploreByTopicPage
from playwright_tests.pages.footer import FooterSection
from playwright_tests.pages.community_forums.forums_pages.product_support_forum import (
    ProductSupportForum)
from playwright_tests.pages.community_forums.forums_pages.support_forums_page import (
    SupportForumsPage)
from playwright_tests.pages.homepage import Homepage
from playwright_tests.pages.messaging_system_pages.inbox_page import InboxPage
from playwright_tests.pages.messaging_system_pages.mess_system_user_navbar import (
    MessagingSystemUserNavbar)
from playwright_tests.pages.messaging_system_pages.new_message import NewMessagePage
from playwright_tests.pages.messaging_system_pages.sent_messages import SentMessagePage
from playwright_tests.pages.ask_a_question.product_solutions_pages.product_solutions_page import \
    ProductSolutionsPage
from playwright_tests.pages.explore_help_articles.product_support_page import ProductSupportPage
from playwright_tests.pages.ask_a_question.product_topics_pages.product_topics_page import (
    ProductTopicPage)
from playwright_tests.pages.search.search_page import SearchPage
from playwright_tests.pages.top_navbar import TopNavbar
from playwright_tests.pages.user_pages.my_profile_answers_page import MyProfileAnswersPage
from playwright_tests.pages.user_pages.my_profile_documents_page import MyProfileDocumentsPage
from playwright_tests.pages.user_pages.my_profile_edit import MyProfileEdit
from playwright_tests.pages.user_pages.my_profile_edit_contribution_areas_page import (
    MyProfileEditContributionAreasPage)
from playwright_tests.pages.user_pages.my_profile_edit_settings_page import (
    MyProfileEditSettingsPage)
from playwright_tests.pages.user_pages.my_profile_my_questions_page import MyProfileMyQuestionsPage
from playwright_tests.pages.user_pages.my_profile_page import MyProfilePage
from playwright_tests.pages.user_pages.my_profile_user_navbar import UserNavbar
from playwright_tests.pages.ask_a_question.posted_question_pages.questions_page import QuestionPage


class SumoPages:
    def __init__(self, page: Page):
        # Auth Page.
        self.auth_page = AuthPage(page)

        # Search Page.
        self.search_page = SearchPage(page)

        # Homepage.
        self.homepage = Homepage(page)

        # Ways to contribute_messages pages.
        self.ways_to_contribute_pages = WaysToContributePages(page)

        # Footer.
        self.footer_section = FooterSection(page)

        # top-navbar.
        self.top_navbar = TopNavbar(page)

        # Profile pages.
        self.my_profile_page = MyProfilePage(page)
        self.my_answers_page = MyProfileAnswersPage(page)
        self.my_questions_page = MyProfileMyQuestionsPage(page)
        self.question_page = QuestionPage(page)
        self.my_documents_page = MyProfileDocumentsPage(page)
        self.edit_my_profile_page = MyProfileEdit(page)
        self.edit_my_profile_settings_page = MyProfileEditSettingsPage(page)
        self.edit_my_profile_con_areas_page = MyProfileEditContributionAreasPage(page)
        self.user_navbar = UserNavbar(page)

        # Messaging System.
        self.sent_message_page = SentMessagePage(page)
        self.new_message_page = NewMessagePage(page)
        self.inbox_page = InboxPage(page)
        self.mess_system_user_navbar = MessagingSystemUserNavbar(page)

        # Contribute page.
        self.contribute_page = ContributePage(page)

        # AAQ Pages
        self.aaq_form_page = AAQFormPage(page)

        # Explore our help articles products page.
        self.products_page = ProductsPage(page)
        self.explore_by_product_page = ExploreByTopicPage(page)

        # KB Articles.
        self.kb_submit_kb_article_form_page = SubmitKBArticlePage(page)
        self.kb_article_page = KBArticlePage(page)
        self.kb_edit_article_page = EditKBArticlePage(page)
        self.kb_article_discussion_page = KBArticleDiscussionPage(page)
        self.kb_article_show_history_page = KBArticleShowHistoryPage(page)
        self.kb_article_review_revision_page = KBArticleReviewRevisionPage(page)
        self.kb_article_preview_revision_page = KBArticleRevisionsPreviewPage(page)
        self.kb_article_edit_article_metadata_page = KBArticleEditMetadata(page)
        self.kb_what_links_here_page = WhatLinksHerePage(page)
        self.kb_category_page = KBCategoryPage(page)
        self.translate_article_page = TranslateArticlePage(page)

        # Product Topics page
        self.product_topics_page = ProductTopicPage(page)

        # Product Solutions page.
        self.product_solutions_page = ProductSolutionsPage(page)

        # Product Support page.
        self.product_support_page = ProductSupportPage(page)

        # Contact Support page.
        self.contact_support_page = ContactSupportPage(page)

        # Forums
        self.support_forums_page = SupportForumsPage(page)
        self.product_support_forum = ProductSupportForum(page)

        # User Groups
        self.user_groups = GroupsPage(page)

        # Article Discussions page.
        self.article_discussions_page = ArticleDiscussionsPage(page)

        # Dashboard pages.
        self.kb_dashboard_page = KBDashboard(page)
        self.recent_revisions_page = RecentRevisions(page)
        self.localization_unreviewed_page = UnreviewedLocalizationPage(page)
        self.most_visited_translations_page = MostVisitedTranslations(page)

        # Media Gallery page.
        self.media_gallery = MediaGallery(page)

        # Moderate Forum Page
        self.moderate_forum_content_page = ModerateForumContent(page)

        # Discussions pages
        self.contributor_discussions_page = ContributorDiscussionPage(page)
        self.discussions_page = DiscussionsPage(page)

        # Auth flow Page.
        self.auth_flow_page = AuthFlowPage(page)

        # AAQ Flow.
        self.aaq_flow = AAQFlow(page)

        # Messaging System Flows.
        self.messaging_system_flow = MessagingSystemFlows(page)

        # Edit profile flow
        self.edit_profile_flow = EditProfileDataFlow(page)

        # KB article Flow
        self.submit_kb_article_flow = AddKbArticleFlow(page)

        # KB article translation Flow
        self.submit_kb_translation_flow = KbArticleTranslationFlow(page)

        # KB article deletion Flow
        self.kb_article_deletion_flow = DeleteKbArticleFlow(page)

        # KB article edit metadata Flow
        self.edit_article_metadata_flow = EditArticleMetaFlow(page)

        # KB add article media Flow
        self.add_kb_media_flow = AddKbMediaFlow(page)

        # User Group Flow
        self.user_group_flow = UserGroupFlow(page)

        # KB article threads Flow
        self.kb_article_thread_flow = KbThreads(page)
