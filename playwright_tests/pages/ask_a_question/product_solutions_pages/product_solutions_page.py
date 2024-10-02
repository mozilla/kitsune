from playwright.sync_api import Page, ElementHandle, Locator
from playwright_tests.core.basepage import BasePage


class ProductSolutionsPage(BasePage):
    # Page breadcrumb locators.
    __complete_progress_item = "//li[@class='progress--item is-complete']/a"
    __complete_progress_item_label = ("//li[@class='progress--item is-complete']//span["
                                      "@class='progress--label']")
    __current_progress_item_label = ("//li[@class='progress--item is-current']//span["
                                     "@class='progress--label']")
    # Page content locators.
    __product_title_heading = "//span[@class='product-title-text']"
    __page_heading_intro_text = "//p[@class='page-heading--intro-text']"

    # Find help locators.
    __product_solutions_find_help_searchbar = "//form[@id='question-search-masthead']/input"
    __product_solutions_find_help_search_button = "//form[@id='question-search-masthead']/button"

    # Still need help locators.
    __still_need_help_subheading = "//div[contains(@class, 'aaq-widget')]/p"
    __still_need_help_ask_now_button = "//a[normalize-space(text())='Continue']"

    # Featured articles locators.
    __featured_article_section_title = "//h2[contains(text(),'Featured Articles')]"
    __featured_articles_cards = "//h2[contains(text(),'Featured Articles')]/../..//a"

    # Popular topics locators.
    __popular_topics_section_title = "//h2[contains(text(),'Popular Topics')]"
    __popular_topics_cards = "//h2[contains(text(),'Popular Topics')]/../..//a"

    # Support scam banner locators.
    __support_scams_banner = "//div[@id='id_scam_alert']"
    __support_scam_banner_learn_more_button = "//div[@id='id_scam_alert']//a"

    def __init__(self, page: Page):
        super().__init__(page)

    # Still need help actions.
    def click_ask_now_button(self):
        self._click(self.__still_need_help_ask_now_button)

    def get_aaq_product_solutions_subheading_text(self) -> str:
        return self._get_text_of_element(self.__still_need_help_subheading)

    def get_aaq_widget_button_name(self) -> str:
        return self._get_text_of_element(self.__still_need_help_ask_now_button)

    def get_still_need_help_locator(self) -> Locator:
        return self._get_element_locator(self.__still_need_help_ask_now_button)

    # Breadcrumb actions.
    def click_on_the_completed_milestone(self):
        self._click(self.__complete_progress_item)

    def get_current_milestone_text(self) -> str:
        return self._get_text_of_element(self.__current_progress_item_label)

    # Featured article actions.
    def click_on_a_featured_article_card(self, card_name: str):
        self._click(f'//h2[contains(text(),"Featured Articles")]/../..//'
                    f'a[normalize-space(text())="{card_name}"]')

    def get_all_featured_articles_titles(self) -> list[str]:
        return self._get_text_of_elements(self.__featured_articles_cards)

    def is_featured_article_section_displayed(self) -> bool:
        return self._is_element_visible(self.__featured_article_section_title)

    # Popular topic actions.
    def click_on_a_popular_topic_card(self, card_name: str):
        self._click(f"//h2[contains(text(),'Popular Topics')]/../..//"
                    f"a[normalize-space(text()) = '{card_name}']")

    def get_popular_topics(self) -> list[str]:
        return self._get_text_of_elements(self.__popular_topics_cards)

    def is_popular_topics_section_displayed(self) -> bool:
        return self._is_element_visible(self.__popular_topics_section_title)

    # Product solutions actions.
    def get_product_solutions_heading(self) -> str:
        return self._get_text_of_element(self.__product_title_heading)

    def is_product_solutions_page_header_displayed(self) -> ElementHandle:
        return self._get_element_handle(self.__product_title_heading)

    # Support scam banner actions

    # Instead of clicking on the 'Learn More' button we are going to perform the assertion
    # by checking that the element has the correct href value. Navigating to prod can yield
    # a 429 error which we want to avoid.
    def get_scam_alert_banner_link(self) -> str:
        return self._get_element_attribute_value(
            self.__support_scam_banner_learn_more_button,
            "href"
        )

    def get_scam_banner_locator(self) -> Locator:
        return self._get_element_locator(self.__support_scams_banner)
