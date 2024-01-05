from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class ContributePage(BasePage):
    # Breadcrumbs
    __breadcrumbs = "//ol[@id='breadcrumbs']/li"
    __breadcrumb_homepage = "//ol[@id='breadcrumbs']/li[1]"

    # Page Hero
    __page_hero_main_header = "//div[contains(@class,'hero')]/div/h1"
    __page_hero_main_header_subtext = ("//div[contains(@class,"
                                       "'hero')]/div/h1/following-sibling::p[1]")
    __page_hero_need_help_header = "//div[contains(@class,'hero')]/div/h2"
    __page_hero_need_help_subtext = "//div[contains(@class,'hero')]/div/h1/following-sibling::p[2]"

    # Ways to contribute
    __way_to_contribute_header = "//nav/preceding-sibling::h2"
    __way_to_contribute_cards = ("//h2[contains(text(),'Pick a way to "
                                 "contribute')]/following-sibling::nav/ul/a")
    __way_to_contribute_card_titles = "//nav/ul/a/li/span"

    # About us
    __about_us_header = "//h2[contains(text(),'About us')]"
    __about_us_subtext = "//h2[contains(text(),'About us')]/following-sibling::p"

    # All page images
    __all_page_images = "//div[@id='svelte']//img"

    def __init__(self, page: Page):
        super().__init__(page)

    # Breadcrumbs
    def _get_breadcrumbs_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__breadcrumbs)

    def _click_on_home_breadcrumb(self):
        super()._click(self.__breadcrumb_homepage)

    # Page Hero
    def _get_page_hero_main_header_text(self) -> str:
        return super()._get_text_of_element(self.__page_hero_main_header)

    def _get_page_hero_main_subtext(self) -> str:
        return super()._get_text_of_element(self.__page_hero_main_header_subtext)

    def _get_page_hero_need_help_header_text(self) -> str:
        return super()._get_text_of_element(self.__page_hero_need_help_header)

    def _get_page_hero_need_help_subtext(self) -> str:
        return super()._get_text_of_element(self.__page_hero_need_help_subtext)

    # Page images
    def _get_all_page_links(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__all_page_images)

    # Way to contribute
    def _get_way_to_contribute_header_text(self) -> str:
        return super()._get_text_of_element(self.__way_to_contribute_header)

    def _get_way_to_contribute_card_titles_text(self) -> list[str]:
        return super()._get_text_of_elements(self.__way_to_contribute_card_titles)

    # About us
    def _get_about_us_header_text(self) -> str:
        return super()._get_text_of_element(self.__about_us_header)

    def _get_about_us_subtext(self) -> str:
        return super()._get_text_of_element(self.__about_us_subtext)

    # Contribute cards
    def _get_list_of_contribute_cards(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.__way_to_contribute_cards)

    def _click_on_way_to_contribute_card(self, way_to_contribute_card: ElementHandle):
        way_to_contribute_card.click()
