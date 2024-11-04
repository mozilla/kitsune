from playwright.sync_api import ElementHandle, Locator, Page

from playwright_tests.core.basepage import BasePage


class TopNavbar(BasePage):
    # General page locators
    TOP_NAVBAR_GENERAL_PAGE_LOCATORS = {
        "menu_titles": "//div[@id='main-navigation']//a[contains(@class,'mzp-c-menu-title')]",
        "sumo_nav_logo": "//div[@class='sumo-nav--logo']/a/img"
    }
    # Locators belonging to the 'Explore Help Articles' top-navbar section".
    TOP_NAVBAR_EXPLORE_HELP_ARTICLES_LOCATORS = {
        "explore_by_topic_top_navbar_header": "//h4[@class='mzp-c-menu-item-title' and text()='"
                                              "Explore by topic']",
        "explore_by_product_top_navbar_header": "//h4[@class='mzp-c-menu-item-title' and text()="
                                                "'Explore by product']",
        "explore_help_articles_top_navbar_option": "//a[@class='mzp-c-menu-title sumo-nav--link' "
                                                   "and normalize-space(text())='Explore Help "
                                                   "Articles']",

        "explore_our_help_articles_view_all_option": "//ul[@class='mzp-c-menu-item-list sumo-nav"
                                                     "--sublist']/li/a[normalize-space(text())="
                                                     "'View all products']",

        "explore_by_product_top_navbar_options": "//h4[text()='Explore by product']/../following-"
                                                 "sibling::ul/li/a",
        "explore_by_topic_top_navbar_options": ("//h4[text()='Explore by topic']/../following-"
                                                "sibling::ul/li/a")
    }
    # Locators belonging to the 'Ask a Question' top-navbar section.
    TOP_NAVBAR_AAQ_LOCATORS = {
        "ask_a_question_top_navbar": "//li[@class='mzp-c-menu-category mzp-has-drop-down "
                                     "mzp-js-expandable']/a[contains(text(), 'Ask a Question')]",
        "get_help_with_heading": "//h4[@class='mzp-c-menu-item-title' and text()='Get help with']",

        "ask_a_question_top_navbar_options": "//a[text()='Ask a Question']/following-sibling::div/"
                                             "li/a",

        "aaq_firefox_browser_option": "//div[@id='main-navigation']//h4[contains(text(), 'Ask a "
                                      "Question')]/../..//a[contains(text(),'Firefox desktop')]",
        "browse_all_products_option": "//div[@id='main-navigation']//a[normalize-space(text(" "))="
                                      "'View all']"
    }
    # Locators belonging to the 'Community Forums' top-navbar section.
    TOP_NAVBAR_COMMUNITY_FORUMS_LOCATORS = {
        "browse_by_product_top_navbar_header": "//h4[@class='mzp-c-menu-item-title' and text()="
                                               "'Browse by product']",
        "browse_all_forum_threads_by_topic_top_navbar_header": "//h4[@class='mzp-c-menu-item-"
                                                               "title' and text()='Browse all "
                                                               "forum threads by topic']",
        "community_forums_top_navbar_option": "//a[@class='mzp-c-menu-title sumo-nav--link' and "
                                              "normalize-space(text())='Community Forums']",
        "browse_by_product_top_navbar_options": "//h4[text()='Browse by product']/../following-"
                                                "sibling::ul/li/a",
        "browse_all_forum_threads_by_topics_top_navbar_options": "//h4[text()='Browse all forum "
                                                                 "threads by topic']/../following-"
                                                                 "sibling::ul/li/a"
    }
    # Locators belonging to the 'Contribute' top-navbar section.
    TOP_NAVBAR_CONTRIBUTE_LOCATORS = {
        "contribute_option": "//a[contains(text(),'Contribute')]",
        "contributor_discussions_top_navbar_header": "//h4[@class='mzp-c-menu-item-title' and text"
                                                     "()='Contributor discussions']",
        "contributor_discussions_options": "//h4[text()='Contributor discussions']/../following-"
                                           "sibling::ul/li/a",
        "contributor_discussions_option": "//h4[@class='mzp-c-menu-item-title' and text() ='"
                                          "Contributor discussions']",
        "article_discussions_option": "//div[@id='main-navigation']//a[normalize-space(text(" "))="
                                      "'Article discussions']",
        "moderate_forum_content": "//div[@id='main-navigation']//a[contains(text(), 'Moderate "
                                  "forum content')]",

        "recent_revisions_option": "//ul[@class='mzp-c-menu-item-list sumo-nav--sublist']//a["
                                   "normalize-space(text())='Recent revisions']",
        "dashboards_option": "//ul[@class='mzp-c-menu-item-list sumo-nav--sublist']//a[normalize-"
                             "space(text())='Knowledge base dashboards']",
        "media_gallery_option": "//ul[@class='mzp-c-menu-item-list sumo-nav--sublist']//a["
                                "normalize-space(text())='Media gallery']",
        "guides_option": "//ul[@class='mzp-c-menu-item-list sumo-nav--sublist']//a[normalize-"
                         "space(text())='Guides']"
    }
    # Locators belonging to the 'Sign In/Up' top-navbar section.
    TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS = {
        "signin_signup_button": "//div[@id='profile-navigation']//a[contains(text(), "
                                "'Sign In/Up')]",
        "signed_in_username": "//span[@class='sumo-nav--username']",
        "signed_in_view_profile_option": "//h4[contains(text(), 'View Profile')]/parent::a",
        "signed_in_edit_profile_option": "//a[contains(text(),'Edit Profile')]",
        "signed_in_my_questions_option": "//div[@class='sumo-nav--dropdown-thirds']//a[contains("
                                         "text(), 'My Questions')]",
        "signed_in_settings_option": "//h4[contains(text(), 'Settings')]/parent::a",
        "signed_in_inbox_option": "//h4[contains(text(), 'Inbox')]/parent::a",
        "sign_out_button": "//a[contains(text(), 'Sign Out')]",
        "unread_message_profile_notification": "//div[@id='profile-navigation']//div[@class='"
                                               "avatar-container-message-alert']",
        "unread_message_count": "//span[@class='message-count-alert']"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    """
        Actions against the top-navbar logo.
    """
    def get_sumo_nav_logo(self) -> ElementHandle:
        """Get sumo nav logo element handle"""
        return self._get_element_handle(self.TOP_NAVBAR_GENERAL_PAGE_LOCATORS["sumo_nav_logo"])

    def click_on_sumo_nav_logo(self):
        """Click on the sumo nav logo"""
        self._click(self.TOP_NAVBAR_GENERAL_PAGE_LOCATORS["sumo_nav_logo"])

    """
        Actions against the 'Explore Help Articles' top-navbar section.
    """
    def hover_over_explore_by_product_top_navbar_option(self):
        """Hover over the 'Explore by product' top-navbar option"""
        self._hover_over_element(self.TOP_NAVBAR_EXPLORE_HELP_ARTICLES_LOCATORS
                                 ["explore_help_articles_top_navbar_option"])

    def get_all_explore_by_product_options_locators(self) -> list[Locator]:
        """Get all 'Explore by product' top-navbar options locators"""
        self.hover_over_explore_by_product_top_navbar_option()
        self.page.wait_for_selector(
            self.TOP_NAVBAR_EXPLORE_HELP_ARTICLES_LOCATORS["explore_by_product_top_navbar_header"])
        return self._get_elements_locators(self.TOP_NAVBAR_EXPLORE_HELP_ARTICLES_LOCATORS
                                           ["explore_by_product_top_navbar_options"])

    def get_all_explore_by_topic_locators(self) -> list[Locator]:
        """Get all 'Explore by topic' top-navbar options locators"""
        self.hover_over_explore_by_product_top_navbar_option()
        self.page.wait_for_selector(self.TOP_NAVBAR_EXPLORE_HELP_ARTICLES_LOCATORS
                                    ["explore_by_topic_top_navbar_header"])
        return self._get_elements_locators(self.TOP_NAVBAR_EXPLORE_HELP_ARTICLES_LOCATORS
                                           ["explore_by_topic_top_navbar_options"])

    def click_on_explore_our_help_articles_view_all_option(self):
        """Click on the 'View all products' option"""
        self._hover_over_element(self.TOP_NAVBAR_EXPLORE_HELP_ARTICLES_LOCATORS
                                 ["explore_help_articles_top_navbar_option"])
        self._click(self.TOP_NAVBAR_EXPLORE_HELP_ARTICLES_LOCATORS
                    ["explore_our_help_articles_view_all_option"])
    """
        Actions against the 'Community Forums' top-navbar section.
    """
    def hover_over_community_forums_top_navbar_option(self):
        """Hover over the 'Community Forums' top-navbar option"""
        self._hover_over_element(self.TOP_NAVBAR_COMMUNITY_FORUMS_LOCATORS
                                 ["community_forums_top_navbar_option"])

    def get_all_browse_by_product_options_locators(self) -> list[Locator]:
        """Get all 'Browse by product' top-navbar options locators"""
        self.hover_over_community_forums_top_navbar_option()
        self.page.wait_for_selector(self.TOP_NAVBAR_COMMUNITY_FORUMS_LOCATORS
                                    ["browse_by_product_top_navbar_header"])
        return self._get_elements_locators(self.TOP_NAVBAR_COMMUNITY_FORUMS_LOCATORS
                                           ["browse_by_product_top_navbar_options"])

    def get_all_browse_all_forum_threads_by_topic_locators(self) -> list[Locator]:
        """Get all 'Browse all forum threads by topic' top-navbar options locators"""
        self.hover_over_community_forums_top_navbar_option()
        self.page.wait_for_selector(self.TOP_NAVBAR_COMMUNITY_FORUMS_LOCATORS
                                    ["browse_all_forum_threads_by_topic_top_navbar_header"])
        return self._get_elements_locators(
            self.TOP_NAVBAR_COMMUNITY_FORUMS_LOCATORS
            ["browse_all_forum_threads_by_topics_top_navbar_options"])

    """
        Actions against the 'Ask a Question' top-navbar section.
    """
    def hover_over_ask_a_question_top_navbar(self):
        """Hover over the 'Ask a Question' top-navbar option"""
        self._hover_over_element(self.TOP_NAVBAR_AAQ_LOCATORS["ask_a_question_top_navbar"])

    def get_all_ask_a_question_locators(self) -> list[Locator]:
        """Get all 'Ask a Question' top-navbar options locators"""
        self._hover_over_element(self.TOP_NAVBAR_AAQ_LOCATORS["ask_a_question_top_navbar"])
        self.page.wait_for_selector(self.TOP_NAVBAR_AAQ_LOCATORS["get_help_with_heading"])
        return self._get_elements_locators(self.TOP_NAVBAR_AAQ_LOCATORS
                                           ["ask_a_question_top_navbar_options"])

    def click_on_browse_all_products_option(self):
        """Click on the 'Browse all products' option"""
        self._hover_over_element(self.TOP_NAVBAR_AAQ_LOCATORS["ask_a_question_top_navbar"])
        self._click(self.TOP_NAVBAR_AAQ_LOCATORS["browse_all_products_option"])

    """
        Actions against the 'Contribute' top-navbar section.
    """
    def hover_over_contribute_top_navbar(self):
        """Hover over the 'Contribute' top-navbar option"""
        self._hover_over_element(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["contribute_option"])

    def get_all_contributor_discussions_locators(self) -> list[Locator]:
        """Get all 'Contributor discussions' top-navbar options locators"""
        self.hover_over_contribute_top_navbar()
        self.page.wait_for_selector(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS
                                    ["contributor_discussions_top_navbar_header"])
        return self._get_elements_locators(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS
                                           ["contributor_discussions_options"])

    def click_on_contribute_top_navbar_option(self):
        """Click on the 'Contribute' top-navbar option"""
        self._click(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["contribute_option"])

    def click_on_community_discussions_top_navbar_option(self):
        """Click on the 'Contributor discussions' top-navbar option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["contributor_discussions_option"])

    def click_on_article_discussions_option(self):
        """Click on the 'Article discussions' option"""
        self._hover_over_element(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["contribute_option"])
        self._click(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["article_discussions_option"])

    # Contributor tools
    def click_on_moderate_forum_content_option(self):
        """Click on the 'Moderate forum content' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["moderate_forum_content"])

    def click_on_recent_revisions_option(self):
        """Click on the 'Recent revisions' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["recent_revisions_option"])

    def click_on_dashboards_option(self):
        """Click on the 'Knowledge base dashboards' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["dashboards_option"])

    def click_on_media_gallery_option(self):
        """Click on the 'Media gallery' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["media_gallery_option"])

    def click_on_guides_option(self):
        """Click on the 'Guides' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.TOP_NAVBAR_CONTRIBUTE_LOCATORS["guides_option"])

    """
        Actions against the sign-in/sign-up top-navbar section.
    """
    def click_on_signin_signup_button(self):
        """Click on the 'Sign In/Up' button"""
        self._click(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signin_signup_button"])

    def click_on_sign_out_button(self):
        """Click on the 'Sign Out' button"""
        self._hover_over_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_username"])
        self._click(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["sign_out_button"])

    def sign_in_up_button_displayed_element(self) -> Locator:
        """Get the 'Sign In/Up' button displayed element locator"""
        return self._get_element_locator(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS
                                         ["signin_signup_button"])

    def is_sign_in_up_button_displayed(self) -> bool:
        """Check if the 'Sign In/Up' button is displayed"""
        return self._is_element_visible(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS
                                        ["signin_signup_button"])

    """
        Actions against the user profile top-navbar section.
    """
    def click_on_view_profile_option(self):
        """Click on the 'View Profile' option"""
        self._hover_over_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_username"])
        self._click(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_view_profile_option"])
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def click_on_edit_profile_option(self):
        """Click on the 'Edit Profile' option"""
        self._hover_over_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_username"])
        self._click(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_edit_profile_option"])
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def click_on_settings_profile_option(self):
        """Click on the 'Settings' option"""
        self._hover_over_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_username"])
        self._click(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_settings_option"])
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def click_on_inbox_option(self):
        """Click on the 'Inbox' option"""
        self._hover_over_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_username"])
        self._click(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_inbox_option"])
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def click_on_my_questions_profile_option(self):
        """Click on the 'My Questions' option"""
        self._hover_over_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_username"])
        self._click(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_my_questions_option"])
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def get_text_of_logged_in_username(self) -> str:
        """Get the text of the logged in username"""
        return self._get_text_of_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS
                                         ["signed_in_username"])

    def is_unread_message_notification_displayed(self) -> bool:
        """Check if the unread message notification is displayed"""
        return self._is_element_visible(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS
                                        ["unread_message_profile_notification"])

    def get_unread_message_notification_counter_value(self) -> int:
        """Get the unread message notification counter value"""
        return int(self._get_text_of_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS
                                             ["unread_message_count"]))

    def is_unread_message_notification_counter_visible(self) -> bool:
        """Check if the unread message notification counter is visible"""
        return self._is_element_visible(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS
                                        ["unread_message_count"])

    def mouse_over_profile_avatar(self):
        """Mouse over the profile avatar"""
        self._hover_over_element(self.TOP_NAVBAR_SIGNIN_SIGNUP_LOCATORS["signed_in_username"])

    """
        General actions against the top-navbar section.
    """
    def get_available_menu_titles(self) -> list[str]:
        """Get the available menu titles"""
        return self._get_text_of_elements(self.TOP_NAVBAR_GENERAL_PAGE_LOCATORS["menu_titles"])
