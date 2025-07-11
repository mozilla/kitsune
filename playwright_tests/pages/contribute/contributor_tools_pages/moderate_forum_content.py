from playwright.sync_api import Locator, Page

from playwright_tests.core.basepage import BasePage


class ModerateForumContent(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # View all deactivated users button
        self.view_all_deactivated_users_button = page.locator("div[class='sumo-button-wrap'] a")

        # Flagged questions
        self.flagged_question = lambda question_info: page.locator("p").get_by_text(
            question_info, exact=True)
        self.flagged_reason = lambda question_title: page.locator(
            f"//p[text()='{question_title}']/../preceding-sibling::hgroup/h2")
        self.flagged_question_content = lambda question_title: page.locator("p").get_by_text(
            question_title, exact=True).locator("> div[class='content'] p")
        self.created_by_link_text = lambda question_info: page.locator(
            f"//p[normalize-space(text())='{question_info}']/ancestor::div"
            f"[@class='flagged-item-content']//h3[text()='Created:']/following-sibling::p/a")
        self.flagged_by_link_text = lambda question_info: page.locator(
            f"//p[normalize-space(text())='{question_info}']/ancestor::div"
            f"[@class='flagged-item-content']//h3[text()='Flagged:']/following-sibling::p/a")
        self.take_action_view_option = lambda question_info: page.get_by_role(
            "paragraph", name=question_info, exact=True).locator("+ div").get_by_role(
            "link", name="View", exact=True)
        self.take_action_edit_option = lambda question_info: page.locator(
            f"//p[normalize-space(text())='{question_info}']/ancestor::"
            f"div[@class='flagged-item-content']//a[text()='Edit']")
        self.take_action_delete_option = lambda question_info: page.locator(
            f"//p[normalize-space(text())='{question_info}']/ancestor::div"
            f"[@class='flagged-item-content']//a[text()='Delete']")
        self.update_status_option = lambda question_info: page.locator(
            f"//p[normalize-space(text())='{question_info}']/ancestor::div"
            f"[@class='flagged-item-content']//following-sibling::form/select")
        self.update_status_button = lambda question_info: page.locator(
            f"//p[normalize-space(text())='{question_info}']/ancestor::div"
            f"[@class='flagged-item-content']//following-sibling::form/input[@value='Update']")

    def get_flagged_question_locator(self, question_info) -> Locator:
        return self.flagged_question(question_info)

    def get_flag_reason(self, question_title: str) -> str:
        return self._get_text_of_element(self.flagged_reason(question_title))

    def get_flagged_question_content(self, question_title: str) -> str:
        return self._get_text_of_element(self.flagged_question_content(question_title))

    def get_created_by_link_text(self, question_info: str) -> str:
        return self._get_text_of_element(self.created_by_link_text(question_info))

    def click_created_by_link(self, question_info: str):
        self._click(self.created_by_link_text(question_info))

    def get_flagged_by_link_text(self, question_info: str) -> str:
        return self._get_text_of_element(self.flagged_by_link_text(question_info))

    def click_flagged_by_link(self, question_info: str):
        self._click(self.flagged_by_link_text(question_info))

    def click_take_action_view_option(self, question_info: str):
        self._click(self.take_action_view_option(question_info))

    def click_take_action_edit_option(self, question_info: str):
        self._click(self.take_action_edit_option(question_info))

    def click_take_action_delete_option(self, question_info: str):
        self._click(self.take_action_delete_option(question_info))

    def select_update_status_option(self, question_info: str, select_value: str):
        self._select_option_by_value(self.update_status_option(question_info), select_value)

    def click_on_the_update_button(self, question_info: str):
        self._click(self.update_status_button(question_info))

    def click_view_all_deactivated_users_button(self):
        self._click(self.view_all_deactivated_users_button)
