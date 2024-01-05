from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class WaysToContributePages(BasePage):
    # Breadcrumbs
    __interactable_breadcrumbs = "//ol[@id='breadcrumbs']/li/a"
    __all_breadcrumbs = "//ol[@id='breadcrumbs']/li"

    # Page Content
    __hero_main_header = "//div[contains(@class,'hero')]/div/h1"
    __hero_second_header = "//div[contains(@class,'hero')]/div/h2"
    __hero_text = "//div[contains(@class,'hero')]/div/p"
    __all_page_images = "//div[@id='svelte']//img"

    # How to contribute section
    __how_to_contribute_header = "//section[@class='mzp-l-content']/h2"
    __all_how_to_contribute_option_links = "//section[@class='mzp-l-content']/div/ol/li/a"
    __start_answering_how_to_contribute_option_text = ("//section[@class='mzp-l-content']/div/ol"
                                                       "/li[4]")
    __first_fact_text = "//div[contains(@class,'fact')]/span[1]"
    __second_fact_text = "//div[contains(@class,'fact')]/span[2]"

    # Other ways to contribute section
    __other_ways_to_contribute_header = "//div[@id='svelte']/section[2]/h2"
    __other_ways_to_contribute_card_titles = "//div[@id='svelte']/section[2]//nav//span"
    __other_ways_to_contribute_card_list = "//div[@id='svelte']/section[2]//ul/a"

    def __init__(self, page: Page):
        super().__init__(page)

    # Breadcrumbs
    def _get_text_of_all_breadcrumbs(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_breadcrumbs)

    def _get_interactable_breadcrumbs(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__interactable_breadcrumbs)

    def _click_on_breadcrumb(self, element: ElementHandle):
        element.click()

    # Page content
    def _get_hero_main_header_text(self) -> str:
        return super()._get_text_of_element(self.__hero_main_header)

    def _get_hero_second_header(self) -> str:
        return super()._get_text_of_element(self.__hero_second_header)

    def _get_hero_text(self) -> str:
        return super()._get_text_of_element(self.__hero_text)

    def _get_all_page_image_links(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__all_page_images)

    # How to contribute section
    def _get_how_to_contribute_header_text(self) -> str:
        return super()._get_text_of_element(self.__how_to_contribute_header)

    def _get_how_to_contribute_link_options_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__all_how_to_contribute_option_links)

    def _get_how_to_contribute_option_four_text(self) -> str:
        return super()._get_text_of_element(self.__start_answering_how_to_contribute_option_text)

    def _get_first_fact_text(self) -> str:
        return super()._get_text_of_element(self.__first_fact_text)

    def _get_second_fact_text(self) -> str:
        return super()._get_text_of_element(self.__second_fact_text)

    # Other ways to contribute section
    def _get_other_ways_to_contribute_header(self) -> str:
        return super()._get_text_of_element(self.__other_ways_to_contribute_header)

    def _get_other_ways_to_contribute_card_title(self) -> list[str]:
        return super()._get_text_of_elements(self.__other_ways_to_contribute_card_titles)

    def _get_other_ways_to_contribute_card_list(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__other_ways_to_contribute_card_list)

    def _click_on_other_way_to_contribute_card(self, card_item: ElementHandle):
        card_item.click()
