from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class ProductTopicPage(BasePage):
    # Product topic page content locators.
    GENERAL_PAGE_LOCATORS = {
        "page_title": "//h1[@class='topic-title sumo-page-heading']",
        "page_subheading": "//div[@class='sumo-article-header--text']/p",
        "all_articles": "//section[@class='topic-list']/article//h2/a",
        "article_link": lambda article_title: f"//h2[@class='sumo-card-heading']/a[normalize-space"
                                              f"(text())='{article_title}']"
    }

    # Product topic page navbar locators.
    NAVBAR_LOCATORS = {
        "navbar_links": "//ul[@class='sidebar-nav--list']/li/a",
        "selected_nav_link": "//a[contains(@class,'selected')]",
        "navbar_option": lambda option_name: f"//ul[@class='sidebar-nav--list']/li/a[contains("
                                             f"text(),'{option_name}')]"
    }
    # Product topic page learn more locators.
    LEARN_MORE_LOCATORS = {
        "learn_more_button": "//section[@id='get-involved-button']//a"
    }

    # Product topic page still need help locators.
    AAQ_WIDGET_LOCATORS = {
        "still_need_help_subheading": "//div[contains(@class, 'aaq-widget')]/p",
        "aaq_button": "//div[contains(@class,'aaq-widget')]/a"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Page content actions.
    def get_all_listed_article_titles(self) -> list[str]:
        """Returns a list of all the article titles displayed on the page."""
        return self._get_text_of_elements(self.GENERAL_PAGE_LOCATORS["all_articles"])

    def get_page_title(self) -> str:
        """Returns the title of the page."""
        return self._get_text_of_element(self.GENERAL_PAGE_LOCATORS["page_title"])

    def get_a_particular_article_locator(self, article_title: str):
        """Returns the locator of a particular article."""
        return self._get_element_locator(self.GENERAL_PAGE_LOCATORS["article_link"](article_title))

    def click_on_a_particular_article(self, article_title: str):
        self._click(self.GENERAL_PAGE_LOCATORS["article_link"](article_title))

    # Navbar actions.
    def get_selected_navbar_option(self) -> str:
        """Returns the text of the selected navbar option."""
        return self._get_text_of_element(self.NAVBAR_LOCATORS["selected_nav_link"])

    def click_on_a_navbar_option(self, option_name: str):
        """Clicks on a particular navbar option."""
        self._click(self.NAVBAR_LOCATORS["navbar_option"](option_name))

    def get_navbar_links_text(self) -> list[str]:
        """Returns a list of all the navbar links displayed on the page."""
        return self._get_text_of_elements(self.NAVBAR_LOCATORS["navbar_links"])

    def get_navbar_option_link(self, option_name: str) -> str:
        """Returns the href value of a particular navbar option."""
        return self._get_element_attribute_value(self.NAVBAR_LOCATORS["navbar_option"]
                                                 (option_name),
                                                 "href")

    # AAQ section actions.
    def get_aaq_widget_subheading_text(self) -> str:
        """Returns the text of the subheading displayed on the AAQ widget."""
        return self._get_text_of_element(self.AAQ_WIDGET_LOCATORS["still_need_help_subheading"])

    def click_on_aaq_button(self):
        """Clicks on the 'Ask a question' button."""
        self._click(self.AAQ_WIDGET_LOCATORS["aaq_button"])

    # Learn more section actions.
    def click_on_learn_more_button(self):
        """Clicks on the 'Learn More' button."""
        self._click(self.LEARN_MORE_LOCATORS["learn_more_button"])
