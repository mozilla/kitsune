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

    def __init__(self, page: Page):
        super().__init__(page)

    """
        Actions against the top-navbar logo.
    """
    def _get_sumo_nav_logo(self) -> ElementHandle:
        return super()._get_element_handle(self.__sumo_nav_logo)

    def _click_on_sumo_nav_logo(self):
        super()._click(self.__sumo_nav_logo)

    """
        Actions against the 'Explore Help Articles' top-navbar section.
    """
    def _hover_over_explore_by_product_top_navbar_option(self):
        super()._hover_over_element(self.__explore_help_articles_top_navbar_option)

    def _get_all_explore_by_product_options_locators(self) -> list[Locator]:
        self._hover_over_explore_by_product_top_navbar_option()
        self.page.wait_for_selector(self.__explore_by_product_top_navbar_header)
        return super()._get_elements_locators(self.__explore_by_product_top_navbar_options)

    def _get_all_explore_by_topic_locators(self) -> list[Locator]:
        self._hover_over_explore_by_product_top_navbar_option()
        self.page.wait_for_selector(self.__explore_by_topic_top_navbar_header)
        return super()._get_elements_locators(self.__explore_by_topic_top_navbar_options)

    def _click_on_explore_our_help_articles_view_all_option(self):
        super()._hover_over_element(self.__explore_help_articles_top_navbar_option)
        super()._click(self.__explore_our_help_articles_view_all_option)
    """
        Actions against the 'Community Forums' top-navbar section.
    """
    def _hover_over_community_forums_top_navbar_option(self):
        super()._hover_over_element(self.__community_forums_top_navbar_option)

    def _get_all_browse_by_product_options_locators(self) -> list[Locator]:
        self._hover_over_community_forums_top_navbar_option()
        self.page.wait_for_selector(self.__browse_by_product_top_navbar_header)
        return super()._get_elements_locators(self.__browse_by_product_top_navbar_options)

    def _get_all_browse_all_forum_threads_by_topic_locators(self) -> list[Locator]:
        self._hover_over_community_forums_top_navbar_option()
        self.page.wait_for_selector(self.__browse_all_forum_threads_by_topic_top_navbar_header)
        return super()._get_elements_locators(
            self.__browse_all_forum_threads_by_topics_top_navbar_options)

    """
        Actions against the 'Ask a Question' top-navbar section.
    """
    def _hover_over_ask_a_question_top_navbar(self):
        super()._hover_over_element(self.__ask_a_question_top_navbar)

    def _get_all_ask_a_question_locators(self) -> list[Locator]:
        super()._hover_over_element(self.__ask_a_question_top_navbar)
        self.page.wait_for_selector(self.__get_help_with_heading)
        return super()._get_elements_locators(self.__ask_a_question_top_navbar_options)

    def _click_on_browse_all_products_option(self):
        super()._hover_over_element(self.__ask_a_question_top_navbar)
        super()._click(self.__browse_all_products_option)

    """
        Actions against the 'Contribute' top-navbar section.
    """
    def _hover_over_contribute_top_navbar(self):
        super()._hover_over_element(self.__contribute_option)

    def _get_all_contributor_discussions_locators(self) -> list[Locator]:
        self._hover_over_contribute_top_navbar()
        self.page.wait_for_selector(self.__contributor_discussions_top_navbar_header)
        return super()._get_elements_locators(self.__contributor_discussions_options)

    def _click_on_contribute_top_navbar_option(self):
        super()._click(self.__contribute_option)

    def _click_on_community_discussions_top_navbar_option(self):
        self._hover_over_contribute_top_navbar()
        super()._click(self.__contributor_discussions_option)

    def _click_on_article_discussions_option(self):
        super()._hover_over_element(self.__contribute_option)
        super()._click(self.__article_discussions_option)

    # Contributor tools
    def _click_on_moderate_forum_content_option(self):
        self._hover_over_contribute_top_navbar()
        super()._click(self.__moderate_forum_content)

    def _click_on_recent_revisions_option(self):
        self._hover_over_contribute_top_navbar()
        super()._click(self.__recent_revisions_option)

    def _click_on_dashboards_option(self):
        self._hover_over_contribute_top_navbar()
        super()._click(self.__dashboards_option)

    def _click_on_media_gallery_option(self):
        self._hover_over_contribute_top_navbar()
        super()._click(self.__media_gallery_option)

    """
        Actions against the sign-in/sign-up top-navbar section.
    """
    def _click_on_signin_signup_button(self):
        super()._click(self.__signin_signup_button)

    def _click_on_sign_out_button(self):
        super()._hover_over_element(self.__signed_in_username)
        super()._click(self.__sign_out_button)

    def _sign_in_up_button_displayed_element(self) -> Locator:
        return super()._get_element_locator(self.__signin_signup_button)

    def is_sign_in_up_button_displayed(self) -> bool:
        return super()._is_element_visible(self.__signin_signup_button)

    """
        Actions against the user profile top-navbar section.
    """
    def _click_on_view_profile_option(self):
        super()._hover_over_element(self.__signed_in_username)
        super()._click(self.__signed_in_view_profile_option)

    def _click_on_edit_profile_option(self):
        super()._hover_over_element(self.__signed_in_username)
        super()._click(self.__signed_in_edit_profile_option)

    def _click_on_settings_profile_option(self):
        super()._hover_over_element(self.__signed_in_username)
        super()._click(self.__signed_in_settings_option)

    def _click_on_inbox_option(self):
        super()._hover_over_element(self.__signed_in_username)
        super()._click(self.__signed_in_inbox_option)

    def _click_on_my_questions_profile_option(self):
        super()._hover_over_element(self.__signed_in_username)
        super()._click(self.__signed_in_my_questions_option)

    def _get_text_of_logged_in_username(self) -> str:
        return super()._get_text_of_element(self.__signed_in_username)

    """
        General actions against the top-navbar section.
    """
    def _get_available_menu_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__menu_titles)
