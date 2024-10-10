from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class ModerateForumContent(BasePage):
    # View all deactivated users button
    __view_all_deactivated_users_button = "//div[@class='sumo-button-wrap']/a"

    def __init__(self, page: Page):
        super().__init__(page)

    def get_flagged_question_locator(self, question_info) -> Locator:
        return self._get_element_locator(f"//p[normalize-space(text())='{question_info}']")

    def get_flag_reason(self, question_title: str) -> str:
        return self._get_text_of_element(f"//p[text()='{question_title}']/../"
                                         f"preceding-sibling::hgroup/h2")

    def get_flagged_question_content(self, question_title: str) -> str:
        return self._get_text_of_element(f"//p[text()='{question_title}']/"
                                         f"following-sibling::div[@class='content']/p")

    def get_created_by_link_text(self, question_info: str) -> str:
        return self._get_text_of_element(f"//p[normalize-space(text())='{question_info}']/"
                                         f"ancestor::div[@class='flagged-item-content']//"
                                         f"h3[text()='Created:']/following-sibling::p/a")

    def click_created_by_link(self, question_info: str):
        self._click(f"//p[normalize-space(text())='{question_info}']/ancestor::div"
                    f"[@class='flagged-item-content']//h3[text()='Created:']/"
                    f"following-sibling::p/a")

    def get_flagged_by_link_text(self, question_info: str) -> str:
        return self._get_text_of_element(f"//p[normalize-space(text())='{question_info}']/"
                                         f"ancestor::div[@class='flagged-item-content']//"
                                         f"h3[text()='Flagged:']/following-sibling::p/a")

    def click_flagged_by_link(self, question_info: str):
        self._click(f"//p[normalize-space(text())='{question_info}']/ancestor::div"
                    f"[@class='flagged-item-content']//h3[text()='Flagged:']/"
                    f"following-sibling::p/a")

    def click_take_action_view_option(self, question_info: str):
        self._click(f"//p[text()='{question_info}']/following-sibling::div/a[text()='View']")

    def click_take_action_edit_option(self, question_info: str):
        self._click(f"//p[normalize-space(text())='{question_info}']/ancestor::div"
                    f"[@class='flagged-item-content']//a[text()='Edit']")

    def click_take_action_delete_option(self, question_info: str):
        self._click(f"//p[normalize-space(text())='{question_info}']/ancestor::div"
                    f"[@class='flagged-item-content']//a[text()='Delete']")

    def select_update_status_option(self, question_info: str, select_value: str):
        self._select_option_by_value(f"//p[normalize-space(text())='{question_info}']"
                                     f"/ancestor::div[@class='flagged-item-content']//"
                                     f"following-sibling::form/select", select_value)

    def click_on_the_update_button(self, question_info: str):
        self._click(f"//p[normalize-space(text())='{question_info}']/ancestor::div"
                    f"[@class='flagged-item-content']//following-sibling::form/input"
                    f"[@value='Update']")

    def click_view_all_deactivated_users_button(self):
        self._click(self.__view_all_deactivated_users_button)
