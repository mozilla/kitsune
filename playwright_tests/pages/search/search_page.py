from playwright.sync_api import Locator, Page, ElementHandle

from playwright_tests.core.basepage import BasePage


class SearchPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the searchbar."""
        self.searchbar_homepage = page.locator("form#support-search-masthead input#search-q")
        self.searchbar_aaq = page.locator("form#question-search-masthead input#search-q")
        self.searchbar_sidebar = page.locator("form#support-search-sidebar input#search-q")
        self.hidden_searchbar = page.locator("form#hidden-search input#search-q")
        self.searchbar_search_button = page.locator("form#support-search-masthead button")
        self.search_results_header = page.locator("div[class='home-search-section--content'] h2")
        self.popular_searches = page.locator("div[class='popular-searches'] a")
        self.popular_search = lambda option: page.locator(
            "p[class='popular-searches']").get_by_role("link", name=option, exact=True)
        self.search_results_section = page.locator("main#search-results-list")

        """Locators belonging to the search results filter."""
        self.selected_filter_locator = page.locator(
            "//ul[@id='doctype-filter']/li[@class='tabs--item']/a[@class='selected']/span")
        self.view_all_filter = page.locator(
            "//ul[@id='doctype-filter']/li[@class='tabs--item']/a/span[text()='View All']")
        self.help_articles_only_filter = page.locator(
            "//ul[@id='doctype-filter']/li[@class='tabs--item']/a/span[text()='Help Articles "
            "Only']")
        self.community_discussions_only_filter = page.locator(
            "//ul[@id='doctype-filter']/li[@class='tabs--item']/a/span[text()='Community "
            "Discussion Only']")

        """Locators belonging to the search results."""
        self.search_results_titles = page.locator(
            "section[class='topic-list content-box'] a[class='title']")
        self.search_results_articles_summary = page.locator("div[class='topic-article--text'] p")
        self.search_results_content = page.locator("section[class='topic-list content-box']")
        self.no_search_results_message = page.locator("//main[@id='search-results-list']/p")
        self.all_bolded_article_content = page.locator(
            "//h3[@class='sumo-card-heading']/a/../following-sibling::p/strong")
        self.article_search_summary = lambda article_title: page.locator(
            f"//h3[@class='sumo-card-heading']/a[normalize-space("
            f"text())='{article_title}']/../../p")
        self.article = lambda article_title: page.locator(
            "h3[class='sumo-card-heading']").get_by_role("link", name=article_title, exact=True)
        self.question_votes_meta_information = page.locator(
            "//ul[@class='topic-article--meta-list thread-meta']/li[contains(text(),"
            "'people have this problem')]")

        """Locators belonging to the side navbar."""
        self.search_results_side_nav_header = page.locator("h3[class='sidebar-subheading']")
        self.search_results_side_nav_selected_item = page.locator(
            "ul#product-filter li[class='selected'] a")
        self.search_results_side_nav_elements = page.locator("ul#product-filter a")
        self.search_results_side_nav_element = lambda product_name: page.locator(
            "ul#product-filter").get_by_role("link", name=product_name, exact=True)

        """General page locators."""
        self.page_header = page.locator("h1[class='sumo-page-heading-xl']")


    def _wait_for_visibility_of_search_results_section(self):
        self._wait_for_locator(self.search_results_section)

    """Actions against the search results."""
    def click_on_a_particular_popular_search(self, popular_search_option: str):
        """Click on a particular popular search option

        Args:
            popular_search_option (str): The popular search option to click on
        """
        self._click(self.popular_search(popular_search_option))
        self._wait_for_visibility_of_search_results_section()

    def get_search_result_summary_text_of_a_particular_article(self, article_title) -> str:
        """Get the search result summary text of a particular article

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_element(self.article_search_summary(article_title))

    def is_a_particular_article_visible(self, article_title: str) -> bool:
        """Check if a particular article is visible

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
        return self._is_element_visible(self.article(article_title))

    def click_on_a_particular_article(self, article_title: str):
        """Click on a particular article

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
        self._click(self.article(article_title))

    def get_all_bolded_content(self) -> list[str]:
        """Get all the bolded content of the search results"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_elements(self.all_bolded_article_content)

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
        return self._get_text_of_elements(self.page.locator(xpath))

    def get_all_search_results_article_titles(self) -> list[str]:
        """Get all the titles of the search results"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_elements(self.search_results_titles)

    def get_all_search_results_handles(self) -> list[ElementHandle]:
        """Get all search results handles"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_element_handles(self.search_results_titles)

    def get_all_search_results_articles_summary(self) -> list[str]:
        """Get all the summaries of the search results"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_elements(self.search_results_articles_summary)

    def get_locator_of_a_particular_article(self, article_title: str) -> Locator:
        """Get the locator of a particular article

        Args:
            article_title (str): The title of the article
        """
        self._wait_for_visibility_of_search_results_section()
        return self.article(article_title)

    def get_text_of_question_votes(self) -> list[str]:
        """Get the 'I have this problem' question votes text"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_elements(self.question_votes_meta_information)

    def is_search_content_section_displayed(self) -> bool:
        """Check if the search content section is displayed"""
        return self._is_element_visible(self.search_results_content)

    """Actions against the search bar."""

    def get_text_of_searchbar_field(self) -> str:
        """Get the text of the search bar field"""
        return self._get_element_input_value(self.searchbar_homepage)

    def fill_into_searchbar(self, text: str, is_aaq=False, is_sidebar=False):
        """Fill into the search bar

        Args:
            text (str): The text to fill into the search bar
            is_aaq (bool): Whether the search bar is on the AAQ flow pages
            is_sidebar (bool): Whether the search bar is on the sidebar
        """
        self.wait_for_dom_to_load()
        if is_aaq:
            self.clear_the_searchbar(is_aaq=True)
            self._fill(self.searchbar_aaq, text)
        elif is_sidebar:
            self._fill(self.searchbar_sidebar, text)
        else:
            self.clear_the_searchbar()
            self._fill(self.searchbar_homepage, text)
        self._wait_for_visibility_of_search_results_section()

    def clear_the_searchbar(self, is_aaq=False, is_sidebar=False):
        """Clear the search bar

        Args:
            is_aaq (bool): Whether the search bar is on the AAQ flow pages
            is_sidebar (bool): Whether the search bar is on the sidebar
        """
        if is_aaq:
            self._clear_field(self.searchbar_aaq)
        elif is_sidebar:
            self._clear_field(self.hidden_searchbar)
        else:
            self._clear_field(self.searchbar_homepage)

    def click_on_search_button(self):
        """Click on the search button"""
        self._click(self.searchbar_search_button)

    def get_list_of_popular_searches(self) -> list[str]:
        """Get the list of popular searches"""
        return self._get_text_of_elements(self.popular_searches)

    def click_on_a_popular_search(self, popular_search_name: str):
        """Click on a popular search

        Args:
            popular_search_name (str): The name of the popular search
        """
        self._click(self.popular_search(popular_search_name))

    """Actions against the side navbar."""
    def get_the_highlighted_side_nav_item(self) -> str:
        """Get the highlighted side nav item"""
        return self._get_text_of_element(self.search_results_side_nav_selected_item)

    def click_on_a_particular_side_nav_item(self, product_name: str):
        """Click on a particular side nav item

        Args:
            product_name (str): The name of the product
        """
        self._click(self.search_results_side_nav_element(product_name))

    """General page actions."""
    def get_search_results_header(self) -> str:
        """Get the search results header"""
        self._wait_for_visibility_of_search_results_section()
        return self._get_text_of_element(self.search_results_header)

    def get_doctype_filter(self) -> str:
        """Get the selected doctype filter"""
        return self._get_text_of_element(self.selected_filter_locator)

    def click_on_view_all_doctype_filter(self):
        """Clicking on the 'Vew All' doctype filter."""
        self._click(self.view_all_filter)

    def click_on_help_articles_only_doctype_filter(self):
        """Clicking on the 'Help Articles Only filter.'"""
        self._click(self.help_articles_only_filter)

    def click_on_community_discussions_only_doctype_filter(self):
        """Clicking on the 'Community Discussions Only' filter"""
        self._click(self.community_discussions_only_filter)

    def get_no_search_results_message(self) -> str:
        """Returning the message displayed when no search results were returned."""
        return self._get_text_of_element(self.no_search_results_message)
