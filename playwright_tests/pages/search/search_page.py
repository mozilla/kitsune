from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class SearchPage(BasePage):
    __search_bar = "//form[@id='support-search-masthead']/input[@id='search-q']"
    __search_bar_button = "//form[@id='support-search-masthead']/button[@class='search-button']"
    __popular_searches = "//p[@class='popular-searches']/a"
    __search_results_article_titles = "//h3[@class='sumo-card-heading']/a"
    __search_results_articles_summary = "//div[@class='topic-article--text']/p"

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_text_of_searchbar_field(self) -> str:
        return super()._get_text_of_element(self.__search_bar)

    def _type_into_searchbar(self, text: str):
        super()._type(self.__search_bar, text, 200)

    def _clear_the_searchbar(self):
        super()._clear_field(self.__search_bar)

    def _click_on_search_button(self):
        super()._click(self.__search_bar_button)

    def _get_list_of_popular_searches(self) -> list[str]:
        return super()._get_text_of_elements(self.__popular_searches)

    def _click_on_a_particular_popular_search(self, popular_search_option: str):
        xpath = f"//p[@class='popular-searches']/a[text()='{popular_search_option}']"
        super()._click(xpath)

    def _get_search_result_summary_text_of_a_particular_article(self, article_title) -> str:
        xpath = f"//h3[@class='sumo-card-heading']/a[text()='{article_title}']/../../p"
        return super()._get_text_of_element(xpath)

    def _click_on_a_particular_article(self, article_title):
        xpath = f"//h3[@class='sumo-card-heading']/a[text()='{article_title}']"
        super()._click(xpath)

    def _get_all_search_results_article_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__search_results_article_titles)

    def _get_all_search_results_articles_summary(self) -> list[str]:
        return super()._get_text_of_elements(self.__search_results_articles_summary)

    def _get_locator_of_a_particular_article(self, article_title: str) -> Locator:
        xpath = f"//h3[@class='sumo-card-heading']/a[text()='{article_title}']"
        return super()._get_element_locator(xpath)
