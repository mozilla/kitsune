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


# The server-side limit (settings.IMAGE_MAX_FILESIZE) and the client-side check in gallery.js.
IMAGE_MAX_FILESIZE = 10485760  # 10MB, in bytes
IMAGE_TOO_LARGE_MESSAGE = "Image too large. Please select a smaller image file."


# C1811690
@pytest.mark.mediaGalleryTests
def test_image_under_size_limit_can_be_uploaded(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    media_title = utilities.generate_unique_title()
    media_description = f"Automation test description{utilities.generate_random_number(1, 1000)}"

    with allure.step("Signing in with a contributor account and navigating to the media gallery"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_media_gallery_option()

    with allure.step("Generating a small (well under 10MB) in-memory image and uploading it to "
                     "the media gallery"):
        small_image = utilities.generate_in_memory_image()
        assert len(small_image) < IMAGE_MAX_FILESIZE
        sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(
            title=media_title, description=media_description, image_bytes=small_image)

    with check, allure.step("Verifying that the upload succeeded and landed on the image preview "
                            "page for the newly uploaded image"):
        expect(sumo_pages.media_gallery.image_heading).to_have_text(media_title)

    with check, allure.step("Searching for the uploaded image in the gallery and verifying that "
                            "it is listed"):
        sumo_pages.top_navbar.click_on_media_gallery_option()
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(media_title)
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        expect(sumo_pages.media_gallery.media_file(media_title)).to_be_visible()


# C1811691
@pytest.mark.mediaGalleryTests
def test_image_over_size_limit_cannot_be_uploaded(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    media_title = utilities.generate_unique_title()

    with allure.step("Signing in with a contributor account and navigating to the media gallery"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_media_gallery_option()

    with allure.step("Opening the 'Upload a New Media File' panel and selecting an in-memory "
                     "image that exceeds the 10MB limit"):
        oversized_image = utilities.generate_in_memory_image(
            min_size_bytes=IMAGE_MAX_FILESIZE + 1024)
        assert len(oversized_image) > IMAGE_MAX_FILESIZE
        sumo_pages.media_gallery.click_on_upload_a_new_media_file_button()
        utilities.upload_file(
            sumo_pages.media_gallery.upload_modal_browse_button,
            file_buffer=oversized_image,
            file_name=f"{media_title}.png")

    with check, allure.step("Verifying that the 'Image too large' error message is displayed and "
                            "that no image preview is rendered"):
        expect(sumo_pages.media_gallery.upload_modal_file_details).to_contain_text(
            IMAGE_TOO_LARGE_MESSAGE)
        expect(sumo_pages.media_gallery.upload_modal_image_preview).to_be_hidden()


# C2266244
@pytest.mark.mediaGalleryTests
@pytest.mark.parametrize("upload_origin", ["en-US", "de"])
def test_image_is_only_displayed_in_the_locale_it_was_uploaded_in(
        page: Page, create_user_factory, upload_origin):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    media_title = utilities.generate_unique_title()
    media_description = f"Automation test description{utilities.generate_random_number(1, 1000)}"
    en_us_gallery = utilities.different_endpoints["media_gallery"]
    de_gallery = en_us_gallery.replace("/en-US/", "/de/")

    with allure.step("Signing in with a contributor account"):
        utilities.start_existing_session(cookies=test_user)

    if upload_origin == "en-US":
        with allure.step("From the en-US media gallery, uploading an image and assigning it the "
                         "German (de) locale via the upload modal's locale dropdown"):
            utilities.navigate_to_link(en_us_gallery)
            sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(
                title=media_title, description=media_description, locale="de")
    else:
        with allure.step("Uploading an image directly from the German (de) media gallery, which "
                         "defaults the image locale to German"):
            utilities.navigate_to_link(de_gallery)
            sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(
                title=media_title, description=media_description)

    with check, allure.step("Searching the German media gallery and verifying that the image is "
                            "displayed there"):
        utilities.navigate_to_link(de_gallery)
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(media_title)
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        expect(sumo_pages.media_gallery.media_file(media_title)).to_be_visible()

    with check, allure.step("Searching the en-US media gallery and verifying that the image is "
                            "not displayed there"):
        utilities.navigate_to_link(en_us_gallery)
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(media_title)
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        expect(sumo_pages.media_gallery.media_file(media_title)).to_be_hidden()


# C2266244
@pytest.mark.mediaGalleryTests
def test_en_us_image_is_not_displayed_in_a_non_en_us_locale_gallery(page: Page,
                                                                    create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    media_title = utilities.generate_unique_title()
    media_description = f"Automation test description{utilities.generate_random_number(1, 1000)}"
    en_us_gallery = utilities.different_endpoints["media_gallery"]
    de_gallery = en_us_gallery.replace("/en-US/", "/de/")

    with allure.step("Signing in with a contributor account and uploading an image from the "
                     "en-US media gallery (the image defaults to the en-US locale)"):
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(en_us_gallery)
        sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(
            title=media_title, description=media_description)

    with check, allure.step("Searching the en-US media gallery and verifying that the image is "
                            "displayed there"):
        utilities.navigate_to_link(en_us_gallery)
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(media_title)
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        expect(sumo_pages.media_gallery.media_file(media_title)).to_be_visible()

    with check, allure.step("Searching the German (non en-US) media gallery and verifying that "
                            "the image is not displayed there"):
        utilities.navigate_to_link(de_gallery)
        sumo_pages.media_gallery.fill_search_media_gallery_searchbox_input_field(media_title)
        sumo_pages.media_gallery.click_on_media_gallery_searchbox_search_button()
        expect(sumo_pages.media_gallery.media_file(media_title)).to_be_hidden()


# C2663905
@pytest.mark.mediaGalleryTests
@pytest.mark.parametrize("user", ["forum_contributor", "non_contributor", None])
def test_contributor_tools_side_navbar(page: Page, create_user_factory, user):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    common_web_elements = sumo_pages.common_web_elements
    media_gallery_url = utilities.different_endpoints["media_gallery"]
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

    if user == "forum_contributor":
        for option in contributor_tools:
            with check, allure.step(f"Clicking on the '{option}' option and verifying that it "
                                    f"successfully navigates to its page (status < 400)"):
                utilities.navigate_to_link(media_gallery_url)
                common_web_elements.click_on_contributor_tools_side_navbar_show_more_button()
                response = utilities.click_and_wait_for_navigation(
                    lambda: common_web_elements
                    .click_on_a_contributor_tools_side_navbar_option(option))
                assert response is not None and response.status < 400, (
                    f"The '{option}' option returned a status of "
                    f"{response.status if response else 'no response'}")


