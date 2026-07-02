from playwright_tests.messages.homepage_messages import HomepageMessages


class ModerateForumContentPageMessages:
    PAGE_URL = HomepageMessages.STAGE_HOMEPAGE_URL_EN_US + "flagged"
    DEACTIVATED_USERS_PAGE_URL = HomepageMessages.STAGE_HOMEPAGE_URL_EN_US + (
        "users/deactivation_log")
    UPDATE_STATUS_FIRST_VALUE = "1"
    UPDATE_STATUS_SECOND_VALUE = "2"
    SIDEBAR_OPTION_NAME = "Moderate forum content"
