from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class AdminGroupsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the groups listing page."""
        self.searchbar = page.locator("input#searchbar")
        self.search_submit_button = page.locator("input[type='submit']")
        self.group = lambda group_name: page.locator(
            f"//table[@id='result_list']//th//a[normalize-space(text())='{group_name}']")

        """Locators belonging to the add/change group pages."""
        self.name_input_field = page.locator("input#id_name")
        self.save_button = page.locator("input[name='_save']")

        """Locators belonging to the group deletion flow."""
        self.delete_button = page.locator("a.deletelink")
        self.confirm_deletion_button = page.locator(
            "form:has(input[name='post'][value='yes']) input[type='submit']")

    """Actions against the groups admin page locators."""
    def search_for_group(self, group_name: str):
        """Search for a particular group inside the groups admin page.

        Args:
            group_name (str): The group name.
        """
        self._fill(self.searchbar, group_name)
        self._click(self.search_submit_button)

    def click_on_a_group(self, group_name: str):
        """Click on a group name from the groups admin page table.

        Args:
            group_name (str): The group name.
        """
        self._click(self.group(group_name))

    def is_group_listed(self, group_name: str) -> bool:
        """Check if a group is listed inside the groups admin page table.

        Args:
            group_name (str): The group name.
        """
        return self._is_element_visible(self.group(group_name))

    def add_text_to_name_field(self, group_name: str):
        """Fill the group name field.

        Args:
            group_name (str): The group name.
        """
        self._fill(self.name_input_field, group_name)

    def click_on_save_button(self):
        self._click(self.save_button)

    def click_on_delete_button(self):
        self._click(self.delete_button)

    def click_on_confirm_deletion_button(self):
        self._click(self.confirm_deletion_button)
