from playwright.sync_api import Page
from playwright_tests.core.basepage import BasePage


class CommunityHubPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # Locators belonging to the Community Hub searchbar.
        self.find_contributor_searchbar = page.locator(
            "//form[@id='find-contributor']//input[@id='search']")

        # Locators belonging to search result cards
        self.user_titles_from_returned_cards = page.locator(
            "section[class='card elevation-01 results-user'] h2[class='card--title']")


    def search_for_contributor(self, search_string: str):
        """
        Search for a contributor

        Args:
            search_string (str): Search string.
        """
        self._fill(self.find_contributor_searchbar, search_string)
        self._press_a_key(self.find_contributor_searchbar, "Enter")

    def clear_search(self):
        """Clear the searchbar."""
        self._clear_field(self.find_contributor_searchbar)

    def get_all_users_from_user_cards(self) -> list[str]:
        """Returns all user titles from user cards."""
        return self._get_text_of_elements(self.user_titles_from_returned_cards)

