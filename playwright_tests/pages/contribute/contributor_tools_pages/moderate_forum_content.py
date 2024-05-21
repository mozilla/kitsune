from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class ModerateForumContent(BasePage):

    # View all deactivated users button
    __view_all_deactivated_users_button = "//div[@class='sumo-button-wrap']/a"

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_flagged_question_locator(self, question_title) -> Locator:
        return super()._get_element_locator(f"//p[text()='{question_title}']")

    def _get_flag_reason(self, question_title: str) -> str:
        return super()._get_text_of_element(f"//p[text()='{question_title}']/../"
                                            f"preceding-sibling::hgroup/h2")

    def _get_flagged_question_content(self, question_title: str) -> str:
        return super()._get_text_of_element(f"//p[text()='{question_title}']/"
                                            f"following-sibling::div[@class='content']/p")

    def _get_created_by_link_text(self, question_title: str) -> str:
        return super()._get_text_of_element(f"//p[text()='{question_title}']/"
                                            f"following-sibling::p[@class='created']/a")

    def _click_created_by_link(self, question_title: str):
        super()._click(f"//p[text()='{question_title}']/"
                       f"following-sibling::p[@class='created']/a")

    def _get_flagged_by_link_text(self, question_title: str) -> str:
        return super()._get_text_of_element(f"//p[text()='{question_title}']/"
                                            f"following-sibling::p[@class='flagged']/a")

    def _click_flagged_by_link(self, question_title: str):
        super()._click(f"//p[text()='{question_title}']/"
                       f"following-sibling::p[@class='flagged']/a")

    def _click_take_action_view_option(self, question_title: str):
        super()._click(f"//p[text()='{question_title}']/following-sibling::div/a[text()='View']")

    def _click_take_action_edit_option(self, question_title: str):
        super()._click(f"//p[text()='{question_title}']/following-sibling::div/a[text()='Edit']")

    def _click_take_action_delete_option(self, question_title: str):
        super()._click(f"//p[text()='{question_title}']/following-sibling::div/a[text()='Delete']")

    def _select_update_status_option(self, question_title: str, select_value: str):
        super()._select_option_by_label(f"//p[text()='{question_title}']/"
                                        f"following-sibling::form/select", select_value)

    def _click_on_the_update_button(self, questions_title: str):
        super()._click(f"//p[text()='{questions_title}']/following-sibling::form/"
                       f"input[@value='Update']")

    def _click_view_all_deactivated_users_button(self):
        super()._click(self.__view_all_deactivated_users_button)
