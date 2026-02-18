import random
from typing import Literal
from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class CommonWebElements(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the spam banner."""
        self.scam_banner = page.locator("div#id_scam_alert")
        self.scam_banner_text = page.locator("div#id_scam_alert p[class='heading']")
        self.learn_more_button = page.locator("div#id_scam_alert").get_by_role("link")

        """Locators belonging to the Still need help widget."""
        self.aaq_widget = page.locator("div[class*='aaq-widget']")
        self.aaq_button = page.locator("div[class*='aaq-widget']").get_by_role("link")
        self.still_need_help_subheading = page.locator("div.aaq-widget p")

        """Locators belonging to the Learn more card."""
        self.volunteer_learn_more_card_heading = page.locator(
            "//div[@class='card--details']//a[text()='Learn More']//../../../h3")
        self.volunteer_learn_more_card_text = page.locator(
            "//div[@class='card--details']//a[text()='Learn More']//../../preceding-sibling::p")
        self.volunteer_learn_more_link = page.locator(
            "div[class='card--details']").get_by_role("link", name="Learn More")

        # Frequent Topics locators applicable to product & product solutions pages.
        """Locators belonging to the Frequent Topics applicable to product & product solutions
         pages.
         """
        self.frequent_topics_section_title = page.get_by_role(
            "heading", name="Topics", exact=True)
        self.frequent_topics_section_subtitle = page.get_by_role(
            "heading", name="Topics", exact=True).locator("+ p")
        self.frequent_topic_card_headers = page.locator(
            "div[class='card--topic'] div[class='topic-header'] h3[class='card--title'] a")
        self.frequent_topic_card_header = lambda card_title: page.locator(
            "div[class='card--topic'] div[class='topic-header'] h3[class='card--title']"
        ).get_by_role("link", name=card_title)
        self.frequent_topic_card_articles = lambda card_title: page.locator(
            f"//div[@class='card--topic']/div[@class='topic-header']/h3/a[normalize-space(text())="
            f"'{card_title}']/../../following-sibling::ul/li/a")
        self.frequent_topic_card_article = lambda card_title, article_title: page.locator(
            f'//div[@class="card--topic"]/div[@class="topic-header"]/h3/a[normalize-space(text())='
            f'"{card_title}"]/../..//following-sibling::ul/li/a[normalize-space(text())='
            f'"{article_title}"]')
        self.frequent_topic_view_all_articles = lambda card_title: page.locator(
            f"//div[@class='card--topic']/div[@class='topic-header']/h3[@class='card--title']/a"
            f"[normalize-space(text())='{card_title}']/../../following-sibling::a")

        """Locators belonging to the pagination elements."""
        self.pagination_items = page.locator("//ol[@class='pagination']//a")
        self.pagination_item = lambda pagination_item: page.locator(
            f"//ol[@class='pagination']//a[text()={pagination_item}]")
        self.selected_pagination_item = page.locator(
            "ol[class='pagination'] li[class='selected']").get_by_role("link")
        self.previous_pagination_item = page.locator(
            "//ol[@class='pagination']//span[text()='Previous']/..")
        self.next_pagination_item= page.locator(
            "//ol[@class='pagination']//span[text()='Next']/..")

    """Actions against the Avoid Spam banner locators."""
    def get_scam_banner_text(self) -> str:
        """Returns the scam banner text."""
        return self._get_text_of_element(self.scam_banner_text)

    """Actions against the Still Need Help widget locators."""
    def click_on_aaq_button(self):
        """Click on the 'Still Need Help?' button."""
        self._click(self.aaq_button)

    def get_aaq_widget_text(self) -> str:
        """Get the 'Still Need Help?' subheading text."""
        return self._get_text_of_element(self.still_need_help_subheading)

    def get_aaq_widget_button_name(self) -> str:
        return self._get_text_of_element(self.aaq_button)

    """Actions against the learn more section locators."""
    def click_on_volunteer_learn_more_link(self):
        self._click(self.volunteer_learn_more_link)

    def get_volunteer_learn_more_card_text(self) -> str:
        """
            Get the Volunteer learn more card details.
        """
        return self._get_text_of_element(self.volunteer_learn_more_card_text)

    def get_volunteer_learn_more_card_header(self) -> str:
        """
            Get the Volunteer learn more card header.
        """
        return self._get_text_of_element(self.volunteer_learn_more_card_heading)

    """Actions against the Frequent Topics Section locators."""
    def is_frequent_topics_section_displayed(self) -> bool:
        """Check if the frequent topics section is displayed on the page."""
        return self._is_element_visible(self.frequent_topics_section_title)

    def get_frequent_topic_card_titles(self) -> list[str]:
        """Get the text of all the frequent topic cards."""
        return self._get_text_of_elements(self.frequent_topic_card_headers)

    def is_frequent_topic_card_displayed(self, card_title: str) -> bool:
        """Check if a particular frequent topic card is displayed."""
        return self._is_element_visible(self.frequent_topic_card_header(card_title))

    def click_on_frequent_topic_card_title(self, topic_card_title: str):
        """Click on a particular frequent topic card."""
        self._click(self.frequent_topic_card_header(topic_card_title))

    def get_frequent_topic_card_articles(self, card_title: str) -> list[str]:
        """Get the text of all the articles in a frequent topic card."""
        return self._get_text_of_elements(self.frequent_topic_card_articles(card_title))

    def click_on_a_frequent_topic_card_article(self, card_title: str, article_title: str):
        """Click on a particular article in a frequent topic card."""
        self._click(self.frequent_topic_card_article(card_title, article_title))

    def get_frequent_topic_card_view_all_articles_link_text(self, card_title: str):
        """Get the text of the view all articles link in a frequent topic card."""
        return self._get_text_of_element(self.frequent_topic_view_all_articles(card_title))

    def click_frequent_topic_card_view_all_articles_link(self, card_title: str):
        """Click on the view all articles link in a frequent topic card."""
        self._click(self.frequent_topic_view_all_articles(card_title))

    def get_frequent_topics_title_text(self) -> str:
        """Get the frequent topics section title text."""
        return self._get_text_of_element(self.frequent_topics_section_title)

    def get_frequent_topics_subtitle_text(self) -> str:
        """Get the frequent topics section subtitle text."""
        return self._get_text_of_element(self.frequent_topics_section_subtitle)

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

    def click_on_pagination_item(self, pagination_item: str):
        """Clicking on the pagination item"""
        self._click(self.pagination_item(pagination_item))

    def get_selected_pagination_item(self) -> str:
        """Returning the selected pagination item"""
        return self._get_text_of_element(self.selected_pagination_item)

    def click_on_previous_pagination_item(self):
        """Clicking on the previous pagination item."""
        self._click(self.previous_pagination_item)

    def click_on_next_pagination_item(self):
        """Clicking on the next pagination item."""
        self._click(self.next_pagination_item)

    def click_on_last_pagination_item(self):
        """Clicking on the last pagination item."""
        self._click(self.pagination_items.last)

    def is_next_pagination_item_visible(self) -> bool:
        """Return if the next pagination item is visible or not."""
        return self._is_element_visible(self.next_pagination_item)
