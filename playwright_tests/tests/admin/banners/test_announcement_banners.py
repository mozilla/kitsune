import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.models.admin_banner_data import AdminBannerData
from playwright_tests.pages.sumo_pages import SumoPages
from playwright_tests.tests.admin.conftest import create_announcement_banner


# C2944342
@pytest.mark.adminAnnouncementBanners
def test_site_wide_announcements_are_visible_for_all_users(page: Page, create_user_factory,
                                                           create_announcement_banner):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    test_user = create_user_factory()
    banner_text = "Test Banner " + utilities.generate_random_number(1, 1000)
    banner = AdminBannerData(content=banner_text)
    banner_id = create_announcement_banner(banner)

    with check, allure.step("Verifying that the banner contains the expected text while not logged"
                            " in"):
        utilities.refresh_page()
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)
               ).to_have_text(banner_text)

    with check, allure.step("Navigating to a different page and verifying that the correct banner "
                            "is displayed"):
        sumo_pages.homepage.click_on_product_card_by_title("Firefox")
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)
               ).to_have_text(banner_text)

    with allure.step("Signing in with a normal test user and verifying that the correct banner "
                     "is displayed"):
        utilities.start_existing_session(test_user)
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)
               ).to_have_text(banner_text)

# C3248626
@pytest.mark.adminAnnouncementBanners
def test_product_specific_banner_visibility(page: Page, create_user_factory,
                                            create_announcement_banner):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)
    banner_text = "Firefox Banner " + utilities.generate_random_number(1, 1000)
    banner = AdminBannerData(content=banner_text, target_product="Firefox")
    banner_id = create_announcement_banner(banner)
    test_user = create_user_factory()

    test_cases = [
        ("Homepage", HomepageMessages.STAGE_HOMEPAGE_URL_EN_US, "hidden"),
        ("Firefox support page",
         utilities.general_test_data['product_support']['Firefox'], "visible"),
        ("Firefox solutions page",
         utilities.general_test_data['product_solutions']['Firefox'], "visible"),
        ("Firefox topics page",
         utilities.general_test_data['product_topics']['Firefox'], "visible"),
        ("Firefox contact form",
         utilities.aaq_question_test_data['products_aaq_url']['Firefox'], "visible"),
        ("Firefox for Android support page",
         utilities.general_test_data['product_support']['Firefox for Android'], "hidden"),
        ("Firefox for Android solutions page",
         utilities.general_test_data['product_solutions']['Firefox for Android'], "hidden"),
        ("Firefox for Android topics page",
         utilities.general_test_data['product_topics']['Firefox for Android'], "hidden"),
        ("Firefox for Android contact form",
         utilities.aaq_question_test_data['products_aaq_url']['Firefox for Android'], "hidden"),
    ]

    utilities.start_existing_session(test_user)
    for name, url, visibility in test_cases:
        with check, allure.step(f"Verifying banner on {name}"):
            utilities.navigate_to_link(url)

            if visibility == "visible":
                expect(sumo_pages.common_web_elements.announcement_banner(banner_id)
                       ).to_have_text(banner_text)
            else:
                expect(sumo_pages.common_web_elements.announcement_banner(banner_id)
                       ).to_be_hidden()


#  C2091903, C2084006
@pytest.mark.adminAnnouncementBanners
def test_banners_targeting_groups_and_locales(page: Page, create_user_factory,
                                              create_announcement_banner):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    targeted_group_user = create_user_factory(groups=['TestGroup1'])
    other_group_user = create_user_factory(groups=['TestGroup2'])
    banner_text = "Group Banner " + utilities.generate_random_number(1, 1000)
    banner = AdminBannerData(content=banner_text, target_groups=['TestGroup1'], target_locale='ro')
    banner_id = create_announcement_banner(banner)

    with check, allure.step("Signing in with the targeted group user and verifying that the banner"
                            " is not displayed on a non-targeted locale"):
        utilities.start_existing_session(targeted_group_user)
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)).to_be_hidden()

    with check, allure.step("Switching the locale to the targeted locale and verifying tha the"
                            " banner is displayed"):
        sumo_pages.footer_section.switch_to_a_locale('ro')
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)
               ).to_have_text(banner_text)

    with check, allure.step("Signing in with a user belonging to a non-targeted group and "
                            "verifying that the banner is not displayed"):
        utilities.start_existing_session(other_group_user)
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)).to_be_hidden()


# C3071204
@pytest.mark.adminAnnouncementBanners
def test_banners_closed_state(page: Page, create_announcement_banner, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    banner_text = "Close Banner " + utilities.generate_random_number(1, 1000)
    banner = AdminBannerData(content=banner_text)
    banner_id = create_announcement_banner(banner)
    test_user = create_user_factory()

    with allure.step("Closing the announcement banner and verifying that the banner is not "
                     "displayed"):
        utilities.start_existing_session(test_user)
        sumo_pages.common_web_elements.click_on_announcement_banner_close_button(banner_id)
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)).to_be_hidden()

    with check, allure.step("Navigating to a different page and verifying that the correct banner "
                            "is not displayed"):
        sumo_pages.homepage.click_on_product_card_by_title("Firefox")
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)).to_be_hidden()

    with allure.step("Verifying that the correct session storage key is saved"):
        assert utilities.fetch_session_storage_banner_key(banner_id) == 'true'

    with allure.step("Signing out from SUMO and verifying that the banner is not displayed."):
        utilities.delete_cookies()
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)).to_be_hidden()

    with allure.step("Setting the closed session storage key to false, refreshing the page and "
                     "verifying that the banner is displayed"):
        utilities.set_session_storage_banner_key(banner_id, 'false')
        utilities.refresh_page()
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)).to_be_visible()

    with allure.step("Signing in back and verifying that the banner is successfully displayed"):
        utilities.start_existing_session(test_user)
        expect(sumo_pages.common_web_elements.announcement_banner(banner_id)).to_be_visible()
