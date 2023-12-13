from playwright.sync_api import Page

from playwright_tests.flows.aaq_flows.aaq_flow import AAQFlow
from playwright_tests.flows.article_flows.add_kb_article_flow import AddKbArticleFlow
from playwright_tests.flows.auth_flows.auth_flow import AuthFlowPage
from playwright_tests.flows.messaging_system_flows.messaging_system_flow import (
    MessagingSystemFlows)
from playwright_tests.flows.user_profile_flows.edit_profile_data_flow import EditProfileDataFlow
from playwright_tests.pages.aaq_pages.aaq_form_page import AAQFormPage
from playwright_tests.pages.articles.kb_article_page import KBArticlePage
from playwright_tests.pages.articles.kb_article_show_history_page import KBArticleShowHistoryPage
from playwright_tests.pages.auth_page import AuthPage
from playwright_tests.pages.contact_support_pages.contact_support_page import ContactSupportPage
from playwright_tests.pages.contribute_pages.contribute_page import ContributePage
from playwright_tests.pages.contribute_pages.ways_to_contribute_pages import WaysToContributePages
from playwright_tests.pages.footer import FooterSection
from playwright_tests.pages.forums_pages.support_forums_page import SupportForumsPage
from playwright_tests.pages.homepage import Homepage
from playwright_tests.pages.messaging_system_pages.inbox_page import InboxPage
from playwright_tests.pages.messaging_system_pages.mess_system_user_navbar import (
    MessagingSystemUserNavbar)
from playwright_tests.pages.messaging_system_pages.new_message import NewMessagePage
from playwright_tests.pages.messaging_system_pages.sent_messages import SentMessagePage
from playwright_tests.pages.product_solutions_pages.product_solutions_page import \
    ProductSolutionsPage
from playwright_tests.pages.product_support_page import ProductSupportPage
from playwright_tests.pages.product_topics_pages.product_topics_page import ProductTopicPage
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
from playwright_tests.pages.user_questions_pages.questions_page import QuestionPage


class SumoPages:
    def __init__(self, page: Page):
        # Auth Page.
        self.auth_page = AuthPage(page)

        # Homepage.
        self.homepage = Homepage(page)

        # Ways to contribute pages.
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

        # KB Articles.
        self.kb_article_page = KBArticlePage(page)
        self.kb_article_show_history_page = KBArticleShowHistoryPage(page)

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
