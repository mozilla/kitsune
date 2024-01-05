from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage


class TopNavbar(BasePage):
    __menu_titles = "//div[@id='main-navigation']//a[contains(@class,'mzp-c-menu-title')]"
    __sumo_nav_logo = "//div[@class='sumo-nav--logo']/a/img"

    # Get Help option
    __get_help_option = ("//li[@class='mzp-c-menu-category mzp-has-drop-down "
                         "mzp-js-expandable']/a[contains(text(), 'Get Help')]")

    # Sub menu items ask a Question section
    __ask_a_question_option = "//h4[contains(text(),'Ask a Question')]/parent::a"
    __aaq_firefox_browser_option = ("//div[@id='main-navigation']//h4[contains(text(), 'Ask a "
                                    "Question')]/../..//a[contains(text(),'Firefox Browser')]")
    __browse_all_products_option = "//div[@id='main-navigation']//a[text()='Browse All Products']"

    # Contribute Tools
    __contribute_option = "//a[contains(text(),'Contribute')]"

    # Contributor Tools
    __contributor_tools_option = "//a[contains(text(),'Contributor Tools')]"
    __moderate_forum_content = ("//div[@id='main-navigation']//a[@data-event-label='Moderate "
                                "Forum Content']")

    # Sign in button
    __signin_signup_button = "//div[@id='profile-navigation']//a[@data-event-label='Sign In']"

    # Signed in options
    __signed_in_username = "//span[@class='sumo-nav--username']"
    __signed_in_view_profile_option = "//h4[contains(text(), 'View Profile')]/parent::a"
    __signed_in_edit_profile_option = "//a[contains(text(),'Edit Profile')]"
    __signed_in_my_questions_option = ("//div[@class='sumo-nav--dropdown-thirds']//a[contains("
                                       "text(), 'My Questions')]")
    __signed_in_settings_option = "//h4[contains(text(), 'Settings')]/parent::a"
    __signed_in_inbox_option = "//h4[contains(text(), 'Inbox')]/parent::a"
    __sign_out_button = "//a[@data-event-label='Sign Out']"

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

    # Contributor tools
    def _click_on_moderate_forum_content_option(self):
        super()._hover_over_element(self.__contributor_tools_option)
        super()._click(self.__moderate_forum_content)

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
        super()._hover_over_element(self.__get_help_option)
        super()._click(self.__ask_a_question_option)

    def _click_on_ask_a_question_firefox_browser_option(self):
        super()._hover_over_element(self.__get_help_option)
        super()._click(self.__aaq_firefox_browser_option)

    def _click_on_browse_all_products_option(self):
        super()._hover_over_element(self.__get_help_option)
        super()._click(self.__browse_all_products_option)

    def _get_text_of_logged_in_username(self) -> str:
        return super()._get_text_of_element(self.__signed_in_username)

    def _sign_in_up_button_displayed_element(self) -> Locator:
        return super()._get_element_locator(self.__signin_signup_button)
