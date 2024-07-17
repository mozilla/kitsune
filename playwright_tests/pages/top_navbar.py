from playwright.sync_api import ElementHandle, Locator, Page

from playwright_tests.core.basepage import BasePage


class TopNavbar(BasePage):
    __menu_titles = "//div[@id='main-navigation']//a[contains(@class,'mzp-c-menu-title')]"
    __sumo_nav_logo = "//div[@class='sumo-nav--logo']/a/img"

    # Get Help option
    __ask_a_question_top_navbar = (
        "//li[@class='mzp-c-menu-category mzp-has-drop-down "
        "mzp-js-expandable']/a[contains(text(), 'Ask a Question')]"
    )

    # Explore our help articles locator.
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

    # Sub menu items ask a Question section
    __aaq_firefox_browser_option = (
        "//div[@id='main-navigation']//h4[contains(text(), 'Ask a "
        "Question')]/../..//a[contains(text(),'Firefox desktop')]"
    )
    __browse_all_products_option = (
        "//div[@id='main-navigation']//a[normalize-space(text(" "))='View all']"
    )

    # Contribute Tools
    __contribute_option = "//a[contains(text(),'Contribute')]"

    # Contributor Discussions
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

    # Sign in button
    __signin_signup_button = "//div[@id='profile-navigation']//a[contains(text(), 'Sign In/Up')]"

    # Signed in options
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

    # Support logo
    def _get_sumo_nav_logo(self) -> ElementHandle:
        return super()._get_element_handle(self.__sumo_nav_logo)

    def _click_on_sumo_nav_logo(self):
        super()._click(self.__sumo_nav_logo)

    def _get_available_menu_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__menu_titles)

    # Contribute Tools
    def _click_on_contribute_top_navbar_option(self):
        super()._click(self.__contribute_option)

    def _click_on_article_discussions_option(self):
        super()._hover_over_element(self.__contribute_option)
        super()._click(self.__article_discussions_option)

    # Contributor tools
    def _click_on_moderate_forum_content_option(self):
        super()._hover_over_element(self.__contribute_option)
        super()._click(self.__moderate_forum_content)

    def _click_on_recent_revisions_option(self):
        super()._hover_over_element(self.__contribute_option)
        super()._click(self.__recent_revisions_option)

    def _click_on_dashboards_option(self):
        super()._hover_over_element(self.__contribute_option)
        super()._click(self.__dashboards_option)

    def _click_on_media_gallery_option(self):
        super()._hover_over_element(self.__contribute_option)
        super()._click(self.__media_gallery_option)

    # Explore our Help Articles actions.
    def _click_on_explore_our_help_articles_view_all_option(self):
        super()._hover_over_element(self.__explore_help_articles_top_navbar_option)
        super()._click(self.__explore_our_help_articles_view_all_option)

    # Sign in option
    def _click_on_signin_signup_button(self):
        super()._click(self.__signin_signup_button)

    # Profile options
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

    def _click_on_sign_out_button(self):
        super()._hover_over_element(self.__signed_in_username)
        super()._click(self.__sign_out_button)

    def _click_on_my_questions_profile_option(self):
        super()._hover_over_element(self.__signed_in_username)
        super()._click(self.__signed_in_my_questions_option)

    def _click_on_ask_a_question_option(self):
        super()._hover_over_element(self.__ask_a_question_top_navbar)
        super()._click(self.__ask_a_question_option)

    def _click_on_ask_a_question_firefox_browser_option(self):
        super()._hover_over_element(self.__ask_a_question_top_navbar)
        super()._click(self.__aaq_firefox_browser_option)

    def _click_on_browse_all_products_option(self):
        super()._hover_over_element(self.__ask_a_question_top_navbar)
        super()._click(self.__browse_all_products_option)

    def _get_text_of_logged_in_username(self) -> str:
        return super()._get_text_of_element(self.__signed_in_username)

    def _sign_in_up_button_displayed_element(self) -> Locator:
        return super()._get_element_locator(self.__signin_signup_button)

    def is_sign_in_up_button_displayed(self) -> bool:
        return super()._is_element_visible(self.__signin_signup_button)
