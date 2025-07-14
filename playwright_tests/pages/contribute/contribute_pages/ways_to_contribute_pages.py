from playwright.sync_api import ElementHandle, Page

from playwright_tests.core.basepage import BasePage


class WaysToContributePages(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Breadcrumbs
        self.interactable_breadcrumbs = page.locator("ol#breadcrumbs li a")
        self.all_breadcrumbs = page.locator("ol#breadcrumbs li")

        # Page Content
        self.hero_main_header = page.locator("div[class*='hero'] div h1")
        self.hero_second_header = page.locator("div[class*='hero'] div h2")
        self.hero_text = page.locator("div[class*='hero'] div p")
        self.all_page_images = page.locator("div#svelte img")

        # How to contribute_messages section
        self.how_to_contribute_header = page.locator("section[class='mzp-l-content'] > h2")
        self.all_how_to_contribute_option_links = page.locator("section.mzp-l-content div ol li a")
        self.start_answering_how_to_contribute_option_text = page.locator(
            "//section[@class='mzp-l-content']/div/ol/li[4]")
        self.first_fact_text = page.locator("//div[contains(@class,'fact')]/span[1]")
        self.second_fact_text = page.locator("//div[contains(@class,'fact')]/span[2]")

        # Other ways to contribute_messages section
        self.other_ways_to_contribute_header = page.locator("//div[@id='svelte']/section[2]/h2")
        self.other_ways_to_contribute_card_titles = page.locator(
            "//div[@id='svelte']/section[2]//nav//span")
        self.other_ways_to_contribute_card_list = page.locator("//div[@id='svelte']/section[2]//"
                                                               "ul/a")

    # Breadcrumbs
    def get_text_of_all_breadcrumbs(self) -> list[str]:
        return self._get_text_of_elements(self.all_breadcrumbs)

    def get_interactable_breadcrumbs(self) -> list[ElementHandle]:
        return self._get_element_handles(self.interactable_breadcrumbs)

    def click_on_breadcrumb(self, element: ElementHandle):
        element.click()

    # Page content
    def get_hero_main_header_text(self) -> str:
        return self._get_text_of_element(self.hero_main_header)

    def get_hero_second_header(self) -> str:
        return self._get_text_of_element(self.hero_second_header)

    def get_hero_text(self) -> str:
        return self._get_text_of_element(self.hero_text)

    def get_all_page_image_links(self) -> list[ElementHandle]:
        return self._get_element_handles(self.all_page_images)

    # How to contribute_messages section
    def get_how_to_contribute_header_text(self) -> str:
        return self._get_text_of_element(self.how_to_contribute_header)

    def get_how_to_contribute_link_options(self) -> list[str]:
        return self._get_text_of_elements(self.all_how_to_contribute_option_links)

    def get_how_to_contribute_option_four(self) -> str:
        return self._get_text_of_element(self.start_answering_how_to_contribute_option_text)

    def get_first_fact_text(self) -> str:
        return self._get_text_of_element(self.first_fact_text)

    def get_second_fact_text(self) -> str:
        return self._get_text_of_element(self.second_fact_text)

    # Other ways to contribute_messages section
    def get_other_ways_to_contribute_header(self) -> str:
        return self._get_text_of_element(self.other_ways_to_contribute_header)

    def get_other_ways_to_contribute_cards(self) -> list[str]:
        return self._get_text_of_elements(self.other_ways_to_contribute_card_titles)

    def get_other_ways_to_contribute_card_list(self) -> list[ElementHandle]:
        return self._get_element_handles(self.other_ways_to_contribute_card_list)

    def click_on_other_way_to_contribute_card(self, card_item: ElementHandle):
        card_item.click()
