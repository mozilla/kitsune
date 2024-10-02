from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class SearchPage(BasePage):
    """
        Locators belonging to the searchbar.
    """
    __searchbar = "//form[@id='support-search-masthead']/input[@id='search-q']"
    __searchbar_search_button = "//form[@id='support-search-masthead']/button"
    __search_results_header = "//div[@class='home-search-section--content']/h2"
    __popular_searches = "//p[@class='popular-searches']/a"

    """
        Locators belonging to the search results filter
    """
    __view_all_filter = "//span[text()='View All']/..[0]"
    __help_articles_only_filter = "//span[text()='Help Articles Only']/..[0]"
    __community_discussions_only_filter = "//span[text()='Community Discussion Only']/..[0]"

    """
        Locators belonging to the search results
    """
    __search_results_titles = "//section[@class='topic-list content-box']//a[@class='title']"
    __search_results_articles_summary = "//div[@class='topic-article--text']/p"
    __search_results_content = "//section[@class='topic-list content-box']"
    __all_bolded_article_content = ("//h3[@class='sumo-card-heading']/a/../following-sibling::p/"
                                    "strong")

    """
        Locators belonging to the side navbar
    """
    __search_results_side_nav_header = "//h3[@class='sidebar-subheading']"
    __search_results_side_nav_selected_item = "//ul[@id='product-filter']//li[@class='selected']/a"
    __search_results_side_nav_elements = "//ul[@id='product-filter']//a"

    """
        General locators
    """
    __page_header = "//h1[@class='sumo-page-heading-xl']"

    def __init__(self, page: Page):
        super().__init__(page)

    """
        Actions against the search results
    """
    def click_on_a_particular_popular_search(self, popular_search_option: str):
        self._click(f"//p[@class='popular-searches']/a[text()='{popular_search_option}']")

    def get_search_result_summary_text_of_a_particular_article(self, article_title) -> str:
        return self._get_text_of_element(f"//h3[@class='sumo-card-heading']/"
                                         f"a[normalize-space(text())='{article_title}']/../"
                                         f"../p")

    def is_a_particular_article_visible(self, article_title: str) -> bool:
        return self._is_element_visible(f"//h3[@class='sumo-card-heading']/"
                                        f"a[normalize-space(text())='{article_title}']")

    def click_on_a_particular_article(self, article_title: str):
        self._click(f"//h3[@class='sumo-card-heading']/"
                    f"a[normalize-space(text())='{article_title}']")

    def get_all_bolded_content(self) -> list[str]:
        return self._get_text_of_elements(self.__all_bolded_article_content)

    def get_all_search_results_article_bolded_content(self, article_title: str) -> list[str]:
        if "'" in article_title:
            parts = article_title.split("'")
            if len(parts) > 1:
                # Construct XPath using concat function
                xpath = (f"//h3[@class='sumo-card-heading']/a[normalize-space(text())=concat("
                         f"'{parts[0]}', \"'\", '{parts[1]}')]/../following-sibling::p/strong")
            else:
                # Handle the case where the text ends with a single quote
                xpath = (f"//h3[@class='sumo-card-heading']/a[normalize-space(text())=concat("
                         f"'{parts[0]}', \"'\")]/../following-sibling::p/strong")
        else:
            # Construct XPath without concat for texts without single quotes

            xpath = (f"//h3[@class='sumo-card-heading']/a[normalize-space(text()"
                     f")='{article_title}']/../following-sibling::p/strong")
        return self._get_text_of_elements(xpath)

    def get_all_search_results_article_titles(self) -> list[str]:
        return self._get_text_of_elements(self.__search_results_titles)

    def get_all_search_results_articles_summary(self) -> list[str]:
        return self._get_text_of_elements(self.__search_results_articles_summary)

    def get_locator_of_a_particular_article(self, article_title: str) -> Locator:
        return self._get_element_locator(f"//h3[@class='sumo-card-heading']/"
                                         f"a[normalize-space(text())='{article_title}']")

    def is_search_content_section_displayed(self) -> bool:
        return self._is_element_visible(self.__search_results_content)

    """
        Actions against the search bar
    """

    def get_text_of_searchbar_field(self) -> str:
        return self._get_element_input_value(self.__searchbar)

    def fill_into_searchbar(self, text: str):
        self._fill(self.__searchbar, text)

    def clear_the_searchbar(self):
        self._clear_field(self.__searchbar)

    def click_on_search_button(self):
        self._click(self.__searchbar_search_button)

    def get_list_of_popular_searches(self) -> list[str]:
        return self._get_text_of_elements(self.__popular_searches)

    def click_on_a_popular_search(self, popular_search_name: str):
        self._click(f"//p[@class='popular-searches']/a[text()='{popular_search_name}']")

    """
        Actions against the side navbar
    """
    def get_the_highlighted_side_nav_item(self) -> str:
        return self._get_text_of_element(self.__search_results_side_nav_selected_item)

    def click_on_a_particular_side_nav_item(self, product_name: str):
        self._click(f"//ul[@id='product-filter']//a[normalize-space(text())='{product_name}']")

    """
        General page actions
    """
    def get_search_results_header(self) -> str:
        return self._get_text_of_element(self.__search_results_header)
