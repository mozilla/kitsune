from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from selenium_tests.core.base_page import BasePage


class WaysToContributePages(BasePage):
    __interactable_breadcrumbs = (By.XPATH, "//ol[@id='breadcrumbs']/li/a")
    __all_breadcrumbs = (By.XPATH, "//ol[@id='breadcrumbs']/li")
    __hero_main_header = (By.XPATH, "//div[contains(@class,'hero')]/div/h1")
    __hero_second_header = (By.XPATH, "//div[contains(@class,'hero')]/div/h2")
    __hero_text = (By.XPATH, "//div[contains(@class,'hero')]/div/p")
    __how_to_contribute_header = (By.XPATH, "//section[@class='mzp-l-content']/h2")
    __all_how_to_contribute_option_links = (By.XPATH, "//section[@class='mzp-l-content']/div/ol/li/a")
    __start_answering_how_to_contribute_option_text = (By.XPATH, "//section[@class='mzp-l-content']/div/ol/li[4]")
    __first_fact_text = (By.XPATH, "//div[contains(@class,'fact')]/span[1]")
    __second_fact_text = (By.XPATH, "//div[contains(@class,'fact')]/span[2]")
    __other_ways_to_contribute_header = (By.XPATH, "//div[@id='svelte']/section[2]/h2")
    __other_ways_to_contribute_card_titles = (By.XPATH, "//div[@id='svelte']/section[2]//nav//span")
    __other_ways_to_contribute_card_list = (By.XPATH, "//div[@id='svelte']/section[2]//ul/a")
    __all_page_images = (By.XPATH, "//div[@id='svelte']//img")

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def get_text_of_all_breadcrumbs(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_breadcrumbs)

    def get_all_interactable_breadcrumbs(self) -> list[WebElement]:
        return super()._find_elements(self.__interactable_breadcrumbs)

    def click_on_breadcrumb(self, element: WebElement):
        super()._click_on_web_element(element)

    def get_hero_main_header_text(self) -> str:
        return super()._get_text_of_element(self.__hero_main_header)

    def get_hero_second_header_text(self) -> str:
        return super()._get_text_of_element(self.__hero_second_header)

    def get_hero_text(self) -> str:
        return super()._get_text_of_element(self.__hero_text)

    def get_how_to_contribute_header_text(self) -> str:
        return super()._get_text_of_element(self.__how_to_contribute_header)

    def get_how_to_contribute_link_options_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_how_to_contribute_option_links)

    def get_how_to_contribute_option_four_text(self) -> str:
        return super()._get_text_of_element(self.__start_answering_how_to_contribute_option_text)

    def get_first_fact_text(self) -> str:
        return super()._get_text_of_element(self.__first_fact_text)

    def get_second_fact_text(self) -> str:
        return super()._get_text_of_element(self.__second_fact_text)

    def get_other_ways_to_contribute_header_text(self) -> str:
        return super()._get_text_of_element(self.__other_ways_to_contribute_header)

    def get_other_ways_to_contribute_card_titles_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__other_ways_to_contribute_card_titles)

    def get_all_page_image_links(self) -> list[WebElement]:
        return super()._find_elements(self.__all_page_images)

    def get_all_other_ways_to_contribute_card_list(self) -> list[WebElement]:
        return super()._find_elements(self.__other_ways_to_contribute_card_list)

    def click_on_other_way_to_contribute_card(self, card_item: WebElement):
        super()._click_on_web_element(card_item)
