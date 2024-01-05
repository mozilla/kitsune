from playwright.sync_api import Page, Locator
from playwright_tests.core.basepage import BasePage


class ModerateForumContent(BasePage):

    # View all deactivated users button
    __view_all_deactivated_users_button = "//div[@class='sumo-button-wrap']/a"

    def __init__(self, page: Page):
        super().__init__(page)

    def _get_flagged_question_locator(self, question_title) -> Locator:
        xpath = f"//p[text()='{question_title}']"
        return super()._get_element_locator(xpath)

    def _get_flag_reason(self, question_title: str) -> str:
        xpath = f"//p[text()='{question_title}']/../preceding-sibling::hgroup/h2"
        return super()._get_text_of_element(xpath)

    def _get_flagged_question_content(self, question_title: str) -> str:
        xpath = f"//p[text()='{question_title}']/following-sibling::div[@class='content']/p"
        return super()._get_text_of_element(xpath)

    def _get_created_by_link_text(self, question_title: str) -> str:
        xpath = f"//p[text()='{question_title}']/following-sibling::p[@class='created']/a"
        return super()._get_text_of_element(xpath)

    def _click_created_by_link(self, question_title: str):
        xpath = f"//p[text()='{question_title}']/following-sibling::p[@class='created']/a"
        super()._click(xpath)

    def _get_flagged_by_link_text(self, question_title: str) -> str:
        xpath = f"//p[text()='{question_title}']/following-sibling::p[@class='flagged']/a"
        return super()._get_text_of_element(xpath)

    def _click_flagged_by_link(self, question_title: str):
        xpath = f"//p[text()='{question_title}']/following-sibling::p[@class='flagged']/a"
        super()._click(xpath)

    def _click_take_action_view_option(self, question_title: str):
        xpath = f"//p[text()='{question_title}']/following-sibling::div/a[text()='View']"
        super()._click(xpath)

    def _click_take_action_edit_option(self, question_title: str):
        xpath = f"//p[text()='{question_title}']/following-sibling::div/a[text()='Edit']"
        super()._click(xpath)

    def _click_take_action_delete_option(self, question_title: str):
        xpath = f"//p[text()='{question_title}']/following-sibling::div/a[text()='Delete']"
        super()._click(xpath)

    def _select_update_status_option(self, question_title: str, select_value: str):
        xpath = f"//p[text()='{question_title}']/following-sibling::form/select"
        super()._select_option_by_label(xpath, select_value)

    def _click_on_the_update_button(self, questions_title: str):
        xpath = f"//p[text()='{questions_title}']/following-sibling::form/input[@value='Update']"
        super()._click(xpath)

    def _click_view_all_deactivated_users_button(self):
        super()._click(self.__view_all_deactivated_users_button)
