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
    __frequent_topic_all_cards = ("//h2[contains(text(),'Frequent Topics')]/../../../..//a["
                                  "@data-event-action='topic']")

    # Still need help widget locators.
    __still_need_help_widget_title = ("//section[@class='support-callouts mzp-l-content "
                                      "sumo-page-section--inner']//h3[@class='card--title']")
    __still_need_help_widget_details = ("//section[@class='support-callouts mzp-l-content "
                                        "sumo-page-section--inner']//p[@class='card--desc']")
    __ask_the_community_still_need_help_widget = ("//section[@class='support-callouts "
                                                  "mzp-l-content sumo-page-section--inner']//a")

    # Join our community section locators.
    __join_our_community_section_header = ("//div[@class='card card--callout is-full-width "
                                           "has-moz-headings']//h3[@class='card--title']")
    __join_our_community_section_paragrah_and_learn_more_option = ("//div[@class='card "
                                                                   "card--callout is-full-width "
                                                                   "has-moz-headings']//p")

    def __init__(self, page: Page):
        super().__init__(page)

    def _click_on_product_support_home_breadcrumb(self):
        super()._click(self.__home_breadcrumb)

    def _get_product_support_title_text(self) -> str:
        return super()._get_text_of_element(self.__product_title)

    def _product_product_title_element(self) -> Locator:
        return super()._get_element_locator(self.__product_title)

    def _is_frequent_topics_section_displayed(self) -> bool:
        return super()._is_element_visible(self.__frequent_topics_section_title)

    def _get_frequent_topics_title_text(self) -> str:
        return super()._get_text_of_element(self.__frequent_topics_section_title)

    def _get_all_frequent_topics_cards(self) -> list[str]:
        return super()._get_text_of_elements(self.__frequent_topic_all_cards)

    def _get_frequent_topics_subtitle_text(self) -> str:
        return super()._get_text_of_element(self.__frequent_topics_section_subtitle)

    def _click_on_a_particular_frequent_topic_card(self, card_title: str):
        xpath = (f"//h2[contains(text(),'Frequent Topics')]"
                 f"/../../../..//a[@data-event-label='{card_title}']")
        super()._click(xpath)

    def _get_featured_articles_header_text(self) -> str:
        return super()._get_text_of_element(self.__featured_article_section_title)

    def _is_featured_articles_section_displayed(self) -> bool:
        return super()._is_element_visible(self.__featured_article_section_title)

    def _get_list_of_featured_articles_headers(self) -> list[str]:
        return super()._get_text_of_elements(self.__featured_articles_cards)

    def _get_feature_articles_count(self) -> int:
        return len(super()._get_text_of_elements(self.__featured_articles_cards))

    def _click_on_a_particular_feature_article_card(self, card_title):
        xpath = f'//h2[contains(text(),"Featured Articles")]/..//a[text()="{card_title}"]'
        super()._click(xpath)

    def _get_still_need_help_widget_title(self) -> str:
        return super()._get_text_of_element(self.__still_need_help_widget_title)

    def _get_still_need_help_widget_content(self) -> str:
        return super()._get_text_of_element(self.__still_need_help_widget_details)

    def _get_still_need_help_widget_button_text(self) -> str:
        return super()._get_text_of_element(self.__ask_the_community_still_need_help_widget)

    def _click_still_need_help_widget_button(self):
        super()._click(self.__ask_the_community_still_need_help_widget)

    def _get_join_our_community_header_text(self) -> str:
        return super()._get_text_of_element(self.__join_our_community_section_header)

    def _get_join_our_community_content_text(self) -> str:
        return super()._get_text_of_elements(
            self.__join_our_community_section_paragrah_and_learn_more_option
        )[0]

    def _click_join_our_community_learn_more_link(self):
        return (super()._click_on_an_element_by_index
                (self.__join_our_community_section_paragrah_and_learn_more_option, 1)
                )
