import random
from typing import Literal
from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class CommonWebElements(BasePage):
    AVOID_SPAM_BANNER = {
        "scam_banner": "//div[@id='id_scam_alert']",
        "scam_banner_text": "//div[@id='id_scam_alert']//p[@class='heading']",
        "learn_more_button": "//div[@id='id_scam_alert']//a"
    }

    # Frequent Topics locators applicable to product & product solutions pages.
    FREQUENT_TOPICS_LOCATORS = {
        "frequent_topics_section_title": "//h2[normalize-space(text())= 'Topics']",
        "frequent_topics_section_subtitle": "//h2[normalize-space(text())='Topics']/following-"
                                            "sibling::p",
        "frequent_topic_card_headers": "//div[@class='card--topic']/div[@class='topic-header']/"
                                       "h3[@class='card--title']/a",
        "frequent_topic_card_header": lambda card_title:
        f"//div[@class='card--topic']/div[@class='topic-header']/h3[@class='card--title']"
        f"/a[normalize-space(text())='{card_title}']",
        "frequent_topic_card_articles": lambda card_title:
        f"//div[@class='card--topic']/div[@class='topic-header']/h3/a[normalize-space(text())="
        f"'{card_title}']/../../following-sibling::ul/li/a",
        "frequent_topic_card_article": lambda card_title, article_title:
        f'//div[@class="card--topic"]/div[@class="topic-header"]/h3/a[normalize-space(text())='
        f'"{card_title}"]/../..//following-sibling::ul/li/a[normalize-space(text())='
        f'"{article_title}"]',
        "frequent_topic_view_all_articles": lambda card_title:
        f"//div[@class='card--topic']/div[@class='topic-header']/h3[@class='card--title']/"
        f"a[normalize-space(text())='{card_title}']/../../following-sibling::a"
    }

    def __init__(self, page: Page):
        super().__init__(page)

    # Actions against the Avoid Spam Banner
    def get_scam_banner_text(self) -> str:
        """Returns the scam banner text."""
        return self._get_text_of_element(self.AVOID_SPAM_BANNER["scam_banner_text"])

    def is_frequent_topics_section_displayed(self) -> bool:
        """Check if the frequent topics section is displayed on the page."""
        return self._is_element_visible(self.FREQUENT_TOPICS_LOCATORS
                                        ["frequent_topics_section_title"])

    def get_frequent_topic_card_titles(self) -> list[str]:
        """Get the text of all the frequent topic cards."""
        return self._get_text_of_elements(self.FREQUENT_TOPICS_LOCATORS
                                          ['frequent_topic_card_headers'])

    def is_frequent_topic_card_displayed(self, card_title: str) -> bool:
        """Check if a particular frequent topic card is displayed."""
        return self._is_element_visible(self.FREQUENT_TOPICS_LOCATORS
                                        ['frequent_topic_card_header'](card_title))

    def click_on_frequent_topic_card_title(self, topic_card_title: str):
        """Click on a particular frequent topic card."""
        self._click(self.FREQUENT_TOPICS_LOCATORS['frequent_topic_card_header'](topic_card_title))

    def get_frequent_topic_card_articles(self, card_title: str) -> list[str]:
        """Get the text of all the articles in a frequent topic card."""
        return self._get_text_of_elements(self.FREQUENT_TOPICS_LOCATORS
                                          ['frequent_topic_card_articles'](card_title))

    def click_on_a_frequent_topic_card_article(self, card_title: str, article_title: str):
        """Click on a particular article in a frequent topic card."""
        self._click(self.FREQUENT_TOPICS_LOCATORS['frequent_topic_card_article'](
            card_title, article_title))

    def get_frequent_topic_card_view_all_articles_link_text(self, card_title: str):
        """Get the text of the view all articles link in a frequent topic card."""
        return self._get_text_of_element(self.FREQUENT_TOPICS_LOCATORS
                                         ['frequent_topic_view_all_articles'](card_title))

    def click_frequent_topic_card_view_all_articles_link(self, card_title: str):
        """Click on the view all articles link in a frequent topic card."""
        self._click(self.FREQUENT_TOPICS_LOCATORS['frequent_topic_view_all_articles'](card_title))

    def get_frequent_topics_title_text(self) -> str:
        """Get the frequent topics section title text."""
        return self._get_text_of_element(self.FREQUENT_TOPICS_LOCATORS
                                         ["frequent_topics_section_title"])

    def get_frequent_topics_subtitle_text(self) -> str:
        """Get the frequent topics section subtitle text."""
        return self._get_text_of_element(self.FREQUENT_TOPICS_LOCATORS
                                         ["frequent_topics_section_subtitle"])

    def verify_topic_card_redirect(self, utilities, sumo_pages, card: str,
                                   verification_type: Literal["heading", "article", "counter"]
                                   ) -> bool:
        if verification_type == "heading":
            self.click_on_frequent_topic_card_title(card)
            if sumo_pages.product_topics_page.get_page_title() != card:
                return False
        elif verification_type == "article":
            listed_articles = sumo_pages.common_web_elements.get_frequent_topic_card_articles(
                card)
            random_article = random.choice(listed_articles)
            sumo_pages.common_web_elements.click_on_a_frequent_topic_card_article(
                card,random_article)
            if sumo_pages.kb_article_page.get_text_of_article_title() != random_article:
                return False
        elif verification_type == "counter":
            counter = utilities.number_extraction_from_string(
                sumo_pages.common_web_elements.get_frequent_topic_card_view_all_articles_link_text(
                    card))
            sumo_pages.common_web_elements.click_frequent_topic_card_view_all_articles_link(card)
            listed_articles = sumo_pages.product_topics_page.get_all_listed_article_titles()
            if sumo_pages.product_topics_page.get_page_title() != card and len(listed_articles
                                                                               ) != counter:
                return False
        utilities.navigate_back()
        return True
