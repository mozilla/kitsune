from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class ProductTopicPage(BasePage):
    # Product topic page content locators.
    __page_title = "//h1[@class='topic-title sumo-page-heading']"
    __page_subheading = "//div[@class='sumo-article-header--text']/p"

    # Product topic page navbar locators.
    __navbar_links = "//ul[@class='sidebar-nav--list']/li/a"
    __selected_nav_link = "//a[contains(@class,'selected')]"

    # Product topic page learn more locators.
    __learn_more_button = "//section[@id='get-involved-button']//a"

    # Product topic page still need help locators.
    __still_need_help_subheading = "//div[contains(@class, 'aaq-widget')]/p"
    __aaq_button = "//div[contains(@class,'aaq-widget')]/a"

    def __init__(self, page: Page):
        super().__init__(page)

    # Page content actions.
    def get_page_title(self) -> str:
        return self._get_text_of_element(self.__page_title)

    def get_a_particular_article_locator(self, article_title: str):
        return self._get_element_locator(f"//h2[@class='sumo-card-heading']/a[normalize-space"
                                         f"(text())='{article_title}']")

    # Navbar actions.
    def get_selected_navbar_option(self) -> str:
        return self._get_text_of_element(self.__selected_nav_link)

    def click_on_a_navbar_option(self, option_name: str):
        self._click(f"//ul[@class='sidebar-nav--list']/li/a[contains(text(),'{option_name}')]")

    def get_navbar_links_text(self) -> list[str]:
        return self._get_text_of_elements(self.__navbar_links)

    def get_navbar_option_link(self, option_name: str) -> str:
        return self._get_element_attribute_value(f"//ul[@class='sidebar-nav--list']/li/"
                                                 f"a[contains(text(),'{option_name}')]",
                                                 "href")

    # AAQ section actions.
    def _get_aaq_widget_subheading_text(self) -> str:
        return self._get_text_of_element(self.__still_need_help_subheading)

    def click_on_aaq_button(self):
        self._click(self.__aaq_button)

    # Learn more section actions.
    def click_on_learn_more_button(self):
        self._click(self.__learn_more_button)
