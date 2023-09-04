from selenium.webdriver.remote.webdriver import WebDriver

from selenium_tests.flows.aaq_flows.aaq_flow import AAQFlow
from selenium_tests.flows.article_flows.add_kb_article_flow import AddKbArticleFlow
from selenium_tests.flows.auth_flows.auth_flow import AuthFlowPage
from selenium_tests.flows.messaging_system_flows.messaging_system_flow import MessagingSystemFlows
from selenium_tests.flows.user_profile_flows.edit_profile_data_flow import EditProfileDataFlow
from selenium_tests.pages.articles.kb_article_page import KBArticlePage
from selenium_tests.pages.articles.kb_article_show_history_page import KBArticleShowHistoryPage
from selenium_tests.pages.auth_page import AuthPage
from selenium_tests.pages.contact_support_pages.contact_support_page import ContactSupportPage
from selenium_tests.pages.contribute_pages.contribute_page import ContributePage
from selenium_tests.pages.contribute_pages.ways_to_contribute_pages import WaysToContributePages
from selenium_tests.pages.footer import FooterSection
from selenium_tests.pages.homepage import Homepage
from selenium_tests.pages.messaging_system_pages.inbox_page import InboxPage
from selenium_tests.pages.messaging_system_pages.mess_system_user_navbar import (
    MessagingSystemUserNavbar,
)
from selenium_tests.pages.messaging_system_pages.new_message import NewMessagePage
from selenium_tests.pages.messaging_system_pages.sent_messages import SentMessagePage
from selenium_tests.pages.product_solutions_pages.product_solutions_page import (
    ProductSolutionsPage,
)

# from pages.search_result_page import SearchResultPage
from selenium_tests.pages.top_navbar import TopNavbar
from selenium_tests.pages.product_support_page import ProductSupportPage
from selenium_tests.pages.user_pages.my_profile_answers_page import MyProfileAnswersPage
from selenium_tests.pages.user_pages.my_profile_documents_page import MyProfileDocumentsPage
from selenium_tests.pages.user_pages.my_profile_edit import MyProfileEdit
from selenium_tests.pages.user_pages.my_profile_edit_contribution_areas_page import (
    MyProfileEditContributionAreasPage,
)
from selenium_tests.pages.user_pages.my_profile_edit_settings_page import MyProfileEditSettingsPage
from selenium_tests.pages.user_pages.my_profile_manage_watch_list_page import (
    MyProfileManageWatchListPage,
)
from selenium_tests.pages.user_pages.my_profile_my_questions_page import MyProfileMyQuestionsPage
from selenium_tests.pages.user_pages.my_profile_page import MyProfilePage
from selenium_tests.pages.user_pages.my_profile_user_navbar import UserNavbar
from selenium_tests.pages.user_questions_pages.questions_page import QuestionPage


class Pages:
    def __init__(self, driver: WebDriver):
        # Contribute pages
        self.contribute_page = ContributePage(driver)
        self.ways_to_contribute_pages = WaysToContributePages(driver)

        # Contact support page
        self.contact_support_page = ContactSupportPage(driver)

        # Homepage
        self.homepage = Homepage(driver)

        # Footer section
        self.footer_section = FooterSection(driver)

        # Top-Navbar
        self.top_navbar = TopNavbar(driver)

        # Questions pages
        self.question_page = QuestionPage(driver)

        # Product solutions pages
        self.product_solutions_page = ProductSolutionsPage(driver)

        # Profile pages
        self.my_profile_page = MyProfilePage(driver)
        self.edit_my_profile_page = MyProfileEdit(driver)
        self.edit_my_profile_settings_page = MyProfileEditSettingsPage(driver)
        self.edit_my_profile_con_areas_page = MyProfileEditContributionAreasPage(driver)
        self.edit_my_profile_watch_list_page = MyProfileManageWatchListPage(driver)
        self.my_questions_page = MyProfileMyQuestionsPage(driver)
        self.my_answers_page = MyProfileAnswersPage(driver)
        self.my_documents_page = MyProfileDocumentsPage(driver)
        self.user_navbar = UserNavbar(driver)

        # Messaging system
        self.sent_message_page = SentMessagePage(driver)
        self.new_message_page = NewMessagePage(driver)
        self.inbox_page = InboxPage(driver)
        self.mess_system_user_navbar = MessagingSystemUserNavbar(driver)

        # Auth page
        self.auth_page = AuthPage(driver)

        # Auth flow
        self.auth_flow_page = AuthFlowPage(driver)

        # AAQ Flow
        self.aaq_flow = AAQFlow(driver)

        # KB article Flow
        self.submit_kb_article_flow = AddKbArticleFlow(driver)

        # Edit profile flow
        self.edit_profile_flow = EditProfileDataFlow(driver)

        # Messaging system flow
        self.messaging_system_flow = MessagingSystemFlows(driver)

        # Articles
        self.kb_article_page = KBArticlePage(driver)
        self.kb_article_show_history_page = KBArticleShowHistoryPage(driver)

        # Product Support Page
        self.product_support_page = ProductSupportPage(driver)

        # self.search_results_page = SearchResultPage(driver)
