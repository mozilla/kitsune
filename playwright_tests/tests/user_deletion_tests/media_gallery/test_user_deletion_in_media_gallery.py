import allure
import pytest
from playwright.sync_api import Page
from pytest_check import check

from playwright_tests.core.utilities import Utilities
from playwright_tests.pages.sumo_pages import SumoPages


# C2939491
@pytest.mark.userDeletion
def test_media_file_ownership_reassignment_to_system_account(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "forum-contributors"])
    media_title = "Automation test image " + utilities.generate_random_number(1, 1000)
    media_description = "Automation test description" + utilities.generate_random_number(1, 1000)
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with a Knowledge Base Reviewer test account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to the media gallery and uploading a new test image"):
        sumo_pages.top_navbar.click_on_media_gallery_option()
        sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(title= media_title,
                                                                   description=media_description)
        image_preview_url = utilities.get_page_url()

    with check, allure.step("Verifying that the test user is added as the image creator"):
        assert sumo_pages.media_gallery.get_image_creator_text() == test_user["username"]

    with allure.step("Deleting the test user account"):
        sumo_pages.top_navbar.click_on_edit_profile_option()
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Navigating back to the image preview and verifying that the system "
                            "account has taken ownership of the image"):
        utilities.navigate_to_link(image_preview_url)
        assert (sumo_pages.media_gallery.get_image_creator_text() == utilities.
                general_test_data["system_account_name"])

    with allure.step("Deleting the uploaded test image"):
        utilities.start_existing_session(session_file_name=staff)
        sumo_pages.add_kb_media_flow.delete_media_file()


# C2961300
@pytest.mark.userDeletion
def test_media_file_is_displayed_in_kb_after_owner_deletion(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers", "forum-contributors"])
    test_user_two = create_user_factory(groups=["Knowledge Base Reviewers", "forum-contributors"])
    media_title = "Automation test image " + utilities.generate_random_number(1, 1000)
    media_description = "Automation test description" + utilities.generate_random_number(1, 1000)
    staff = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Signing in with a test account and uploading a new image to the media "
                     "gallery"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_media_gallery_option()
        sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(title=media_title,
                                                                   description=media_description)
        image_preview_url = utilities.get_page_url()

    with allure.step("Signing in with the staff user and creating a new kb article by including "
                     "the newly added image inside the kb content"):
        utilities.start_existing_session(cookies=test_user_two)
        article_info = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            media_file_type="Images", media_file_name=media_title, approve_first_revision=True,
            article_content_image=True
        )

    with allure.step("Signing in with the test user and deleting the account"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.edit_profile_flow.close_account()

    with check, allure.step("Signing in and verifying that the image is still displayed at kb"
                            " article level"):
        utilities.navigate_to_link(utilities.remove_character_from_string(
            article_info["article_url"], "/history"))
        assert sumo_pages.kb_article_page.is_article_content_image_displayed(media_title)

    with check, allure.step("Navigating to the image and preview and verifying that: "
                            "1. The article is added inside the Articles list. "
                            "2. The image ownership is assigned to the system account"):
        utilities.navigate_to_link(image_preview_url)
        assert (article_info["article_title"] in sumo_pages.media_gallery
                .get_image_in_documents_list_items_text())
        assert (sumo_pages.media_gallery.get_image_creator_text() == utilities.
                general_test_data["system_account_name"])

    with allure.step("Deleting the attached image"):
        utilities.start_existing_session(session_file_name=staff)
        sumo_pages.add_kb_media_flow.delete_media_file()


# C2961299
@pytest.mark.userDeletion
def test_media_gallery_image_is_preserved_after_editor_deletion(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors", "Moderators"])
    media_title = "Automation test image " + utilities.generate_random_number(1, 1000)
    media_description = "Automation test description" + utilities.generate_random_number(1, 1000)
    new_media_description = "Test 123"

    with allure.step("Signing in with a test account and uploading a new image to the media "
                     "gallery"):
        utilities.start_existing_session(cookies=test_user)
        sumo_pages.top_navbar.click_on_media_gallery_option()
        sumo_pages.add_kb_media_flow.add_new_media_file_to_gallery(title=media_title,
                                                                   description=media_description)
        image_preview_url = utilities.get_page_url()

    with allure.step("Signing in with the second test account and editing the image description"):
        utilities.start_existing_session(cookies=test_user_two)
        sumo_pages.media_gallery.click_on_edit_this_image_button()
        sumo_pages.media_gallery.fill_into_image_description_edit_textarea(new_media_description)
        sumo_pages.media_gallery.click_on_image_description_edit_save_button()

    with allure.step("Deleting the second user account"):
        sumo_pages.edit_profile_flow.close_account()

    with allure.step("Navigating back to the image and verifying that: "
                     "1. The image ownership is kept to the first user."
                     "2. The image description is kept to the edited version"):
        utilities.navigate_to_link(image_preview_url)
        assert sumo_pages.media_gallery.get_image_creator_text() == test_user["username"]
        assert sumo_pages.media_gallery.get_image_description() == new_media_description



