from playwright.sync_api import ElementHandle, Locator, Page
from playwright_tests.core.basepage import BasePage
from playwright_tests.pages.contribute.contributor_tools_pages.recent_revisions_page import \
    RecentRevisions


class TopNavbar(BasePage):
    def __init__(self, page: Page):
        self.recent_revisions = RecentRevisions(page)
        super().__init__(page)

        """General page locators."""
        self.menu_titles = page.locator("div#main-navigation a.mzp-c-menu-title")
        self.sumo_nav_logo = page.locator(
            "div.sumo-nav--logo").get_by_role("link").get_by_role("img")

        """Locators belonging to the 'Explore Help Articles' top-navbar section."""
        self.explore_by_topic_top_navbar_header = page.locator(
            "h4.mzp-c-menu-item-title").filter(has_text="Explore by topic")
        self.explore_by_product_top_navbar_header = page.locator(
            "h4.mzp-c-menu-item-title").filter(has_text="Explore by product")
        self.explore_help_articles_top_navbar_option = page.locator(
            "a[class='mzp-c-menu-title sumo-nav--link']").filter(has_text="Explore Help Articles")
        self.explore_our_help_articles_view_all_option = page.locator(
            "ul[class='mzp-c-menu-item-list sumo-nav--sublist'] li"
        ).get_by_role("link", name="View all products", exact=True)
        self.explore_by_product_top_navbar_options = page.locator(
            "//h4[text()='Explore by product']/../following-sibling::ul/li/a")
        self.explore_by_topic_top_navbar_options = page.locator(
            "//h4[text()='Explore by topic']/../following-sibling::ul/li/a")

        """Locators belonging to the 'Ask a Question' top-navbar section."""
        self.ask_a_question_top_navbar = page.locator(
            "li[class='mzp-c-menu-category mzp-has-drop-down mzp-js-expandable']").filter(
            has_text="Ask a Question")
        self.get_help_with_heading = page.locator(
            "h4[class='mzp-c-menu-item-title']").filter(has_text="Get help with")
        self.ask_a_question_top_navbar_options = page.get_by_role(
            "link", name="Ask a Question", exact=True).locator("+ div li a")
        self.aaq_firefox_browser_option = page.get_by_role(
            "link", name="Ask a Question", exact=True).locator("+ div li").get_by_role(
            "link").filter(has_text="Firefox desktop")
        self.browse_all_products_option = page.locator(
            "div#main-navigation").get_by_role("link", name="View all", exact=True)

        """Locators belonging to the 'Community Forums' top-navbar section."""
        self.browse_by_product_top_navbar_header = page.locator(
            "h4.mzp-c-menu-item-title").filter(has_text="Browse by product")
        self.browse_all_forum_threads_by_topic_top_navbar_header = page.locator(
            "h4.mzp-c-menu-item-title").filter(has_text="Browse all forum threads by topic")
        self.community_forums_top_navbar_option = page.locator(
            "a[class='mzp-c-menu-title sumo-nav--link']").filter(has_text="Community Forums")
        self.browse_by_product_top_navbar_options = page.locator(
            "//h4[text()='Browse by product']/../following-sibling::ul/li/a")
        self.browse_all_forum_threads_by_topics_top_navbar_options = page.locator(
            "//h4[text()='Browse all forum threads by topic']/../following-sibling::ul/li/a")
        self.firefox_desktop_option = page.locator("//a[text()='Firefox desktop']")
        self.view_all_forums = page.locator("//a[normalize-space(text())='View all forums']")

        """Locators belonging to the 'Contribute' top-navbar section."""
        self.contribute_option = page.get_by_role("link").filter(has_text="Contribute")
        self.contributor_discussions_top_navbar_header = page.locator(
            "h4.mzp-c-menu-item-title").filter(has_text="Contributor discussions")
        self.contributor_discussions_options = page.locator(
            "//h4[text()='Contributor discussions']/../following-sibling::ul/li/a")
        self.contributor_discussions_option = page.locator(
            "h4.mzp-c-menu-item-title").filter(has_text="Contributor discussions")
        self.article_discussions_option = page.locator(
            "div#main-navigation").get_by_role("link", name="Article discussions", exact=True)
        self.moderate_forum_content = page.locator(
            "div#main-navigation").get_by_role("link").filter(has_text="Moderate forum content")
        self.recent_revisions_option = page.locator(
            "ul[class='mzp-c-menu-item-list sumo-nav--sublist']").get_by_role(
            "link").filter(has_text="Recent revisions")
        self.dashboards_option = page.locator(
            "ul[class='mzp-c-menu-item-list sumo-nav--sublist']").get_by_role("link").filter(
            has_text="Knowledge base dashboards")
        self.media_gallery_option = page.locator(
            "ul[class='mzp-c-menu-item-list sumo-nav--sublist']").get_by_role("link").filter(
            has_text="Media gallery")
        self.guides_option = page.locator(
            "ul[class='mzp-c-menu-item-list sumo-nav--sublist']").get_by_role("link").filter(
            has_text="Guides")
        self.community_hub_option = page.locator(
            "ul[class='mzp-c-menu-item-list sumo-nav--sublist']").get_by_role("link").filter(
            has_text="Community hub")

        """Locators belonging to the 'Sign in/up' top-navbar section."""
        self.signin_signup_button = page.locator("div#profile-navigation").get_by_role(
            "link").filter(has_text="Sign In/Up")
        self.signed_in_username = page.locator("span.sumo-nav--username")
        self.signed_in_view_profile_option = page.locator(
            "//h4[contains(text(), 'View Profile')]/parent::a")
        self.signed_in_edit_profile_option = page.get_by_role("link").filter(
            has_text="Edit Profile")
        self.signed_in_my_questions_option = page.locator(
            "div.sumo-nav--dropdown-thirds").get_by_role("link").filter(has_text="My Questions")
        self.signed_in_settings_option = page.locator(
            "//h4[contains(text(), 'Settings')]/parent::a")
        self.signed_in_inbox_option = page.locator("//h4[contains(text(), 'Inbox')]/parent::a")
        self.sign_out_button = page.locator("div#mzp-c-menu-panel-profile").get_by_role(
            "link").get_by_text("Sign Out")
        self.unread_message_profile_notification = page.locator(
            "div#profile-navigation div.avatar-container-message-alert")
        self.unread_message_count = page.locator("span.message-count-alert")

    """Actions against the top-navbar logo."""
    def get_sumo_nav_logo(self) -> ElementHandle:
        """Get sumo nav logo element handle"""
        return self._get_element_handle(self.sumo_nav_logo)

    def click_on_sumo_nav_logo(self):
        """Click on the sumo nav logo"""
        self._click(self.sumo_nav_logo)

    """Actions against the 'Explore Help Articles' top-navbar section."""
    def hover_over_explore_by_product_top_navbar_option(self):
        """Hover over the 'Explore by product' top-navbar option"""
        self._hover_over_element(self.explore_help_articles_top_navbar_option)
        self._wait_for_locator(self.explore_by_product_top_navbar_header)

    def get_all_explore_by_product_options_locators(self) -> list[Locator]:
        """Get all 'Explore by product' top-navbar options locators"""
        self.hover_over_explore_by_product_top_navbar_option()
        return self.explore_by_product_top_navbar_options.all()

    def get_all_explore_by_topic_locators(self) -> list[Locator]:
        """Get all 'Explore by topic' top-navbar options locators"""
        self.hover_over_explore_by_product_top_navbar_option()
        return self.explore_by_topic_top_navbar_options.all()

    def click_on_explore_our_help_articles_view_all_option(self):
        """Click on the 'View all products' option"""
        self.hover_over_explore_by_product_top_navbar_option()
        self._click(self.explore_our_help_articles_view_all_option)

    """Actions against the 'Community Forums' top-navbar section."""
    def hover_over_community_forums_top_navbar_option(self):
        """Hover over the 'Community Forums' top-navbar option"""
        self._hover_over_element(self.community_forums_top_navbar_option)
        self._wait_for_locator(self.browse_by_product_top_navbar_header)

    def get_all_browse_by_product_options_locators(self) -> list[Locator]:
        """Get all 'Browse by product' top-navbar options locators"""
        self.hover_over_community_forums_top_navbar_option()
        return self.browse_by_product_top_navbar_options.all()

    def get_all_browse_all_forum_threads_by_topic_locators(self) -> list[Locator]:
        """Get all 'Browse all forum threads by topic' top-navbar options locators"""
        self.hover_over_community_forums_top_navbar_option()
        return self.browse_all_forum_threads_by_topics_top_navbar_options.all()

    def click_on_firefox_desktop_option(self):
        """Click on the 'Firefox desktop' option from the 'Browse by product' section."""
        self.hover_over_community_forums_top_navbar_option()
        self._click(self.firefox_desktop_option)

    def click_on_view_all_forums_option(self):
        """Click on the 'View all forums' option from the 'Browse by product' section."""
        self.hover_over_community_forums_top_navbar_option()
        self._click(self.view_all_forums)

    """Actions against the 'Ask a Question' top-navbar section."""
    def hover_over_ask_a_question_top_navbar(self):
        """Hover over the 'Ask a Question' top-navbar option"""
        self._hover_over_element(self.ask_a_question_top_navbar)
        self._wait_for_locator(self.get_help_with_heading)

    def get_all_ask_a_question_locators(self) -> list[Locator]:
        """Get all 'Ask a Question' top-navbar options locators"""
        self.hover_over_ask_a_question_top_navbar()
        return self.ask_a_question_top_navbar_options.all()

    def click_on_browse_all_products_option(self):
        """Click on the 'Browse all products' option"""
        self.hover_over_ask_a_question_top_navbar()
        self._click(self.browse_all_products_option)

    """Actions against the 'Contribute' top-navbar section."""
    def hover_over_contribute_top_navbar(self):
        """Hover over the 'Contribute' top-navbar option"""
        self._hover_over_element(self.contribute_option)
        self._wait_for_locator(self.contributor_discussions_top_navbar_header)

    def get_all_contributor_discussions_locators(self) -> list[Locator]:
        """Get all 'Contributor discussions' top-navbar options locators"""
        self.hover_over_contribute_top_navbar()
        return self.contributor_discussions_options.all()

    def click_on_contribute_top_navbar_option(self):
        """Click on the 'Contribute' top-navbar option"""
        self._click(self.contribute_option)

    def click_on_contributor_discussions_top_navbar_option(self):
        """Click on the 'Contributor discussions' top-navbar option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.contributor_discussions_option)

    def click_on_article_discussions_option(self):
        """Click on the 'Article discussions' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.article_discussions_option)

    """Actions against the Contributor Tools."""
    def click_on_moderate_forum_content_option(self):
        """Click on the 'Moderate forum content' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.moderate_forum_content)

    def click_on_recent_revisions_option(self):
        """Click on the 'Recent revisions' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.recent_revisions_option)
        self._wait_for_locator(self.recent_revisions.revisions_table, 5000)

    def click_on_dashboards_option(self):
        """Click on the 'Knowledge base dashboards' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.dashboards_option)

    def click_on_media_gallery_option(self):
        """Click on the 'Media gallery' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.media_gallery_option)

    def click_on_guides_option(self):
        """Click on the 'Guides' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.guides_option)

    def click_on_community_hub_option(self):
        """Click on the 'Community hub' option"""
        self.hover_over_contribute_top_navbar()
        self._click(self.community_hub_option)

    """Actions against the sign-in/sign-up top-navbar section."""
    def click_on_signin_signup_button(self):
        """Click on the 'Sign In/Up' button"""
        self._click(self.signin_signup_button)

    def mouse_over_profile_avatar(self):
        """Mouse over the profile avatar"""
        self._hover_over_element(self.signed_in_username)
        self._wait_for_locator(self.sign_out_button)

    def click_on_sign_out_button(self):
        """Click on the 'Sign Out' button"""
        self.mouse_over_profile_avatar()
        self._click(self.sign_out_button)

    """Actions against the user profile top-navbar section."""
    def click_on_view_profile_option(self):
        """Click on the 'View Profile' option"""
        self.mouse_over_profile_avatar()
        self._click(self.signed_in_view_profile_option)
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def click_on_edit_profile_option(self):
        """Click on the 'Edit Profile' option"""
        self.mouse_over_profile_avatar()
        self._click(self.signed_in_edit_profile_option)
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def click_on_settings_profile_option(self):
        """Click on the 'Settings' option"""
        self.mouse_over_profile_avatar()
        self._click(self.signed_in_settings_option)
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def click_on_inbox_option(self):
        """Click on the 'Inbox' option"""
        self.mouse_over_profile_avatar()
        self._click(self.signed_in_inbox_option)
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def click_on_my_questions_profile_option(self):
        """Click on the 'My Questions' option"""
        self.mouse_over_profile_avatar()
        self._click(self.signed_in_my_questions_option)
        # Sometimes the top-navbar is not hidden after clicking on the 'Settings' option. This
        # action is to move the mouse to the top-left corner of the page to hide the top-navbar.
        self._move_mouse_to_location(0, 0)

    def get_text_of_logged_in_username(self) -> str:
        """Get the text of the logged in username"""
        return self._get_text_of_element(self.signed_in_username)

    def get_unread_message_notification_counter_value(self) -> int:
        """Get the unread message notification counter value"""
        return int(self._get_text_of_element(self.unread_message_count))

    """General actions against the top-navbar section."""
    def get_available_menu_titles(self) -> list[str]:
        """Get the available menu titles"""
        return self._get_text_of_elements(self.menu_titles)
