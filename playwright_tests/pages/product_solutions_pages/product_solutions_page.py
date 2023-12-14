from playwright.sync_api import Page, ElementHandle
from playwright_tests.core.basepage import BasePage


class ProductSolutionsPage(BasePage):
    __complete_progress_item = "//li[@class='progress--item is-complete']/a"
    __complete_progress_item_label = ("//li[@class='progress--item is-complete']//span["
                                      "@class='progress--label']")
    __current_progress_item_label = ("//li[@class='progress--item is-current']//span["
                                     "@class='progress--label']")
    __product_title_heading = "//span[@class='product-title-text']"
    __product_solutions_find_help_searchbar = "//form[@id='question-search-masthead']/input"
    __product_solutions_find_help_search_button = "//form[@id='question-search-masthead']/button"
    __page_heading_intro_text = "//p[@class='page-heading--intro-text']"
    __still_need_help_subheading = "//div[contains(@class, 'aaq-widget')]/p"
    __still_need_help_ask_now_button = "//a[@data-event-action='aaq']"
    __featured_article_section_title = "//h2[contains(text(),'Featured Articles')]"
    __featured_articles_cards = "//h2[contains(text(),'Featured Articles')]/../..//a"
    __popular_topics_section_title = "//h2[contains(text(),'Popular Topics')]"
    __popular_topics_cards = "//h2[contains(text(),'Popular Topics')]/../..//a"

    def __init__(self, page: Page):
        super().__init__(page)

    def _click_ask_now_button(self):
        super()._click(self.__still_need_help_ask_now_button)

    def _click_on_the_completed_milestone(self):
        super()._click(self.__complete_progress_item)

    def _click_on_a_featured_article_card(self, card_name: str):
        xpath = f'//h2[contains(text(),"Featured Articles")]/../..//a[text()="{card_name}"]'
        super()._click(xpath)

    def _click_on_a_popular_topic_card(self, card_name: str):
        xpth = f'//h2[contains(text(),"Popular Topics")]/../..//a[@data-event-label="{card_name}"]'
        super()._click(xpth)

    def _get_current_milestone_text(self) -> str:
        return super()._get_text_of_element(self.__current_progress_item_label)

    def _get_product_solutions_heading(self) -> str:
        return super()._get_text_of_element(self.__product_title_heading)

    def _get_aaq_subheading_text(self) -> str:
        return super()._get_text_of_element(self.__still_need_help_subheading)

    def _get_all_featured_articles_titles(self) -> list[str]:
        return super()._get_text_of_elements(self.__featured_articles_cards)

    def _get_aaq_widget_button_name(self) -> str:
        return super()._get_text_of_element(self.__still_need_help_ask_now_button)

    def _get_popular_topics(self) -> list[str]:
        return super()._get_text_of_elements(self.__popular_topics_cards)

    def _is_product_solutions_page_header_displayed(self) -> ElementHandle:
        return super()._get_element_handle(self.__product_title_heading)

    def _is_featured_article_section_displayed(self) -> bool:
        return super()._is_element_visible(self.__featured_article_section_title)

    def _is_popular_topics_section_displayed(self) -> bool:
        return super()._is_element_visible(self.__popular_topics_section_title)
