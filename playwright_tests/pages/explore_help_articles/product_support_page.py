from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class ProductSupportPage(BasePage):
    # Product support breadcrumb locators.
    __home_breadcrumb = "//ol[@id='breadcrumbs']/li/a"

    # Page content locators.
    __product_title = "//span[@class='product-title-text']"

    # Feature article locators.
    __featured_article_section_title = "//h2[contains(text(),'Featured Articles')]"
    __featured_articles_cards = "//h2[contains(text(),'Featured Articles')]/..//a"

    # Frequent Topics locators.
    __frequent_topics_section_title = "//h2[contains(text(),'Frequent Topics')]"
    __frequent_topics_section_subtitle = ("//h2[contains(text(),'Frequent "
                                          "Topics')]/following-sibling::p")
    __frequent_topic_all_cards = "//div[contains(@class,'card card--topic')]//a"

    # Still need help widget locators.
    __still_need_help_widget = ("//section[@class='support-callouts mzp-l-content sumo-page-"
                                "section--inner']")
    __still_need_help_widget_title = ("//section[@class='support-callouts mzp-l-content "
                                      "sumo-page-section--inner']//h3[@class='card--title']")
    __still_need_help_widget_details = ("//section[@class='support-callouts mzp-l-content "
                                        "sumo-page-section--inner']//p[@class='card--desc']")
    __ask_the_community_still_need_help_widget = ("//section[@class='support-callouts "
                                                  "mzp-l-content sumo-page-section--inner']//a")

    # Join our community section locators.
    __join_our_community_section_header = ("//div[@class='card card--callout is-full-width "
                                           "has-moz-headings']//h3[@class='card--title']")
    __join_our_community_section_paragraph_and_learn_more_option = ("//div[@class='card "
                                                                    "card--callout is-full-width "
                                                                    "has-moz-headings']//p")

    def __init__(self, page: Page):
        super().__init__(page)

    def click_on_product_support_home_breadcrumb(self):
        self._click(self.__home_breadcrumb)

    def get_product_support_title_text(self) -> str:
        return self._get_text_of_element(self.__product_title)

    def product_product_title_element(self) -> Locator:
        return self._get_element_locator(self.__product_title)

    def is_frequent_topics_section_displayed(self) -> bool:
        return self._is_element_visible(self.__frequent_topics_section_title)

    def get_frequent_topics_title_text(self) -> str:
        return self._get_text_of_element(self.__frequent_topics_section_title)

    def get_all_frequent_topics_cards(self) -> list[str]:
        return self._get_text_of_elements(self.__frequent_topic_all_cards)

    def get_frequent_topics_subtitle_text(self) -> str:
        return self._get_text_of_element(self.__frequent_topics_section_subtitle)

    def click_on_a_particular_frequent_topic_card(self, card_title: str):
        self._click(f"//h2[contains(text(),'Frequent Topics')]/../../../..//a[normalize-space("
                    f"text())='{card_title}']")

    def get_featured_articles_header_text(self) -> str:
        return self._get_text_of_element(self.__featured_article_section_title)

    def is_featured_articles_section_displayed(self) -> bool:
        return self._is_element_visible(self.__featured_article_section_title)

    def get_list_of_featured_articles_headers(self) -> list[str]:
        return self._get_text_of_elements(self.__featured_articles_cards)

    def get_feature_articles_count(self) -> int:
        return len(self._get_text_of_elements(self.__featured_articles_cards))

    def click_on_a_particular_feature_article_card(self, card_title):
        self._click(f'//h2[contains(text(),"Featured Articles")]/..//a[normalize-space(text())'
                    f'="{card_title}"]')

    def is_still_need_help_widget_displayed(self) -> bool:
        return self._is_element_visible(self.__still_need_help_widget)

    def get_still_need_help_widget_title(self) -> str:
        return self._get_text_of_element(self.__still_need_help_widget_title)

    def get_still_need_help_widget_content(self) -> str:
        return self._get_text_of_element(self.__still_need_help_widget_details)

    def get_still_need_help_widget_button_text(self) -> str:
        return self._get_text_of_element(self.__ask_the_community_still_need_help_widget)

    def click_still_need_help_widget_button(self):
        self._click(self.__ask_the_community_still_need_help_widget)

    def get_join_our_community_header_text(self) -> str:
        return self._get_text_of_element(self.__join_our_community_section_header)

    def get_join_our_community_content_text(self) -> str:
        return self._get_text_of_elements(
            self.__join_our_community_section_paragraph_and_learn_more_option
        )[0]

    def click_join_our_community_learn_more_link(self):
        return (self._click_on_an_element_by_index
                (self.__join_our_community_section_paragraph_and_learn_more_option, 1)
                )
