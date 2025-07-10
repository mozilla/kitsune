from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class ProductSupportPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Product support breadcrumb locators.
        self.home_breadcrumb = page.locator("ol#breadcrumbs li").get_by_role("link")

        # Page content locators.
        self.product_title = page.locator("span.product-title-text")

        # Feature article locators.
        self.featured_article_section_title = page.get_by_role("heading").filter(
            has_text="Featured Articles")
        self.featured_articles_cards = page.locator(
            "//h2[contains(text(),'Featured Articles')]/..//a")
        self.featured_article_card = lambda card_title: page.locator(
            f'//h2[contains(text(),"Featured Articles")]/..//a[normalize-space(text())'
            f'="{card_title}"]')

        # Still need help widget locators.
        self.still_need_help_widget = page.locator(
            "section[class='support-callouts mzp-l-content sumo-page-section--inner']")
        self.still_need_help_widget_title = page.locator(
            "section[class='support-callouts mzp-l-content sumo-page-section--inner'] "
            "h3.card--title")
        self.still_need_help_widget_details = page.locator(
            "section[class='support-callouts mzp-l-content sumo-page-section--inner'] "
            "p.card--desc")
        self.ask_the_community_still_need_help_widget = page.locator(
            "section[class='support-callouts mzp-l-content sumo-page-section--inner']"
        ).get_by_role("link")

    def click_on_product_support_home_breadcrumb(self):
        """Click on the home breadcrumb link on the product support page."""
        self._click(self.home_breadcrumb)

    def get_product_support_title_text(self) -> str:
        """Get the product title text on the product support page."""
        return self._get_text_of_element(self.product_title)

    def product_product_title_element(self) -> Locator:
        """Get the product title element locator on the product support page."""
        return self.product_title

    def get_featured_articles_header_text(self) -> str:
        """Get the featured articles section title text."""
        return self._get_text_of_element(self.featured_article_section_title)

    def is_featured_articles_section_displayed(self) -> bool:
        """Check if the featured articles section is displayed on the page."""
        return self._is_element_visible(self.featured_article_section_title)

    def get_list_of_featured_articles_headers(self) -> list[str]:
        """Get the text of all the featured articles cards."""
        return self._get_text_of_elements(self.featured_articles_cards)

    def get_feature_articles_count(self) -> int:
        """Get the count of the featured articles."""
        return len(self._get_text_of_elements(self.featured_articles_cards))

    def click_on_a_particular_feature_article_card(self, card_title):
        """Click on a particular featured article card.

        Args:
            card_title (str): The title of the card to click on.
        """
        self._click(self.featured_article_card(card_title))

    def is_still_need_help_widget_displayed(self) -> bool:
        """Check if the still need help widget is displayed on the page."""
        return self._is_element_visible(self.still_need_help_widget)

    def get_still_need_help_widget_title(self) -> str:
        """Get the still need help widget title text."""
        return self._get_text_of_element(self.still_need_help_widget_title)

    def get_still_need_help_widget_content(self) -> str:
        """Get the still need help widget content text."""
        return self._get_text_of_element(self.still_need_help_widget_details)

    def get_still_need_help_widget_button_text(self) -> str:
        """Get the text of the still need help widget button."""
        return self._get_text_of_element(self.ask_the_community_still_need_help_widget)

    def click_still_need_help_widget_button(self):
        """Click on the still need help widget button."""
        self._click(self.ask_the_community_still_need_help_widget)
