from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class ProductSupportPage(BasePage):
    # Product support breadcrumb locators.
    BREADCRUMB_LOCATORS = {
        "home_breadcrumb": "//ol[@id='breadcrumbs']/li/a"
    }

    # Page content locators.
    PAGE_CONTENT_LOCATORS = {
        "product_title": "//span[@class='product-title-text']"
    }

    # Feature article locators.
    FEATURE_ARTICLE_LOCATORS = {
        "featured_article_section_title": "//h2[contains(text(),'Featured Articles')]",
        "featured_articles_cards": "//h2[contains(text(),'Featured Articles')]/..//a"
    }

    # Frequent Topics locators.
    FREQUENT_TOPICS_LOCATORS = {
        "frequent_topics_section_title": "//h2[contains(text(),'Frequent Topics')]",
        "frequent_topics_section_subtitle": "//h2[contains(text(),'Frequent Topics')]/following-"
                                            "sibling::p",
        "frequent_topic_all_cards": "//div[contains(@class,'card card--topic')]//a"
    }

    # Still need help widget locators.
    STILL_NEED_HELP_WIDGET_LOCATORS = {
        "still_need_help_widget": "//section[@class='support-callouts mzp-l-content sumo-page-"
                                  "section--inner']",
        "still_need_help_widget_title": "//section[@class='support-callouts mzp-l-content sumo-"
                                        "page-section--inner']//h3[@class='card--title']",
        "still_need_help_widget_details": "//section[@class='support-callouts mzp-l-content sumo-"
                                          "page-section--inner']//p[@class='card--desc']",
        "ask_the_community_still_need_help_widget": "//section[@class='support-callouts mzp-l-"
                                                    "content sumo-page-section--inner']//a"
    }

    # Join our community section locators.
    JOIN_OUR_COMMUNITY_LOCATORS = {
        "join_our_community_section_header": "//div[@class='card card--callout is-full-width has-"
                                             "moz-headings']//h3[@class='card--title']",
        "join_our_community_section_paragraph_and_learn_more_option": "//div[@class='card card--"
                                                                      "callout is-full-width has-"
                                                                      "moz-headings']//p"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    def click_on_product_support_home_breadcrumb(self):
        """Click on the home breadcrumb link on the product support page."""
        self._click(self.BREADCRUMB_LOCATORS["home_breadcrumb"])

    def get_product_support_title_text(self) -> str:
        """Get the product title text on the product support page."""
        return self._get_text_of_element(self.PAGE_CONTENT_LOCATORS["product_title"])

    def product_product_title_element(self) -> Locator:
        """Get the product title element locator on the product support page."""
        return self._get_element_locator(self.PAGE_CONTENT_LOCATORS["product_title"])

    def is_frequent_topics_section_displayed(self) -> bool:
        """Check if the frequent topics section is displayed on the page."""
        return self._is_element_visible(self.FREQUENT_TOPICS_LOCATORS
                                        ["frequent_topics_section_title"])

    def get_frequent_topics_title_text(self) -> str:
        """Get the frequent topics section title text."""
        return self._get_text_of_element(self.FREQUENT_TOPICS_LOCATORS
                                         ["frequent_topics_section_title"])

    def get_all_frequent_topics_cards(self) -> list[str]:
        """Get the text of all the frequent topics cards."""
        return self._get_text_of_elements(self.FREQUENT_TOPICS_LOCATORS
                                          ["frequent_topic_all_cards"])

    def get_frequent_topics_subtitle_text(self) -> str:
        """Get the frequent topics section subtitle text."""
        return self._get_text_of_element(self.FREQUENT_TOPICS_LOCATORS
                                         ["frequent_topics_section_subtitle"])

    def click_on_a_particular_frequent_topic_card(self, card_title: str):
        """Click on a particular frequent topic card.

        Args:
            card_title (str): The title of the card to click on.
        """
        self._click(f"//h2[contains(text(),'Frequent Topics')]/../../../..//a[normalize-space("
                    f"text())='{card_title}']")

    def get_featured_articles_header_text(self) -> str:
        """Get the featured articles section title text."""
        return self._get_text_of_element(self.FEATURE_ARTICLE_LOCATORS
                                         ["featured_article_section_title"])

    def is_featured_articles_section_displayed(self) -> bool:
        """Check if the featured articles section is displayed on the page."""
        return self._is_element_visible(self.FEATURE_ARTICLE_LOCATORS
                                        ["featured_article_section_title"])

    def get_list_of_featured_articles_headers(self) -> list[str]:
        """Get the text of all the featured articles cards."""
        return self._get_text_of_elements(self.FEATURE_ARTICLE_LOCATORS["featured_articles_cards"])

    def get_feature_articles_count(self) -> int:
        """Get the count of the featured articles."""
        return len(self._get_text_of_elements(self.FEATURE_ARTICLE_LOCATORS
                                              ["featured_articles_cards"]))

    def click_on_a_particular_feature_article_card(self, card_title):
        """Click on a particular featured article card.

        Args:
            card_title (str): The title of the card to click on.
        """
        self._click(f'//h2[contains(text(),"Featured Articles")]/..//a[normalize-space(text())'
                    f'="{card_title}"]')

    def is_still_need_help_widget_displayed(self) -> bool:
        """Check if the still need help widget is displayed on the page."""
        return self._is_element_visible(self.STILL_NEED_HELP_WIDGET_LOCATORS
                                        ["still_need_help_widget"])

    def get_still_need_help_widget_title(self) -> str:
        """Get the still need help widget title text."""
        return self._get_text_of_element(self.STILL_NEED_HELP_WIDGET_LOCATORS
                                         ["still_need_help_widget_title"])

    def get_still_need_help_widget_content(self) -> str:
        """Get the still need help widget content text."""
        return self._get_text_of_element(self.STILL_NEED_HELP_WIDGET_LOCATORS
                                         ["still_need_help_widget_details"])

    def get_still_need_help_widget_button_text(self) -> str:
        """Get the text of the still need help widget button."""
        return self._get_text_of_element(self.STILL_NEED_HELP_WIDGET_LOCATORS
                                         ["ask_the_community_still_need_help_widget"])

    def click_still_need_help_widget_button(self):
        """Click on the still need help widget button."""
        self._click(self.STILL_NEED_HELP_WIDGET_LOCATORS
                    ["ask_the_community_still_need_help_widget"])

    def get_join_our_community_header_text(self) -> str:
        """Get the join our community section header text."""
        return self._get_text_of_element(self.JOIN_OUR_COMMUNITY_LOCATORS
                                         ["join_our_community_section_header"])

    def get_join_our_community_content_text(self) -> str:
        """Get the join our community section content text."""
        return self._get_text_of_elements(
            self.JOIN_OUR_COMMUNITY_LOCATORS
            ["join_our_community_section_paragraph_and_learn_more_option"]
        )[0]

    def click_join_our_community_learn_more_link(self):
        """Click on the learn more link in the join our community section."""
        return (self._click_on_an_element_by_index
                (self.JOIN_OUR_COMMUNITY_LOCATORS
                 ["join_our_community_section_paragraph_and_learn_more_option"], 1)
                )
