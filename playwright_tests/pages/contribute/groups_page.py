from playwright_tests.core.basepage import BasePage
from playwright.sync_api import Page, Locator


class GroupsPage(BasePage):
    __private_message_group_members_button = "//section[@id='main-area']/p[@class='pm']/a"
    __user_added_notification = "//ul[@class='user-messages']//p"
    __edit_group_members_option = "//div[@id='group-members']/a"
    __add_group_member_field = "//div[@id='group-members']//input[@id='token-input-id_users']"
    __add_member_button = "//div[@id='group-members']//input[@value='Add Member']"
    __remove_user_from_group_confirmation_button = "//input[@value='Remove member']"

    def __init__(self, page: Page):
        super().__init__(page)

    # Add Group member
    def _get_user_added_successfully_message(self) -> str:
        return super()._get_text_of_element(self.__user_added_notification)

    def _get_pm_group_members_button(self) -> Locator:
        return super()._get_element_locator(self.__private_message_group_members_button)

    def _click_on_a_particular_group(self, group_name):
        super()._click(f"//a[text()='{group_name}']")

    def _click_on_pm_group_members_button(self):
        super()._click(self.__private_message_group_members_button)

    def _click_on_edit_group_members(self):
        super()._click(self.__edit_group_members_option)

    def _click_on_remove_a_user_from_group_button(self, username: str):
        super()._click(f"//div[@class='info']/a[text()='{username}']/../..//a"
                       f"[@title='Remove user from group']")

    def _click_on_remove_member_confirmation_button(self):
        super()._click(self.__remove_user_from_group_confirmation_button)

    def _type_into_add_member_field(self, text: str):
        super()._type(self.__add_group_member_field, text, delay=0)

    def _group_click_on_a_searched_username(self, username: str):
        super()._click(f"//div[@class='name_search']/b[text()='{username}']")

    def _click_on_add_member_button(self):
        super()._click(self.__add_member_button)
