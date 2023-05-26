from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from selenium_tests.core.base_page import BasePage


class ContributePage(BasePage):
    __breadcrumbs = (By.XPATH, "//ol[@id='breadcrumbs']/li")
    __breadcrumb_homepage = (By.XPATH, "//ol[@id='breadcrumbs']/li[1]")
    __page_hero_main_header = (By.XPATH, "//div[contains(@class,'hero')]/div/h1")
    __page_hero_main_header_subtext = (
        By.XPATH,
        "//div[contains(@class,'hero')]/div/h1/following-sibling::p[1]",
    )
    __page_hero_need_help_header = (By.XPATH, "//div[contains(@class,'hero')]/div/h2")
    __page_hero_need_help_subtext = (
        By.XPATH,
        "//div[contains(@class,'hero')]/div/h1/following-sibling::p[2]",
    )
    __way_to_contribute_header = (By.XPATH, "//nav/preceding-sibling::h2")
    __way_to_contribute_cards = (
        By.XPATH,
        "//h2[contains(text(),'Pick a way to " "contribute')]/following-sibling::nav/ul/a",
    )
    __way_to_contribute_card_titles = (By.XPATH, "//nav/ul/a/li/span")
    __about_us_header = (By.XPATH, "//h2[contains(text(),'About us')]")
    __about_us_subtext = (By.XPATH, "//h2[contains(text(),'About us')]/following-sibling::p")
    __all_page_images = (By.XPATH, "//div[@id='svelte']//img")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def navigate_back(self):
        super().navigate_back()

    def get_breadcrumbs_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__breadcrumbs)

    def get_all_page_links(self) -> list[WebElement]:
        return super()._find_elements(self.__all_page_images)

    def get_page_hero_main_header_text(self) -> str:
        return super()._get_text_of_element(self.__page_hero_main_header)

    def get_page_hero_main_subtext(self) -> str:
        return super()._get_text_of_element(self.__page_hero_main_header_subtext)

    def get_page_hero_need_help_header_text(self) -> str:
        return super()._get_text_of_element(self.__page_hero_need_help_header)

    def get_page_hero_need_help_subtext(self) -> str:
        return super()._get_text_of_element(self.__page_hero_need_help_subtext)

    def get_way_to_contribute_header_text(self) -> str:
        return super()._get_text_of_element(self.__way_to_contribute_header)

    def get_way_to_contribute_card_titles_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__way_to_contribute_card_titles)

    def get_about_us_header_text(self) -> str:
        return super()._get_text_of_element(self.__about_us_header)

    def get_about_us_subtext(self) -> str:
        return super()._get_text_of_element(self.__about_us_subtext)

    def get_list_of_contribute_cards(self) -> list[WebElement]:
        return super()._find_elements(self.__way_to_contribute_cards)

    def click_on_way_to_contribute_card(self, way_to_contribute_card):
        super()._click_on_web_element(way_to_contribute_card)

    def click_on_home_breadcrumb(self):
        super()._click(self.__breadcrumb_homepage)
