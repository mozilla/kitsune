import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages


# C891382, C2266243, C957188, C891370
@pytest.mark.mediaGalleryTests
@pytest.mark.parametrize("user", [None, 'simple_user', 'admin'])
def test_media_gallery_edit_permissions(page: Page, create_user_factory, user):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["Content Moderators", "forum-contributors"])
    media_title = utilities.generate_unique_title()
    media_description = f"Automation test description{utilities.generate_random_number(1, 1000)}"

    with allure.step("Signing in with a content moderator account and uploading an image to the "
                     "media gallery"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.top_navbar.click_on_media_gallery_option()
        sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(title=media_title,
                                                                   description=media_description)
        image_preview_url = utilities.get_page_url()
        sumo_pages.top_navbar.click_on_sumo_nav_logo()

    with allure.step("Signing in with a different contributor user account"):
        if user == "simple_user":
            utilities.start_existing_session(cookies=test_user)
        elif user is None:
            utilities.delete_cookies()

    def verify_no_access(sub_path):
        """A signed-out user is sent to the auth page; a signed-in non-owner gets a 403."""
        if user is None:
            utilities.navigate_to_link(image_preview_url + sub_path)
            expect(sumo_pages.auth_page.auth_page_section).to_be_visible()
        else:
            # navigate_to_link already retries on a 502 and returns the final response, so a
            # transient gateway error is retried instead of being asserted against.
            response = utilities.navigate_to_link(image_preview_url + sub_path)
            assert response is not None and response.status == 403

    with check, allure.step("Verifying that both the 'Delete this image' and 'Edit this image' "
                            "buttons are not available"):
        utilities.navigate_to_link(image_preview_url)
        if user is None or user == "simple_user":
            expect(sumo_pages.media_gallery.edit_this_image_button).to_be_hidden()
            expect(sumo_pages.media_gallery.delete_this_image_button).to_be_hidden()

            with check, allure.step("Navigating to the /edit page and verifying that the user "
                                    "cannot access it"):
                verify_no_access("/edit")

            with check, allure.step("Navigating to the /delete page and verifying that the user "
                                    "cannot access it"):
                verify_no_access("/delete")
        else:
            expect(sumo_pages.media_gallery.edit_this_image_button).to_be_visible()
            expect(sumo_pages.media_gallery.delete_this_image_button).to_be_visible()

# C891369
@pytest.mark.mediaGalleryTests
def test_cancelling_a_media_upload_does_not_upload_the_file(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    media_title = utilities.generate_unique_title()
    media_description = f"Automation test description{utilities.generate_random_number(1, 1000)}"

    with allure.step("Signing in with a contributor account and navigating to the media gallery"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_media_gallery_option()

    with allure.step("Opening the 'Upload a New Media File' panel, adding a media file, filling "
                     "in the title and description fields and clicking on the 'Cancel' button"):
        sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(
            title=media_title, description=media_description, submit=False)

    with allure.step("Searching for the media file and verifying that it was not uploaded"):
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(media_title)
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        expect(sumo_pages.media_gallery.media_file(media_title)).to_be_hidden()


# C2266242
@pytest.mark.mediaGalleryTests
def test_signed_out_users_are_unable_to_upload_media_in_gallery(page:Page):
    sumo_pages = SumoPages(page)
    utilities = Utilities(page)

    with allure.step("Navigating to the media gallery page and verifying that the upload "
                     "button is not displayed"):
        utilities.navigate_to_link(utilities.different_endpoints["media_gallery"])
        expect(sumo_pages.media_gallery.upload_media_button).to_be_hidden()


#  C891384
@pytest.mark.mediaGalleryTests
def test_media_gallery_pagination(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    media_title = utilities.generate_unique_title()
    media_description = f"Automation test description{utilities.generate_random_number(1, 1000)}"

    with allure.step("Signing in with a contributor account and navigating to the media gallery"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_media_gallery_option()

    with allure.step("Verifying that the media gallery pagination is displayed and that we are "
                     "on the first pagination page"):
        expect(sumo_pages.media_gallery.pagination_section).to_be_visible()
        expect(sumo_pages.media_gallery.selected_pagination_page).to_have_text("1")
        first_page_images = sumo_pages.media_gallery.get_displayed_media_files_links()

    # The gallery is ordered newest-first and other media gallery tests upload/delete images in
    # parallel, so a page's exact contents can shift between reads. We therefore assert that each
    # page introduces images that were not on the page we just navigated away from. This holds
    # regardless of concurrent uploads/deletions (a page's fresh items can never have appeared on
    # the previous page) and avoids the flakiness of exact set comparisons.
    with check, allure.step("Clicking on the 'Next' pagination button and verifying that a new "
                            "set of images is displayed on the second page"):
        sumo_pages.media_gallery.click_on_the_next_pagination_page()
        expect(sumo_pages.media_gallery.selected_pagination_page).to_have_text("2")
        second_page_images = sumo_pages.media_gallery.get_displayed_media_files_links()
        assert set(second_page_images) - set(first_page_images), (
            "The second pagination page is not displaying a new set of images")

    with check, allure.step("Clicking on the 'Previous' pagination button and verifying that we "
                            "are navigated back to the first page with a new set of images"):
        sumo_pages.media_gallery.click_on_the_previous_pagination_page()
        expect(sumo_pages.media_gallery.selected_pagination_page).to_have_text("1")
        first_page_images_revisited = sumo_pages.media_gallery.get_displayed_media_files_links()
        assert set(first_page_images_revisited) - set(second_page_images), (
            "The first pagination page is not displaying a new set of images")

    with check, allure.step("Clicking on the second pagination page number and verifying that a "
                            "new set of images is displayed"):
        sumo_pages.media_gallery.click_on_a_pagination_page(2)
        expect(sumo_pages.media_gallery.selected_pagination_page).to_have_text("2")
        second_page_images_revisited = sumo_pages.media_gallery.get_displayed_media_files_links()
        assert set(second_page_images_revisited) - set(first_page_images_revisited), (
            "The second pagination page is not displaying a new set of images")

    with allure.step("Uploading a new media file to the gallery"):
        sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(
            title=media_title, description=media_description)

    with check, allure.step("Navigating back to the media gallery and verifying that the newly "
                            "uploaded image is displayed inside the first pagination page"):
        sumo_pages.top_navbar.click_on_media_gallery_option()
        expect(sumo_pages.media_gallery.selected_pagination_page).to_have_text("1")
        expect(sumo_pages.media_gallery.media_file(media_title)).to_be_visible()


@pytest.mark.mediaGalleryTests
@pytest.mark.parametrize("user", ["forum_contributor", "non_contributor", None])
def test_contributor_tools_side_navbar(page: Page, create_user_factory, user):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    common_web_elements = sumo_pages.common_web_elements
    media_gallery_url = utilities.different_endpoints["media_gallery"]
    # All 'Contributor tools' side navbar options available to a signed-in non-moderator. The
    # last three are revealed by the 'Show More' toggle. ('Moderate forum content' is excluded
    # since it requires moderation permissions.)
    contributor_tools = ["Knowledge base dashboards", "Guides", "Templates", "Media gallery",
                         "Recent revisions", "Community hub", "Locales", "Locale metrics",
                         "Aggregated metrics"]

    with allure.step("Signing in with the parametrized user account (if any) and navigating to "
                     "the media gallery"):
        if user == "forum_contributor":
            utilities.start_existing_session(
                cookies=create_user_factory(groups=["forum-contributors"]))
        elif user == "non_contributor":
            utilities.start_existing_session(cookies=create_user_factory())
        utilities.navigate_to_link(media_gallery_url)

    if user is None:
        with allure.step("Verifying that the 'Contributor tools' side navbar is not displayed "
                         "for signed-out users"):
            expect(common_web_elements.contributor_tools_side_navbar).to_be_hidden()
        return

    with allure.step("Verifying that the 'Contributor tools' side navbar is displayed"):
        expect(common_web_elements.contributor_tools_side_navbar).to_be_visible()
        expect(common_web_elements.contributor_tools_side_navbar_heading).to_have_text(
            "Contributor tools")

    with check, allure.step("Verifying that the 'Media gallery' option is highlighted by default "
                            "when landing on the media gallery page"):
        expect(common_web_elements.contributor_tools_side_navbar_selected_option).to_have_text(
            "Media gallery")

    with allure.step("Expanding the collapsible 'Show More' section of the side navbar"):
        common_web_elements.click_on_contributor_tools_side_navbar_show_more_button()

    with check, allure.step("Verifying that all the 'Contributor tools' options are displayed"):
        for option in contributor_tools:
            expect(common_web_elements.contributor_tools_side_navbar_option(option)
                   ).to_be_visible()

    # The side navbar options are identical for every signed-in user, so we only verify the
    # redirects once, using the forum contributor account.
    if user == "forum_contributor":
        for option in contributor_tools:
            with check, allure.step(f"Clicking on the '{option}' option and verifying that it "
                                    f"successfully navigates to its page (status < 400)"):
                utilities.navigate_to_link(media_gallery_url)
                common_web_elements.click_on_contributor_tools_side_navbar_show_more_button()
                # click_and_wait_for_navigation reloads the destination on a 502 and returns the
                # final response, so transient gateway errors are retried instead of failing.
                response = utilities.click_and_wait_for_navigation(
                    lambda: common_web_elements
                    .click_on_a_contributor_tools_side_navbar_option(option))
                assert response is not None and response.status < 400, (
                    f"The '{option}' option returned a status of "
                    f"{response.status if response else 'no response'}")


