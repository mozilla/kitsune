import pytest

from playwright_tests.core.utilities import Utilities
from playwright_tests.models.admin_banner_data import AdminBannerData
from playwright_tests.pages.sumo_pages import SumoPages


@pytest.fixture()
def create_admin_context(browser, request):
    admin_context = browser.new_context(user_agent=f"{Utilities.user_agent}")
    admin_page = admin_context.new_page
    return admin_page

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
