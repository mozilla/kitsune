from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class ContributePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Breadcrumbs
        self.breadcrumbs = page.locator("ol#breadcrumbs li")
        self.breadcrumb_homepage = page.locator("ol#breadcrumbs li").first

        # Page Hero
        self.page_hero_main_header = page.locator("div[class*='hero'] div h1")
        self.page_hero_main_header_subtext = page.locator(
            "//div[contains(@class, 'hero')]/div/h1/following-sibling::p[1]")
        self.page_hero_need_help_header = page.locator("div[class*='hero'] div h2")
        self.page_hero_need_help_subtext = page.locator(
            "//div[contains(@class,'hero')]/div/h1/following-sibling::p[2]")

        # Ways to contribute_messages
        self.way_to_contribute_header = page.locator("//nav/preceding-sibling::h2")
        self.way_to_contribute_cards = page.locator(
            "//h2[contains(text(),'Pick a way to contribute_messages')]/following-sibling::"
            "nav/ul/a")
        self.way_to_contribute_card_titles = page.locator("nav ul a li span")

        # About us
        self.about_us_header = page.get_by_role("heading").filter(has_text="About us")
        self.about_us_subtext = page.locator(
            "//h2[contains(text(),'About us')]/following-sibling::p")

        # All page images
        self.all_page_images = page.locator("div#svelte img")

    # Breadcrumbs
    def _get_breadcrumbs_text(self) -> list[str]:
        return super()._get_text_of_elements(self.breadcrumbs)

    def _click_on_home_breadcrumb(self):
        super()._click(self.breadcrumb_homepage)

    # Page Hero
    def _get_page_hero_main_header_text(self) -> str:
        return super()._get_text_of_element(self.page_hero_main_header)

    def _get_page_hero_main_subtext(self) -> str:
        return super()._get_text_of_element(self.page_hero_main_header_subtext)

    def _get_page_hero_need_help_header_text(self) -> str:
        return super()._get_text_of_element(self.page_hero_need_help_header)

    def _get_page_hero_need_help_subtext(self) -> str:
        return super()._get_text_of_element(self.page_hero_need_help_subtext)

    # Page images
    def _get_all_page_links(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.all_page_images)

    # Way to contribute_messages
    def _get_way_to_contribute_header_text(self) -> str:
        return super()._get_text_of_element(self.way_to_contribute_header)

    def _get_way_to_contribute_cards(self) -> list[str]:
        return super()._get_text_of_elements(self.way_to_contribute_card_titles)

    # About us
    def _get_about_us_header_text(self) -> str:
        return super()._get_text_of_element(self.about_us_header)

    def _get_about_us_subtext(self) -> str:
        return super()._get_text_of_element(self.about_us_subtext)

    # Contribute cards
    def _get_list_of_contribute_cards(self) -> list[ElementHandle]:
        return super()._get_element_handles(self.way_to_contribute_cards)

    def _click_on_way_to_contribute_card(self, way_to_contribute_card: ElementHandle):
        way_to_contribute_card.click()
