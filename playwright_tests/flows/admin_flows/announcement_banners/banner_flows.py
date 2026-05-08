from typing import Callable, Any, Dict
from playwright.sync_api import Page

from playwright_tests.core.utilities import Utilities
from playwright_tests.models.admin_banner_data import AdminBannerData
from playwright_tests.pages.admin_pages.announcement_banners.announcement_banner_page import \
    AnnouncementBannerAdminPage


class BannerFlows:
    def __init__(self, page: Page):
        self.utilities = Utilities(page)
        self.banner_admin_page = AnnouncementBannerAdminPage(page)

    def create_new_banner_flow(self, banner: AdminBannerData):
        self.banner_admin_page.click_on_add_announcement_button()

        field_map: Dict[str, Callable[[Any], None]] = {
            "start_display_date": self.banner_admin_page.set_start_displaying_date,
            "start_display_time": self.banner_admin_page.set_start_displaying_time,
            "stop_display_date": self.banner_admin_page.stop_displaying_date,
            "stop_display_time": self.banner_admin_page.stop_displaying_time,
            "target_groups": self.banner_admin_page.set_banner_target_groups,
            "target_locale": self.banner_admin_page.set_banner_target_locale,
            "target_platforms": self.banner_admin_page.set_banner_target_platforms,
            "target_product": self.banner_admin_page.set_banner_target_product
        }

        for field, setter in field_map.items():
            value = getattr(banner, field)
            if value:
                setter(value)

        self.banner_admin_page.set_banner_content(banner.content)
        self.banner_admin_page.click_on_save_new_banner_button()
        self.utilities.wait_for_dom_to_load()
        return str(self.utilities.number_extraction_from_string(self.utilities.get_page_url()))

    def delete_new_banner_flow(self):
        self.banner_admin_page.click_on_delete_new_banner_button()
        self.banner_admin_page.click_on_delete_confirm_button()

