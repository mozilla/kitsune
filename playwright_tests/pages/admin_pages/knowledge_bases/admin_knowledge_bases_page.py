from playwright.sync_api import Page

from playwright_tests.core.basepage import BasePage


class AdminKnowledgeBasesPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        """Locators belonging to the knowledge bases listing page."""
        self.knowledge_base = lambda name: page.locator(
            f"//table[@id='result_list']/tbody//th//a[normalize-space(text())='{name}']")

        """Locators belonging to the add/change knowledge base pages."""
        self.name_input_field = page.locator("input#id_name")
        self.slug_input_field = page.locator("input#id_slug")
        self.is_public_checkbox = page.locator("input#id_is_public")
        self.groups_select = page.locator("select#id_groups")
        self.save_button = page.locator("input[name='_save']")

        """Locators belonging to the knowledge base deletion flow."""
        self.delete_button = page.locator("a.deletelink")
        self.confirm_deletion_button = page.locator(
            "form:has(input[name='post'][value='yes']) input[type='submit']")

    """Actions against the knowledge bases admin page locators."""
    def is_knowledge_base_listed(self, name: str) -> bool:
        """Check if a knowledge base is listed inside the knowledge bases admin page table.

        Args:
            name (str): The knowledge base name.
        """
        return self._is_element_visible(self.knowledge_base(name))

    def click_on_a_knowledge_base(self, name: str):
        """Click on a knowledge base name from the knowledge bases admin page table.

        Args:
            name (str): The knowledge base name.
        """
        self._click(self.knowledge_base(name))

    def add_text_to_name_field(self, name: str):
        self._fill(self.name_input_field, name)

    def add_text_to_slug_field(self, slug: str):
        self._fill(self.slug_input_field, slug)

    def select_groups(self, group_names: list[str]):
        """Select the groups whose members can read the knowledge base.

        Args:
            group_names (list[str]): The group names.
        """
        self.groups_select.select_option(label=group_names)

    def click_on_save_button(self):
        self._click(self.save_button)

    def click_on_delete_button(self):
        self._click(self.delete_button)

    def click_on_confirm_deletion_button(self):
        self._click(self.confirm_deletion_button)
