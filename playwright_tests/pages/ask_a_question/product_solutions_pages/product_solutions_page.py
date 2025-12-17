from playwright.sync_api import ElementHandle, Page
from playwright_tests.core.basepage import BasePage


class ProductSolutionsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the page breadcrumbs."""
        self.complete_progress_item = page.locator("li[class='progress--item is-complete'] a")
        self.complete_progress_item_label = page.locator(
            "li[class='progress--item is-complete'] span.progress--label")
        self.current_progress_item_label = page.locator(
            "li[class='progress--item is-current'] span.progress--label")

        """General page content locators."""
        self.product_title_heading = page.locator("span.product-title-text")
        self.page_heading_intro_text = page.locator("p.page-heading--intro-text")

        """Locators belonging to the Find Help section."""
        self.product_solutions_find_help_searchbar = page.locator(
            "form#question-search-masthead input")
        self.product_solutions_find_help_search_button = page.locator(
            "form#question-search-masthead button")

        """Locators belonging to the featured articles section."""
        self.featured_article_section_title = page.get_by_role("heading").filter(
            has_text="Featured Articles")
        self.featured_articles_cards = page.locator(
            "//h2[contains(text(),'Featured Articles')]/../..//a")
        self.featured_article_card = lambda card_name: page.locator(
            f'//h2[contains(text(),"Featured Articles")]/../..//a[normalize-space(text())='
            f'"{card_name}"]')

        """Locators belonging to the popular topics section."""
        self.popular_topics_section_title = page.get_by_role("heading").filter(
            has_text="Popular Topics")
        self.popular_topics_cards = page.locator(
            "//h2[contains(text(),'Popular Topics')]/../..//a")
        self.popular_topic_card = lambda card_name: page.locator(
            f"//h2[contains(text(),'Popular Topics')]/../..//a[normalize-space(text()) = "
            f"'{card_name}']")

        """Locators belonging to the support scam banner."""
        self.support_scams_banner = page.locator("div#id_scam_alert")
        self.support_scam_banner_learn_more_button = page.locator("div#id_scam_alert a")

    """Actions against the page breadcrumbs locators."""
    def click_on_the_completed_milestone(self):
        self._click(self.complete_progress_item)

    def get_current_milestone_text(self) -> str:
        return self._get_text_of_element(self.current_progress_item_label)

    """Actions against the featured article section locators."""
    def click_on_a_featured_article_card(self, card_name: str):
        self._click(self.featured_article_card(card_name))

    def get_all_featured_articles_titles(self) -> list[str]:
        return self._get_text_of_elements(self.featured_articles_cards)

    def is_featured_article_section_displayed(self) -> bool:
        return self._is_element_visible(self.featured_article_section_title)

    """Actions against the popular topic section locators."""
    def click_on_a_popular_topic_card(self, card_name: str):
        self._click(self.popular_topic_card(card_name))

    def get_popular_topics(self) -> list[str]:
        return self._get_text_of_elements(self.popular_topics_cards)

    def is_popular_topics_section_displayed(self) -> bool:
        return self._is_element_visible(self.popular_topics_section_title)

    """Actions against the product solutions section locators."""
    def get_product_solutions_heading(self) -> str:
        return self._get_text_of_element(self.product_title_heading)

    def is_product_solutions_page_header_displayed(self) -> ElementHandle:
        return self._get_element_handle(self.product_title_heading)

    """Actions against the scam banner locators."""
    def get_scam_alert_banner_link(self) -> str:
        # Instead of clicking on the 'Learn More' button we are going to perform the assertion
        # by checking that the element has the correct href value. Navigating to prod can yield
        # a 429 error which we want to avoid.
        return self._get_element_attribute_value(self.support_scam_banner_learn_more_button,
                                                 "href")
