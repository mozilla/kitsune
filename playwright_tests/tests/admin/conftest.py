import pytest

from playwright_tests.core.utilities import Utilities
from playwright_tests.models.admin_banner_data import AdminBannerData
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.fixture()
def create_admin_context(page, request):
    def _create_admin_context():
        return Utilities(page).create_new_context_page()
    return _create_admin_context

@pytest.fixture()
def create_announcement_banner(create_admin_context, request):
    admin_page = create_admin_context()
    utilities = Utilities(admin_page)
    sumo_pages = SumoPages(admin_page)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    def _create_announcement_banner(banner: AdminBannerData):
        utilities.navigate_to_homepage()
        utilities.start_existing_session(session_file_name=staff_user)
        utilities.navigate_to_link(utilities.different_endpoints['admin_announcement_page'])
        banner_id = sumo_pages.admin_banner_flows.create_new_banner_flow(banner)
        return banner_id
    yield _create_announcement_banner

    sumo_pages.admin_banner_flows.delete_new_banner_flow()


@pytest.fixture()
def navigate_to_users_admin_page(create_admin_context, request):
    admin_page = create_admin_context()
    utilities = Utilities(admin_page)
    sumo_pages = SumoPages(admin_page)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    def _access_admin_users_page(username: str):
        utilities.navigate_to_homepage()
        utilities.start_existing_session(session_file_name=staff_user)
        utilities.navigate_to_link(utilities.different_endpoints['admin_announcement_page'])
        sumo_pages.admin_users_flows.navigate_to_a_particular_user_profile_in_admin(username)
        return admin_page
    yield _access_admin_users_page

