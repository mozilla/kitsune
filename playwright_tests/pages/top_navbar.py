from playwright.sync_api import ElementHandle, Locator, Page

from playwright_tests.core.basepage import BasePage


class TopNavbar(BasePage):
    """
        General page locators
    """
    __menu_titles = "//div[@id='main-navigation']//a[contains(@class,'mzp-c-menu-title')]"
    __sumo_nav_logo = "//div[@class='sumo-nav--logo']/a/img"

    """
        Locators belonging to the 'Explore Help Articles' top-navbar section".
    """
    __explore_by_topic_top_navbar_header = ("//h4[@class='mzp-c-menu-item-title' and text("
                                            ")='Explore by topic']")
    __explore_by_product_top_navbar_header = ("//h4[@class='mzp-c-menu-item-title' and text("
                                              ")='Explore by product']")
    __explore_help_articles_top_navbar_option = (
        "//a[@class='mzp-c-menu-title sumo-nav--link' "
        "and normalize-space(text())='Explore Help "
        "Articles']"
    )
    __explore_our_help_articles_view_all_option = (
        "//ul[@class='mzp-c-menu-item-list "
        "sumo-nav--sublist']/li/a[normalize-space("
        "text())='View all products']"
    )
    __explore_by_product_top_navbar_options = ("//h4[text()='Explore by "
                                               "product']/../following-sibling::ul/li/a")
    __explore_by_topic_top_navbar_options = ("//h4[text()='Explore by "
                                             "topic']/../following-sibling::ul/li/a")

    """
        Locators belonging to the 'Ask a Question' top-navbar section.
    """
    __ask_a_question_top_navbar = (
        "//li[@class='mzp-c-menu-category mzp-has-drop-down "
        "mzp-js-expandable']/a[contains(text(), 'Ask a Question')]"
    )
    __get_help_with_heading = "//h4[@class='mzp-c-menu-item-title' and text()='Get help with']"

    __ask_a_question_top_navbar_options = ("//a[text()='Ask a Question']/following-sibling::div"
                                           "//li/a")

    __aaq_firefox_browser_option = (
        "//div[@id='main-navigation']//h4[contains(text(), 'Ask a "
        "Question')]/../..//a[contains(text(),'Firefox desktop')]"
    )
    __browse_all_products_option = (
        "//div[@id='main-navigation']//a[normalize-space(text(" "))='View all']"
    )

    """
        Locators belonging to the 'Community Forums' top-navbar section.
    """
    __browse_by_product_top_navbar_header = ("//h4[@class='mzp-c-menu-item-title' and text("
                                             ")='Browse by product']")
    __browse_all_forum_threads_by_topic_top_navbar_header = ("//h4[@class='mzp-c-menu-item-title' "
                                                             "and text()='Browse all forum "
                                                             "threads by topic']")
    __community_forums_top_navbar_option = ("//a[@class='mzp-c-menu-title sumo-nav--link' "
                                            "and normalize-space(text())='Community Forums']")
    __browse_by_product_top_navbar_options = ("//h4[text()='Browse by "
                                              "product']/../following-sibling::ul/li/a")
    __browse_all_forum_threads_by_topics_top_navbar_options = ("//h4[text()='Browse all forum "
                                                               "threads by topic']/../"
                                                               "following-sibling::ul/li/a")

    """
        Locators belonging to the 'Contribute' top-navbar section.
    """
    __contribute_option = "//a[contains(text(),'Contribute')]"

    # Contributor Discussions
    __contributor_discussions_top_navbar_header = ("//h4[@class='mzp-c-menu-item-title' and text("
                                                   ")='Contributor discussions']")
    __contributor_discussions_options = ("//h4[text()='Contributor "
                                         "discussions']/../following-sibling::ul/li/a")
    __contributor_discussions_option = ("//h4[@class='mzp-c-menu-item-title' and text() "
                                        "='Contributor discussions']")
    __article_discussions_option = (
        "//div[@id='main-navigation']//a[normalize-space(text(" "))='Article discussions']"
    )
    # Contributor Tools
    __moderate_forum_content = (
        "//div[@id='main-navigation']//a[contains(text(), 'Moderate " "forum content')]"
    )
    __recent_revisions_option = (
        "//ul[@class='mzp-c-menu-item-list sumo-nav--sublist']//a["
        "normalize-space(text())='Recent revisions']"
    )
    __dashboards_option = (
        "//ul[@class='mzp-c-menu-item-list sumo-nav--sublist']//a["
        "normalize-space(text())='Knowledge base dashboards']"
    )
    __media_gallery_option = (
        "//ul[@class='mzp-c-menu-item-list sumo-nav--sublist']//a["
        "normalize-space(text())='Media gallery']"
    )

    """
        Locators belonging to the username section of the top-navbar.
    """
    __signin_signup_button = "//div[@id='profile-navigation']//a[contains(text(), 'Sign In/Up')]"
    __signed_in_username = "//span[@class='sumo-nav--username']"
    __signed_in_view_profile_option = "//h4[contains(text(), 'View Profile')]/parent::a"
    __signed_in_edit_profile_option = "//a[contains(text(),'Edit Profile')]"
    __signed_in_my_questions_option = (
        "//div[@class='sumo-nav--dropdown-thirds']//a[contains(" "text(), 'My Questions')]"
    )
    __signed_in_settings_option = "//h4[contains(text(), 'Settings')]/parent::a"
    __signed_in_inbox_option = "//h4[contains(text(), 'Inbox')]/parent::a"
    __sign_out_button = "//a[contains(text(), 'Sign Out')]"
    __unread_message_profile_notification = ("//div[@id='profile-navigation']//"
                                             "div[@class='avatar-container-message-alert']")
    __unread_message_count = "//span[@class='message-count-alert']"

    def __init__(self, page: Page):
        super().__init__(page)

    """
        Actions against the top-navbar logo.
    """
    def get_sumo_nav_logo(self) -> ElementHandle:
        return self._get_element_handle(self.__sumo_nav_logo)

    def click_on_sumo_nav_logo(self):
        self._click(self.__sumo_nav_logo)

    """
        Actions against the 'Explore Help Articles' top-navbar section.
    """
    def hover_over_explore_by_product_top_navbar_option(self):
        self._hover_over_element(self.__explore_help_articles_top_navbar_option)

    def get_all_explore_by_product_options_locators(self) -> list[Locator]:
        self.hover_over_explore_by_product_top_navbar_option()
        self.page.wait_for_selector(self.__explore_by_product_top_navbar_header)
        return self._get_elements_locators(self.__explore_by_product_top_navbar_options)

    def get_all_explore_by_topic_locators(self) -> list[Locator]:
        self.hover_over_explore_by_product_top_navbar_option()
        self.page.wait_for_selector(self.__explore_by_topic_top_navbar_header)
        return self._get_elements_locators(self.__explore_by_topic_top_navbar_options)

    def click_on_explore_our_help_articles_view_all_option(self):
        self._hover_over_element(self.__explore_help_articles_top_navbar_option)
        self._click(self.__explore_our_help_articles_view_all_option)
    """
        Actions against the 'Community Forums' top-navbar section.
    """
    def hover_over_community_forums_top_navbar_option(self):
        self._hover_over_element(self.__community_forums_top_navbar_option)

    def get_all_browse_by_product_options_locators(self) -> list[Locator]:
        self.hover_over_community_forums_top_navbar_option()
        self.page.wait_for_selector(self.__browse_by_product_top_navbar_header)
        return self._get_elements_locators(self.__browse_by_product_top_navbar_options)

    def get_all_browse_all_forum_threads_by_topic_locators(self) -> list[Locator]:
        self.hover_over_community_forums_top_navbar_option()
        self.page.wait_for_selector(self.__browse_all_forum_threads_by_topic_top_navbar_header)
        return self._get_elements_locators(
            self.__browse_all_forum_threads_by_topics_top_navbar_options)

    """
        Actions against the 'Ask a Question' top-navbar section.
    """
    def hover_over_ask_a_question_top_navbar(self):
        self._hover_over_element(self.__ask_a_question_top_navbar)

    def get_all_ask_a_question_locators(self) -> list[Locator]:
        self._hover_over_element(self.__ask_a_question_top_navbar)
        self.page.wait_for_selector(self.__get_help_with_heading)
        return self._get_elements_locators(self.__ask_a_question_top_navbar_options)

    def click_on_browse_all_products_option(self):
        self._hover_over_element(self.__ask_a_question_top_navbar)
        self._click(self.__browse_all_products_option)

    """
        Actions against the 'Contribute' top-navbar section.
    """
    def hover_over_contribute_top_navbar(self):
        self._hover_over_element(self.__contribute_option)

    def get_all_contributor_discussions_locators(self) -> list[Locator]:
        self.hover_over_contribute_top_navbar()
        self.page.wait_for_selector(self.__contributor_discussions_top_navbar_header)
        return self._get_elements_locators(self.__contributor_discussions_options)

    def click_on_contribute_top_navbar_option(self):
        self._click(self.__contribute_option)

    def click_on_community_discussions_top_navbar_option(self):
        self.hover_over_contribute_top_navbar()
        self._click(self.__contributor_discussions_option)

    def click_on_article_discussions_option(self):
        self._hover_over_element(self.__contribute_option)
        self._click(self.__article_discussions_option)

    # Contributor tools
    def click_on_moderate_forum_content_option(self):
        self.hover_over_contribute_top_navbar()
        self._click(self.__moderate_forum_content)

    def click_on_recent_revisions_option(self):
        self.hover_over_contribute_top_navbar()
        self._click(self.__recent_revisions_option)

    def click_on_dashboards_option(self):
        self.hover_over_contribute_top_navbar()
        self._click(self.__dashboards_option)

    def click_on_media_gallery_option(self):
        self.hover_over_contribute_top_navbar()
        self._click(self.__media_gallery_option)

    """
        Actions against the sign-in/sign-up top-navbar section.
    """
    def click_on_signin_signup_button(self):
        self._click(self.__signin_signup_button)

    def click_on_sign_out_button(self):
        self._hover_over_element(self.__signed_in_username)
        self._click(self.__sign_out_button)

    def sign_in_up_button_displayed_element(self) -> Locator:
        return self._get_element_locator(self.__signin_signup_button)

    def is_sign_in_up_button_displayed(self) -> bool:
        return self._is_element_visible(self.__signin_signup_button)

    """
        Actions against the user profile top-navbar section.
    """
    def click_on_view_profile_option(self):
        self._hover_over_element(self.__signed_in_username)
        self._click(self.__signed_in_view_profile_option)

    def click_on_edit_profile_option(self):
        self._hover_over_element(self.__signed_in_username)
        self._click(self.__signed_in_edit_profile_option)

    def click_on_settings_profile_option(self):
        self._hover_over_element(self.__signed_in_username)
        self._click(self.__signed_in_settings_option)

    def click_on_inbox_option(self):
        self._hover_over_element(self.__signed_in_username)
        self._click(self.__signed_in_inbox_option)

    def click_on_my_questions_profile_option(self):
        self._hover_over_element(self.__signed_in_username)
        self._click(self.__signed_in_my_questions_option)

    def get_text_of_logged_in_username(self) -> str:
        return self._get_text_of_element(self.__signed_in_username)

    def is_unread_message_notification_displayed(self) -> bool:
        return self._is_element_visible(self.__unread_message_profile_notification)

    def get_unread_message_notification_counter_value(self) -> int:
        return int(self._get_text_of_element(self.__unread_message_count))

    def is_unread_message_notification_counter_visible(self) -> bool:
        return self._is_element_visible(self.__unread_message_count)

    def mouse_over_profile_avatar(self):
        self._hover_over_element(self.__signed_in_username)

    """
        General actions against the top-navbar section.
    """
    def get_available_menu_titles(self) -> list[str]:
        return self._get_text_of_elements(self.__menu_titles)
