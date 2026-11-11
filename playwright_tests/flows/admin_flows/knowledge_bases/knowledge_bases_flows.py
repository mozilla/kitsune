from playwright.sync_api import Page
from slugify import slugify

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.admin_pages.knowledge_bases.admin_knowledge_bases_page import (
    AdminKnowledgeBasesPage,
)


class AdminKnowledgeBasesFlows:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.knowledge_bases_page = AdminKnowledgeBasesPage(page)

    def is_knowledge_base_listed(self, name: str) -> bool:
        """Report whether a knowledge base with the given name exists.

        Args:
            name (str): The knowledge base name.
        """
        self.utilities.navigate_to_link(
            self.utilities.different_endpoints["admin_knowledge_bases_page"])
        return self.knowledge_bases_page.is_knowledge_base_listed(name)

    def create_private_knowledge_base(self, name: str, group_names: list[str]) -> str:
        """Flow for creating a private knowledge base readable by the given groups.

        Args:
            name (str): The knowledge base name, also used to derive its slug.
            group_names (list[str]): The groups whose members can read its articles.
        """
        self.utilities.navigate_to_link(
            self.utilities.different_endpoints["admin_knowledge_bases_page"] + "add/")
        self.knowledge_bases_page.add_text_to_name_field(name)
        self.knowledge_bases_page.add_text_to_slug_field(slugify(name))
        self.knowledge_bases_page.select_groups(group_names)
        self.knowledge_bases_page.click_on_save_button()
        return name

    def delete_knowledge_base(self, name: str, ignore_missing: bool = False):
        """Flow for deleting a knowledge base. Only knowledge bases without articles can be
        deleted, since an article's knowledge bases are protected.

        Args:
            name (str): The knowledge base name.
            ignore_missing (bool): If True, a knowledge base which is no longer listed is
                skipped instead of failing.
        """
        if not self.is_knowledge_base_listed(name):
            if ignore_missing:
                return
            raise AssertionError(f"The '{name}' knowledge base is not listed")

        self.knowledge_bases_page.click_on_a_knowledge_base(name)
        self.knowledge_bases_page.click_on_delete_button()
        self.knowledge_bases_page.click_on_confirm_deletion_button()
