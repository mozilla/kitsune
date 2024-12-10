from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class SearchPage(BasePage):
    # Locators belonging to the searchbar.
    SEARCHBAR_LOCATORS = {
        "searchbar_homepage": "//form[@id='support-search-masthead']/input[@id='search-q']",
        "searchbar_aaq": "//form[@id='question-search-masthead']/input[@id='search-q']",
        "searchbar_sidebar": "//form[@id='support-search-sidebar']/input[@id='search-q']",
        "hidden_searchbar": "//form[@id='hidden-search']/input[@id='search-q']",
        "searchbar_search_button": "//form[@id='support-search-masthead']/button",
        "search_results_header": "//div[@class='home-search-section--content']/h2",
        "popular_searches": "//p[@class='popular-searches']/a",
        "search_results_section": "//main[@id='search-results-list']"
    }

    # Locators belonging to the search results filter
    SEARCH_RESULTS_FILTER_LOCATORS = {
        "view_all_filter": "//span[text()='View All']/..[0]",
        "help_articles_only_filter": "//span[text()='Help Articles Only']/..[0]",
        "community_discussions_only_filter": "//span[text()='Community Discussion Only']/..[0]"
    }
    # Locators belonging to the search results

    SEARCH_RESULTS_LOCATORS = {
        "search_results_titles": "//section[@class='topic-list content-box']//a[@class='title']",
        "search_results_articles_summary": "//div[@class='topic-article--text']/p",
        "search_results_content": "//section[@class='topic-list content-box']",
        "all_bolded_article_content": "//h3[@class='sumo-card-heading']/a/../following-sibling::"
                                      "p/strong"
    }
    # Locators belonging to the side navbar
    SEARCH_RESULTS_SIDE_NAV_LOCATORS = {
        "search_results_side_nav_header": "//h3[@class='sidebar-subheading']",
        "search_results_side_nav_selected_item": "//ul[@id='product-filter']//"
                                                 "li[@class='selected']/a",
        "search_results_side_nav_elements": "//ul[@id='product-filter']//a"
    }
    # General page locators
    GENERAL_LOCATORS = {
        "page_header": "//h1[@class='sumo-page-heading-xl']"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    def _wait_for_visibility_of_search_results_section(self):
        self._wait_for_selector(self.SEARCHBAR_LOCATORS["search_results_section"])

    """
        Actions against the search results
    """
    def click_on_a_particular_popular_search(self, popular_search_option: str):
        """Click on a particular popular search option

        Args:
            popular_search_option (str): The popular search option to click on
        """
        self._click(f"//p[@class='popular-searches']/a[text()='{popular_search_option}']")

    def get_search_result_summary_text_of_a_particular_article(self, article_title) -> str:
        """Get the search result summary text of a particular article

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_element(f"//h3[@class='sumo-card-heading']/"
                                         f"a[normalize-space(text())='{article_title}']/../"
                                         f"../p")

    def is_a_particular_article_visible(self, article_title: str) -> bool:
        """Check if a particular article is visible

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
        return self._is_element_visible(f"//h3[@class='sumo-card-heading']/"
                                        f"a[normalize-space(text())='{article_title}']")

    def click_on_a_particular_article(self, article_title: str):
        """Click on a particular article

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
        self._click(f"//h3[@class='sumo-card-heading']/"
                    f"a[normalize-space(text())='{article_title}']")

    def get_all_bolded_content(self) -> list[str]:
        """Get all the bolded content of the search results"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_elements(self.SEARCH_RESULTS_LOCATORS
                                          ["all_bolded_article_content"])

    def get_all_search_results_article_bolded_content(self, article_title: str) -> list[str]:
        """Get all the bolded content of a particular article

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
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
        """Get all the titles of the search results"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_elements(self.SEARCH_RESULTS_LOCATORS["search_results_titles"])

    def get_all_search_results_articles_summary(self) -> list[str]:
        """Get all the summaries of the search results"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_elements(self.SEARCH_RESULTS_LOCATORS
                                          ["search_results_articles_summary"])

    def get_locator_of_a_particular_article(self, article_title: str) -> Locator:
        """Get the locator of a particular article

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
        return self._get_element_locator(f"//h3[@class='sumo-card-heading']/"
                                         f"a[normalize-space(text())='{article_title}']")

    def is_search_content_section_displayed(self) -> bool:
        """Check if the search content section is displayed"""
        return self._is_element_visible(self.SEARCH_RESULTS_LOCATORS["search_results_content"])

    """
        Actions against the search bar
    """

    def get_text_of_searchbar_field(self) -> str:
        """Get the text of the search bar field"""
        return self._get_element_input_value(self.SEARCHBAR_LOCATORS["searchbar_homepage"])

    def fill_into_searchbar(self, text: str, is_aaq=False, is_sidebar=False):
        """Fill into the search bar

        Args:
            text (str): The text to fill into the search bar
            is_aaq (bool): Whether the search bar is on the AAQ flow pages
            is_sidebar (bool): Whether the search bar is on the sidebar
        """
        if is_aaq:
            self.clear_the_searchbar(is_aaq=True)
            self._fill(self.SEARCHBAR_LOCATORS["searchbar_aaq"], text)
        elif is_sidebar:
            self._fill(self.SEARCHBAR_LOCATORS["searchbar_sidebar"], text)
        else:
            self.clear_the_searchbar()
            self._fill(self.SEARCHBAR_LOCATORS["searchbar_homepage"], text)

    def clear_the_searchbar(self, is_aaq=False, is_sidebar=False):
        """Clear the search bar

        Args:
            is_aaq (bool): Whether the search bar is on the AAQ flow pages
            is_sidebar (bool): Whether the search bar is on the sidebar
        """
        if is_aaq:
            self._clear_field(self.SEARCHBAR_LOCATORS["searchbar_aaq"])
        elif is_sidebar:
            self._clear_field(self.SEARCHBAR_LOCATORS["hidden_searchbar"])
        else:
            self._clear_field(self.SEARCHBAR_LOCATORS["searchbar_homepage"])

    def click_on_search_button(self):
        """Click on the search button"""
        self._click(self.SEARCHBAR_LOCATORS["searchbar_search_button"])

    def get_list_of_popular_searches(self) -> list[str]:
        """Get the list of popular searches"""
        return self._get_text_of_elements(self.SEARCHBAR_LOCATORS["popular_searches"])

    def click_on_a_popular_search(self, popular_search_name: str):
        """Click on a popular search

        Args:
            popular_search_name (str): The name of the popular search
        """
        self._click(f"//p[@class='popular-searches']/a[text()='{popular_search_name}']")

    """
        Actions against the side navbar
    """
    def get_the_highlighted_side_nav_item(self) -> str:
        """Get the highlighted side nav item"""
        return self._get_text_of_element(self.SEARCH_RESULTS_SIDE_NAV_LOCATORS
                                         ["search_results_side_nav_selected_item"])

    def click_on_a_particular_side_nav_item(self, product_name: str):
        """Click on a particular side nav item

        Args:
            product_name (str): The name of the product
        """
        self._click(f"//ul[@id='product-filter']//a[normalize-space(text())='{product_name}']")

    """
        General page actions
    """
    def get_search_results_header(self) -> str:
        """Get the search results header"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_element(self.SEARCHBAR_LOCATORS["search_results_header"])
