from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class ProductTopicPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Product topic page content locators.
        self.page_title = page.locator("h1[class='topic-title sumo-page-heading']")
        self.page_subheading = page.locator("div[class='sumo-article-header--text'] p")
        self.all_articles = page.locator("section[class='topic-list'] article h2 a")
        self.article_link = lambda article_title: page.locator(
            "h2[class='sumo-card-heading']").get_by_role(
            "link", name=article_title, exact=True)

        # Product topic page navbar locators.
        self.navbar_links = page.locator("//ul[@class='sidebar-nav--list']/li/a")
        self.selected_nav_link = page.locator("a[class*='selected']")
        self.navbar_option = lambda option_name: page.locator(
            "ul[class='sidebar-nav--list'] li").get_by_role("link").filter(has_text=option_name)

        # Product topic page article metadata locators.
        self.article_helpfulness_count = lambda article_name: page.locator(
            f"//a[normalize-space(text())='{article_name}']/../../div[@id='document_metadata']//"
            f"span[@class='helpful-count']")

    # Page content actions.
    def get_all_listed_article_titles(self) -> list[str]:
        """Returns a list of all the article titles displayed on the page."""
        return self._get_text_of_elements(self.all_articles)

    def get_page_title(self) -> str:
        """Returns the title of the page."""
        return self._get_text_of_element(self.page_title)

    def get_a_particular_article_locator(self, article_title: str):
        """Returns the locator of a particular article."""
        return self.article_link(article_title)

    def click_on_a_particular_article(self, article_title: str):
        self._click(self.article_link(article_title))

    # Navbar actions.
    def get_selected_navbar_option(self) -> str:
        """Returns the text of the selected navbar option."""
        return self._get_text_of_element(self.selected_nav_link)

    def click_on_a_navbar_option(self, option_name: str):
        """Clicks on a particular navbar option."""
        self._click(self.navbar_option(option_name))

    def get_navbar_links_text(self) -> list[str]:
        """Returns a list of all the navbar links displayed on the page."""
        return self._get_text_of_elements(self.navbar_links)

    def get_navbar_option_link(self, option_name: str) -> str:
        """Returns the href value of a particular navbar option."""
        return self._get_element_attribute_value(self.navbar_option(option_name),"href")

    def is_article_helpfulness_metadata_displayed(self, article_title: str) -> bool:
        """Checks if the article helpfulness metadata is displayed."""
        return self._is_element_visible(self.article_helpfulness_count(article_title))
