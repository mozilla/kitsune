from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import TimeoutException
from selenium_tests.core.base_page import BasePage
import time


class TopNavbar(BasePage):
    __menu_titles = (
        By.XPATH,
        "//div[@id='main-navigation']//a[contains(@class,'mzp-c-menu-title')]",
    )

    __sumo_nav_logo = (By.XPATH, "//div[@class='sumo-nav--logo']/a/img")
    __get_help_option = (By.XPATH, "//a[contains(text(),'Get Help')]")
    __contribute_option = (By.XPATH, "//a[contains(text(),'Contribute')]")
    __signin_signup_button = (
        By.XPATH,
        "//div[@id='profile-navigation']//a[@data-event-label='Sign In']",
    )
    __signed_in_username = (By.XPATH, "//span[@class='sumo-nav--username']")

    # Sub menu items ask a Question section
    __ask_a_question_option = (By.XPATH, "//h4[contains(text(),'Ask a Question')]/parent::a")
    __aaq_firefox_browser_option = (
        By.XPATH,
        "//div[@id='main-navigation']//h4[contains(text(), 'Ask a "
        "Question')]/../..//a[contains(text(),'Firefox Browser')]",
    )

    __signed_in_view_profile_option = (
        By.XPATH,
        "//h4[contains(text(), 'View Profile')]/parent::a",
    )
    __signed_in_edit_profile_option = (By.XPATH, "//a[contains(text(),'Edit Profile')]")
    __signed_in_my_questions_option = (By.XPATH, "//a[contains(text(),'My Questions')]")
    __signed_in_settings_option = (By.XPATH, "//h4[contains(text(), 'Settings')]/parent::a")
    __signed_in_inbox_option = (By.XPATH, "//h4[contains(text(), 'Inbox')]/parent::a")
    __sign_out_button = (By.XPATH, "//a[@data-event-label='Sign Out']")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_available_menu_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__menu_titles)

    def get_sumo_nav_logo(self) -> WebElement:
        return super()._find_element(self.__sumo_nav_logo)

    def click_on_contribute_top_navbar_option(self):
        super()._click(self.__contribute_option)

    def click_on_signin_signup_button(self):
        super()._click(self.__signin_signup_button)

    def click_on_sumo_nav_logo(self):
        super()._click(self.__sumo_nav_logo)

    def click_on_view_profile_option(self, max_attempts=3, poll_interval=1):
        super()._press_home_keyboard_button()
        for attempt in range(max_attempts):
            try:
                super()._mouseover_element(self.__signed_in_username)
                super()._click(self.__signed_in_view_profile_option)
            except TimeoutException as err:
                print(err)
                time.sleep(poll_interval)

    def click_on_edit_profile_option(self, max_attempts=3, poll_interval=1):
        super()._press_home_keyboard_button()
        for attempt in range(max_attempts):
            try:
                super()._mouseover_element(self.__signed_in_username)
                super()._click(self.__signed_in_edit_profile_option)
            except TimeoutException as err:
                print(err)
                time.sleep(poll_interval)

    def click_on_settings_profile_option(self, max_attempts=3, poll_interval=1):
        super()._press_home_keyboard_button()
        for attempt in range(max_attempts):
            try:
                super()._mouseover_element(self.__signed_in_username)
                super()._click(self.__signed_in_settings_option)
            except TimeoutException as err:
                print(err)
                time.sleep(poll_interval)

    def click_on_inbox_option(self, max_attempts=3, poll_interval=1):
        super()._press_home_keyboard_button()
        for attempt in range(max_attempts):
            try:
                super()._mouseover_element(self.__signed_in_username)
                super()._click(self.__signed_in_inbox_option)
            except TimeoutException as err:
                print(err)
                time.sleep(poll_interval)

    def click_on_sign_out_button(self, max_attempts=3, poll_interval=1):
        super()._press_home_keyboard_button()
        for attempt in range(max_attempts):
            try:
                super()._mouseover_element(self.__signed_in_username)
                super()._click(self.__sign_out_button)
            except TimeoutException as err:
                print(err)
                time.sleep(poll_interval)

    def click_on_my_questions_profile_option(self, max_attempts=3, poll_interval=1):
        super()._press_home_keyboard_button()
        for attempt in range(max_attempts):
            try:
                super()._mouseover_element(self.__signed_in_username)
                super()._click(self.__signed_in_my_questions_option)
            except TimeoutException as err:
                print(err)
                time.sleep(poll_interval)

    def click_on_ask_a_question_firefox_browser_option(self, max_attempts=3, poll_interval=1):
        super()._press_home_keyboard_button()
        for attempt in range(max_attempts):
            try:
                super()._mouseover_element(self.__get_help_option)
                super()._click(self.__aaq_firefox_browser_option)
            except TimeoutException as err:
                print(err)
                time.sleep(poll_interval)

    def get_text_of_logged_in_username(self) -> str:
        return super()._get_text_of_element(self.__signed_in_username)

    def is_sign_in_up_button_displayed(self) -> bool:
        return super()._is_element_displayed(self.__signin_signup_button)
