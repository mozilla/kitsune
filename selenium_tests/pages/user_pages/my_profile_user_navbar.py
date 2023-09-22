from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium_tests.core.base_page import BasePage


class UserNavbar(BasePage):
    __my_profile_option = (By.XPATH, "//ul[@id='user-nav']//a[contains(text(), 'My profile')]")
    __edit_my_profile_option = (
        By.XPATH,
        "//ul[@id='user-nav']//a[contains(text(),'Edit my profile')]",
    )
    __edit_my_profile_settings_option = (
        By.XPATH,
        "//ul[@id='user-nav']//a[contains(text(),'Edit settings')]",
    )
    __edit_my_profile_contribution_areas_option = (
        By.XPATH,
        "//ul[@id='user-nav']//a[contains(text(),'Edit " "contribution areas')]",
    )
    __edit_my_profile_manage_watch_list_option = (
        By.XPATH,
        "//ul[@id='user-nav']//a[contains(text(),'Manage watch " "list')]",
    )
    __edit_my_profile_my_questions_option = (
        By.XPATH,
        "//ul[@id='user-nav']//a[contains(text(),'My questions')]",
    )

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def click_on_my_profile_option(self):
        super()._mouseover_element(self.__my_profile_option)
        super()._click(self.__my_profile_option)

    def click_on_edit_my_profile_option(self):
        super()._mouseover_element(self.__edit_my_profile_option)
        super()._click(self.__edit_my_profile_option)

    def click_on_edit_contribution_areas_option(self):
        super()._mouseover_element(self.__edit_my_profile_contribution_areas_option)
        super()._click(self.__edit_my_profile_contribution_areas_option)

    def click_on_my_questions_option(self):
        super()._mouseover_element(self.__edit_my_profile_my_questions_option)
        super()._click(self.__edit_my_profile_my_questions_option)
