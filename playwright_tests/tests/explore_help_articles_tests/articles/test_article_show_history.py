import allure
from pytest_check import check
import pytest
from playwright_tests.core.utilities import Utilities
from playwright.sync_api import expect, Page

from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import \
    QuestionPageMessages
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.explore_help_articles.kb_article_page_messages import (
    KBArticlePageMessages)
from playwright_tests.messages.explore_help_articles.kb_article_revision_page_messages import (
    KBArticleRevision)
from playwright_tests.messages.explore_help_articles.kb_article_show_history_page_messages import \
    KBArticleShowHistoryPageMessages
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages)
from playwright_tests.pages.explore_help_articles.articles.kb_article_show_history_page import \
    KBArticleShowHistoryPage
from playwright_tests.pages.sumo_pages import SumoPages


# C891309, C2102170,  C2102168, C2489545, C910271
@pytest.mark.smokeTest
@pytest.mark.kbArticleShowHistory
def test_kb_article_removal(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_show_history_page_messages = KBArticleShowHistoryPageMessages()

    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
    ))

    article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page)
    revision_id_number = utilities.number_extraction_from_string(
        article_details['first_revision_id']
    )

    with allure.step("Verifying that the delete button is not available for the only kb "
                     "revision"):
        expect(
            sumo_pages.kb_article_show_history_page.get_delete_revision_button_locator(
                article_details['first_revision_id']
            )
        ).to_be_hidden()

    with check, allure.step("Verifying that manually navigating to the delete revision "
                            "endpoint returns 403"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(
                kb_show_history_page_messages.get_delete_revision_endpoint(
                    article_details["article_slug"], revision_id_number
                ))
            response = navigation_info.value
            assert response.status == 403

    with allure.step("Navigating back and verifying that the delete button for the article "
                     "is not displayed"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        expect(sumo_pages.kb_article_show_history_page.get_delete_this_document_button_locator(
        )).to_be_hidden()

    with check, allure.step("Verifying that manually navigating to the delete endpoint "
                            "returns 403"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(
                KBArticlePageMessages
                .KB_ARTICLE_PAGE_URL + article_details['article_slug'] + QuestionPageMessages
                .DELETE_QUESTION_URL_ENDPOINT
            )
            response = navigation_info.value
            assert response.status == 403

    with allure.step("Navigating back and deleting the user session"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        utilities.delete_cookies()

    with check, allure.step("Manually navigating to the delete revision endpoint and "
                            "verifying that the auth page is returned"):
        utilities.navigate_to_link(kb_show_history_page_messages.get_delete_revision_endpoint(
            article_details["article_slug"], revision_id_number
        ))
        assert FxAPageMessages.AUTH_PAGE_URL in utilities.get_page_url()

    with check, allure.step("Navigating back and verifying that manually navigating to the "
                            "delete endpoint returns the auth page"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        utilities.navigate_to_link(
            KBArticlePageMessages
            .KB_ARTICLE_PAGE_URL + article_details['article_slug'] + QuestionPageMessages
            .DELETE_QUESTION_URL_ENDPOINT
        )
        assert FxAPageMessages.AUTH_PAGE_URL in utilities.get_page_url()

    with allure.step("Navigating back and verifying that the delete button is not available "
                     "for the only revision"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        expect(sumo_pages.kb_article_show_history_page.get_delete_revision_button_locator(
            article_details['first_revision_id'])).to_be_hidden()

    with allure.step("Verifying that the delete button for the article is not displayed"):
        expect(sumo_pages.kb_article_show_history_page.get_delete_this_document_button_locator(
        )).to_be_hidden()

    with allure.step("Signing in with an admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with check, allure.step("Clicking on the delete revision button for the only available "
                            "revision and verifying that the correct 'Unable to delete the "
                            "revision' page header"):
        sumo_pages.kb_article_show_history_page.click_on_delete_revision_button(
            article_details['first_revision_id']
        )
        assert (sumo_pages.kb_article_show_history_page.get_unable_to_delete_revision_header(
        ) == KBArticleRevision.KB_REVISION_CANNOT_DELETE_ONLY_REVISION_HEADER)

    with check, allure.step("Verifying that the correct 'Unable to delete the revision' page "
                            "sub-header is displayed"):
        assert (sumo_pages.kb_article_show_history_page.get_unable_to_delete_revision_subheader(
        ) == KBArticleRevision.KB_REVISION_CANNOT_DELETE_ONLY_REVISION_SUBHEADER)

    with allure.step("Clicking on the 'Go back to document history button' and verifying "
                     "that we are redirected to the document history page"):
        sumo_pages.kb_article_show_history_page.click_go_back_to_document_history_option()
        expect(page).to_have_url(
            KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
            ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT
        )

    with allure.step("Clicking on the 'Delete article' button, canceling the confirmation "
                     "modal and verifying that we are back on the show history page for the "
                     "article"):
        sumo_pages.kb_article_show_history_page.click_on_delete_this_document_button()
        sumo_pages.kb_article_show_history_page.click_on_confirmation_cancel_button()
        expect(page).to_have_url(
            KBArticlePageMessages.KB_ARTICLE_PAGE_URL + article_details
            ['article_slug'] + KBArticlePageMessages.KB_ARTICLE_HISTORY_URL_ENDPOINT
        )

    with allure.step("Creating a new revision for the article"):
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True)

    with check, allure.step("Deleting the revision and verifying that the revision is not "
                            "displayed"):
        sumo_pages.kb_article_show_history_page.click_on_delete_revision_button(
            article_details['first_revision_id']
        )
        sumo_pages.kb_article_show_history_page.click_on_confirmation_delete_button()
        expect(sumo_pages.kb_article_show_history_page.get_a_particular_revision_locator(
            article_details['first_revision_id'])).to_be_hidden()

        expect(sumo_pages.kb_article_show_history_page.get_a_particular_revision_locator(
            second_revision['revision_id'])).to_be_visible()

    with check, allure.step("Deleting the article, navigating to the article and verifying "
                            "that the article was successfully deleted"):
        sumo_pages.kb_article_deletion_flow.delete_kb_article()
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(
                KBArticlePageMessages.
                KB_ARTICLE_PAGE_URL + article_details['article_slug'] + "/"
            )
        response = navigation_info.value
        assert response.status == 404


# C2490047, C2490048
@pytest.mark.kbArticleShowHistory
def test_kb_article_category_link_and_header(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
    for category in utilities.general_test_data["kb_article_categories"]:
        if category != "Templates":
            with allure.step("Creating a new article"):
                article_info = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                    article_category=category
                )
        else:
            with allure.step("Creating a new template article"):
                article_info = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
                    article_category=category, is_template=True
                )

        with check, allure.step("Verifying that the correct page header is displayed"):
            assert sumo_pages.kb_article_show_history_page.get_show_history_page_title(
            ) == KBArticleShowHistoryPageMessages.PAGE_TITLE + article_info["article_title"]

        with check, allure.step("Verifying that the correct category is displayed inside the "
                                "'Show History' page"):
            assert sumo_pages.kb_article_show_history_page.get_show_history_category_text(
            ) == category

        with check, allure.step("Verifying that the correct revision history for locale is "
                                "displayed"):
            assert (
                sumo_pages.kb_article_show_history_page.get_show_history_revision_for_locale_text(
                ) == KBArticleShowHistoryPageMessages.DEFAULT_REVISION_FOR_LOCALE)

        with allure.step("Clicking on the 'Category' link and verifying that the user is "
                         "redirected to the correct page"):
            sumo_pages.kb_article_show_history_page.click_on_show_history_category()
            expect(
                page
            ).to_have_url(utilities.different_endpoints['kb_categories_links'][category])

        with allure.step("Navigating back and deleting the article"):
            utilities.navigate_back()
            sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2101637, C2489543, C2102169, C2489542
@pytest.mark.kbArticleShowHistory
def test_kb_article_contributor_removal(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_show_history_page_messages = KBArticleShowHistoryPageMessages()

    username_one = utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page)
    with allure.step("Verifying that no users are added inside the contributors list"):
        expect(sumo_pages.kb_article_show_history_page.get_all_contributors_locator()
               ).to_be_hidden()

    with check, allure.step("Clicking on the Article menu option and verifying that the user "
                            "is not displayed inside the article contributors section"):
        sumo_pages.kb_article_page.click_on_article_option()
        assert username_one not in sumo_pages.kb_article_page.get_list_of_kb_article_contributors(
        )

    with allure.step("Navigating back to the 'Show History page and approving the revision"):
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=article_details['first_revision_id'])

    with check, allure.step("Verifying that the username which created the revision is added "
                            "inside the 'Contributors' list"):
        assert username_one in (sumo_pages.kb_article_show_history_page
                                .get_list_of_all_contributors())

    sumo_pages.kb_article_show_history_page.click_on_edit_contributors_option()
    sumo_pages.kb_article_show_history_page.click_on_delete_button_for_a_particular_contributor(
        username_one)
    deletion_link = utilities.get_page_url()

    with check, allure.step("Navigating back by hitting the cancel button. clicking on the "
                            "Article menu option and verifying that the user is displayed "
                            "inside the article contributors section"):
        (sumo_pages.kb_article_show_history_page
         .click_on_delete_contributor_confirmation_page_cancel_button())
        sumo_pages.kb_article_page.click_on_article_option()
        assert username_one in sumo_pages.kb_article_page.get_list_of_kb_article_contributors()

    with allure.step("Navigating back to the 'Show History page' and signing in with a "
                     "non-admin account"):
        sumo_pages.kb_article_page.click_on_show_history_option()
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

    username_two = sumo_pages.top_navbar.get_text_of_logged_in_username()

    with allure.step("Creating a new revision for the document and verifying that the 'Edit "
                     "Contributors' option is not displayed for users which don't have the "
                     "necessary permissions"):
        second_revision_info = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()
        expect(sumo_pages.kb_article_show_history_page.get_edit_contributors_option_locator()
               ).to_be_hidden()

    with check, allure.step("Manually navigating to the deletion link and verifying that 403 "
                            "is returned"):
        with page.expect_navigation() as navigation_info:
            utilities.navigate_to_link(deletion_link)
        response = navigation_info.value
        assert response.status == 403

    with check, allure.step("Navigating back, clicking on the Article menu and verifying "
                            "that the user is not displayed inside the article contributors "
                            "section"):
        utilities.navigate_to_link(article_details['article_url'])
        sumo_pages.kb_article_page.click_on_article_option()
        assert (username_two not in sumo_pages.kb_article_page
                .get_list_of_kb_article_contributors())

    with allure.step("Navigating back to the 'Show History page', deleting the user session "
                     "and verifying that the 'Edit Contributors' options is not displayed"):
        sumo_pages.kb_article_page.click_on_show_history_option()
        utilities.delete_cookies()
        expect(sumo_pages.kb_article_show_history_page.get_edit_contributors_option_locator()
               ).to_be_hidden()

    with check, allure.step("Manually navigating to the deletion link and the user is "
                            "redirected to the auth page"):
        utilities.navigate_to_link(deletion_link)
        assert FxAPageMessages.AUTH_PAGE_URL in utilities.get_page_url()

    with check, allure.step("Navigating back, signing in with a non-admin account and "
                            "verifying that the username two is not displayed inside the "
                            "Contributors list"):
        utilities.navigate_to_link(article_details['article_url'])
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        assert (username_two not in sumo_pages.kb_article_show_history_page
                .get_list_of_all_contributors())

    with check, allure.step("Approving the revision and verifying that the second username "
                            "is displayed inside the Contributors list"):
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=second_revision_info['revision_id'])
        assert (username_two in sumo_pages.kb_article_show_history_page
                .get_list_of_all_contributors())

    with check, allure.step("Clicking on the Article menu and verifying that the user is "
                            "displayed inside the article contributors section"):
        sumo_pages.kb_article_page.click_on_article_option()
        assert username_one in sumo_pages.kb_article_page.get_list_of_kb_article_contributors()

    with allure.step("Clicking on the delete button for user two"):
        sumo_pages.kb_article_page.click_on_show_history_option()
        sumo_pages.kb_article_show_history_page.click_on_edit_contributors_option()
        (sumo_pages.kb_article_show_history_page
         .click_on_delete_button_for_a_particular_contributor(username_two))

    with check, allure.step("Verifying that the correct delete contributor page header is "
                            "displayed"):
        assert (sumo_pages.kb_article_show_history_page
                .get_delete_contributor_confirmation_page_header(
                ) == kb_show_history_page_messages.get_remove_contributor_page_header(
                    username_two))

    with check, allure.step("Clicking on the 'Cancel' button and verifying that the second "
                            "username is displayed inside the Contributors list"):
        (sumo_pages.kb_article_show_history_page
         .click_on_delete_contributor_confirmation_page_cancel_button())
        assert (username_two in sumo_pages.kb_article_show_history_page
                .get_list_of_all_contributors())

    with check, allure.step("Clicking on the Article menu option and verifying that the user "
                            "is displayed inside the article contributors section"):
        sumo_pages.kb_article_page.click_on_article_option()
        assert username_one in sumo_pages.kb_article_page.get_list_of_kb_article_contributors()

    with allure.step("Navigating back to the 'Show History' page and deleting the the second "
                     "contributor"):
        sumo_pages.kb_article_page.click_on_show_history_option()
        sumo_pages.kb_article_show_history_page.click_on_edit_contributors_option()
        (sumo_pages.kb_article_show_history_page
         .click_on_delete_button_for_a_particular_contributor(username_two))
        (sumo_pages.kb_article_show_history_page.
         click_on_delete_contributor_confirmation_page_confirm_button())

    with check, allure.step("Verifying that the correct banner is displayed"):
        assert sumo_pages.kb_article_show_history_page.get_show_history_page_banner(
        ) == kb_show_history_page_messages.get_contributor_removed_message(username_two)

    with check, allure.step("Verifying that second username is not displayed inside the "
                            "'Contributors' list"):
        assert (username_two not in sumo_pages.kb_article_show_history_page
                .get_list_of_all_contributors())

    with check, allure.step("Clicking on the Article menu and verifying that the user is not "
                            "displayed inside the contributors section"):
        sumo_pages.kb_article_page.click_on_article_option()
        assert (username_two not in sumo_pages.kb_article_page
                .get_list_of_kb_article_contributors())

    with allure.step("Signing in with the removed username and creating a new revision"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))
        third_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Approving the revision and verifying that the user is added again "
                     "inside the contributors list"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=third_revision['revision_id'])

    with check, allure.step("Verifying that second username is not inside the 'Contributors' "
                            "list"):
        assert (username_two in sumo_pages.kb_article_show_history_page
                .get_list_of_all_contributors())

    with check, allure.step("Clicking on the Article menu and verifying that the user is not "
                            "displayed inside the contributors section"):
        sumo_pages.kb_article_page.click_on_article_option()
        assert username_two in sumo_pages.kb_article_page.get_list_of_kb_article_contributors()

    with allure.step("Deleting the artice"):
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2101638
@pytest.mark.kbArticleShowHistory
def test_contributors_can_be_manually_added(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_show_history_page_messages = KBArticleShowHistoryPageMessages()
    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))
    with allure.step("Clicking on the 'Edit Contributors' option, adding and selecting the "
                     "username from the search field"):
        sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(page=page)
        sumo_pages.kb_article_show_history_page.click_on_edit_contributors_option()
        new_contributor = utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        )
        (sumo_pages.kb_article_show_history_page
         .add_a_new_contributor_inside_the_contributor_field(new_contributor))
        (sumo_pages.kb_article_show_history_page.click_on_new_contributor_search_result(
            new_contributor))

    with check, allure.step("Clicking on the 'Add Contributor' option and verifying that the "
                            "correct banner is displayed"):
        sumo_pages.kb_article_show_history_page.click_on_add_contributor_button()
        assert sumo_pages.kb_article_show_history_page.get_show_history_page_banner(
        ) == kb_show_history_page_messages.get_contributor_added_message(new_contributor)

    with check, allure.step("Verifying that the user was successfully added inside the "
                            "contributors list"):
        assert (new_contributor in sumo_pages.kb_article_show_history_page
                .get_list_of_all_contributors())

    with check, allure.step("Clicking on the Article menu option and verifying that the user "
                            "is displayed inside the article contributors section"):
        sumo_pages.kb_article_page.click_on_article_option()
        assert new_contributor in sumo_pages.kb_article_page.get_list_of_kb_article_contributors()

    with allure.step("Deleting the article"):
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2101634, C2489553, C2102186
@pytest.mark.kbArticleShowHistory
def test_kb_article_contributor_profile_access(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_article_show_history_page = KBArticleShowHistoryPage(page)
    utilities.start_existing_session(utilities.username_extraction_from_email(
        utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
    ))

    sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
        page=page, approve_revision=True)
    sumo_pages.kb_article_page.click_on_article_option()
    article_url = utilities.get_page_url()

    with allure.step("Signing in with a non-Admin account and creating a new revision"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_12"]
        ))

        username_two = sumo_pages.top_navbar.get_text_of_logged_in_username()

        second_revision_info = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Approving the revision and deleting the user session"):
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=second_revision_info['revision_id'])
        utilities.delete_cookies()

    with allure.step("Clicking on the second contributor and verifying that we are "
                     "redirected to it's profile page"):
        kb_article_show_history_page.click_on_a_particular_contributor(username_two)
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

    with allure.step("Navigating back, clicking on the revision editor and verifying that we "
                     "are redirected to the editor homepage"):
        utilities.navigate_back()
        kb_article_show_history_page.click_on_a_particular_revision_editor(
            second_revision_info['revision_id'], username_two
        )
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

    with allure.step("Navigating back to the article main menu"):
        utilities.navigate_to_link(article_url)

    with allure.step("Clicking on the contributor listed inside the article page and "
                     "verifying that we are redirected to the editor homepage"):
        sumo_pages.kb_article_page.click_on_a_particular_article_contributor(username_two)
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

    with allure.step("Navigating back and signin in with an admin account"):
        utilities.navigate_back()
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Clicking on the Article menu option, clicking on the contributor "
                     "listed inside the article page and verifying that we are redirected to "
                     "the editor homepage"):
        sumo_pages.kb_article_page.click_on_article_option()
        sumo_pages.kb_article_page.click_on_a_particular_article_contributor(username_two)
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

    with allure.step("Navigating back to the article history, clicking on the second "
                     "contributor and verifying that we are redirected to it's profile page"):
        utilities.navigate_back()
        sumo_pages.kb_article_page.click_on_show_history_option()
        kb_article_show_history_page.click_on_a_particular_contributor(username_two)
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

    with allure.step("Navigating back and clicking on the revision editor"):
        utilities.navigate_back()
        kb_article_show_history_page.click_on_a_particular_revision_editor(
            second_revision_info['revision_id'], username_two
        )

    with allure.step("Verifying that we are redirected to the editor homepage"):
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(username_two))

    with allure.step("Navigating back and deleting the created article"):
        utilities.navigate_back()
        sumo_pages.kb_article_deletion_flow.delete_kb_article()


# C2499415, C2271120, C2101633
@pytest.mark.kbArticleShowHistory
def test_kb_article_revision_date_functionality(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account and creating a new article and "
                     "approving it's first revision"):
        main_user = utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))
        article_details = sumo_pages.submit_kb_article_flow.kb_article_creation_via_api(
            page=page, approve_revision=True)

    with allure.step("Signing in with a non-admin account"):
        creator_username = utilities.start_existing_session(
            utilities.username_extraction_from_email(
                utilities.user_secrets_accounts['TEST_ACCOUNT_12']))

    with allure.step("Submitting a new revision"):
        second_revision_info = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with allure.step("Deleting the user session and clicking on the first revision"):
        utilities.delete_cookies()
        revision_time = sumo_pages.kb_article_show_history_page.get_revision_time(
            second_revision_info['revision_id']
        )
        sumo_pages.kb_article_show_history_page.click_on_a_revision_date(
            article_details['first_revision_id']
        )

    with check, allure.step("Verifying that the correct 'Is current revision?' text is "
                            "displayed"):
        assert sumo_pages.kb_article_preview_revision_page.get_is_current_revision_text(
        ) == KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS

    with allure.step("Navigating back and clicking on the revision time"):
        utilities.navigate_back()
        sumo_pages.kb_article_show_history_page.click_on_a_revision_date(
            second_revision_info['revision_id'])

    with allure.step("Verifying that the revision information content is expanded by default"):
        expect(
            sumo_pages.kb_article_preview_revision_page.get_revision_information_content_locator(
            )).to_be_visible()

    with allure.step("Clicking on the 'Revision Information' foldout section and Verifying "
                     "that the revision information content is collapsed/no longer displayed"):
        (sumo_pages.kb_article_preview_revision_page
         .click_on_revision_information_foldout_section())
        expect(
            sumo_pages.kb_article_preview_revision_page.get_revision_information_content_locator(
            )).to_be_hidden()

    with allure.step("Clicking on the 'Revision Information' foldout section"):
        (sumo_pages.kb_article_preview_revision_page
         .click_on_revision_information_foldout_section())

    with allure.step("Verifying that the revision information content is displayed"):
        expect(
            sumo_pages.kb_article_preview_revision_page.get_revision_information_content_locator(
            )).to_be_visible()

    with check, allure.step("Verifying that the revision id is the correct one"):
        assert sumo_pages.kb_article_preview_revision_page.get_preview_revision_id_text(
        ) == str(utilities.number_extraction_from_string(second_revision_info['revision_id']))

    with check, allure.step("Verifying that the correct revision time is displayed"):
        assert (
            sumo_pages.kb_article_preview_revision_page.get_preview_revision_created_date_text(
            ) == revision_time)

    with check, allure.step("Verifying that the correct creator is displayed"):
        assert (sumo_pages.kb_article_preview_revision_page.get_preview_revision_creator_text(
        ) == creator_username)

    with allure.step("Clicking on the creator link and verifying that we are redirected to "
                     "the username page"):
        sumo_pages.kb_article_preview_revision_page.click_on_creator_link()
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(creator_username))

    with check, allure.step("Navigating back to the revision preview page and verifying that "
                            "the correct review comment is displayed"):
        utilities.navigate_back()
        assert (sumo_pages.kb_article_preview_revision_page.get_preview_revision_comment_text(
        ) == utilities.kb_article_test_data['changes_description'])

    with check, allure.step("Verifying that the correct reviewed status is displayed"):
        assert (sumo_pages.kb_article_preview_revision_page.get_preview_revision_reviewed_text(
        ) == KBArticleRevision.KB_ARTICLE_REVISION_NO_STATUS)

    with allure.step("Verifying that the reviewed by locator is hidden"):
        expect(
            sumo_pages.kb_article_preview_revision_page.get_reviewed_by_locator()).to_be_hidden()

    with allure.step("Verifying that the is approved locator is hidden"):
        expect(
            sumo_pages.kb_article_preview_revision_page.get_is_approved_text_locator()
        ).to_be_hidden()

    with allure.step("Verifying that the is current revision locator is hidden"):
        expect(
            sumo_pages.kb_article_preview_revision_page.is_current_revision_locator()
        ).to_be_hidden()

    with check, allure.step("Verifying that the correct ready for localization locator is "
                            "displayed"):
        assert (sumo_pages.kb_article_preview_revision_page
                .get_preview_revision_ready_for_localization_text(
                ) == KBArticleRevision.KB_ARTICLE_REVISION_NO_STATUS)

    with allure.step("Verifying that the readied for localization by is hidden"):
        expect(sumo_pages.kb_article_preview_revision_page.readied_for_localization_by_locator(
        )).to_be_hidden()

    with allure.step("Verifying that the 'Edit article based on this revision' is not "
                     "displayed"):
        expect(
            (sumo_pages.kb_article_preview_revision_page
             .get_edit_article_based_on_this_revision_link_locator())).to_be_hidden()

    with allure.step("Verifying that the 'Revision Source' section is hidden by default"):
        expect((sumo_pages.kb_article_preview_revision_page
                .get_preview_revision_source_textarea_locator())).to_be_hidden()

    with check, allure.step("Clicking on the 'Revision Source' foldout section option and "
                            "verifying that the 'Revision Source' textarea contains the "
                            "correct details"):
        sumo_pages.kb_article_preview_revision_page.click_on_revision_source_foldout_section()
        assert (sumo_pages.kb_article_preview_revision_page
                .get_preview_revision_source_textarea_content(
                ) == utilities.kb_article_test_data['updated_article_content'])

    with allure.step("Verifying that the 'Revision Content' section is hidden by default"):
        expect(sumo_pages.kb_article_preview_revision_page.get_revision_content_html_locator(
        )).to_be_hidden()

    with allure.step("Clicking on the 'Revision Content' foldout option and verifying that "
                     "the 'Revision Content' section is visible"):
        sumo_pages.kb_article_preview_revision_page.click_on_revision_content_foldout_section()
        expect(sumo_pages.kb_article_preview_revision_page.get_revision_content_html_locator(
        )).to_be_visible()

    with allure.step("Signing in with an admin account and approving the revision"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Approving the second revision"):
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=second_revision_info['revision_id'], ready_for_l10n=True)

    with check, allure.step("Deleting the user session, clicking on the revision time and "
                            "verifying that the correct reviewed status is displayed"):
        utilities.delete_cookies()
        sumo_pages.kb_article_show_history_page.click_on_a_revision_date(
            second_revision_info['revision_id']
        )
        assert (sumo_pages.kb_article_preview_revision_page.get_preview_revision_reviewed_text(
        ) == KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS)

    with allure.step("Verifying that the reviewed by date is displayed"):
        expect((sumo_pages.kb_article_preview_revision_page
                .get_preview_revision_reviewed_date_locator())).to_be_visible()

    with check, allure.step("Verifying that the correct 'Reviewed by' text is displayed"):
        assert sumo_pages.kb_article_preview_revision_page.get_reviewed_by_text() == main_user

    with check, allure.step("Verifying that the correct is approved status displayed"):
        assert (sumo_pages.kb_article_preview_revision_page.get_is_approved_text(
        ) == KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS)

    with check, allure.step("Verifying that the correct is current revision status displayed"):
        assert (sumo_pages.kb_article_preview_revision_page.get_is_current_revision_text(
        ) == KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS)

    with check, allure.step("Verifying that the correct is ready for localization status "
                            "displayed"):
        assert (sumo_pages.kb_article_preview_revision_page
                .get_preview_revision_ready_for_localization_text(
                ) == KBArticleRevision.KB_ARTICLE_REVISION_YES_STATUS)

    with allure.step("Verifying that the 'Readied for localization' date is displayed"):
        expect(
            sumo_pages.kb_article_preview_revision_page.ready_for_localization_date()
        ).to_be_visible()

    with check, allure.step("Verifying that the correct localization by text is displayed"):
        assert sumo_pages.kb_article_preview_revision_page.readied_for_localization_by_text(
        ) == main_user

    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Clicking on the 'Edit article based on this revision option' and "
                     "verifying that the correct link is displayed"):
        (sumo_pages.kb_article_preview_revision_page
         .click_on_edit_article_based_on_this_revision_link())
        expect(page).to_have_url(
            article_details['article_url'] + QuestionPageMessages.
            EDIT_QUESTION_URL_ENDPOINT + "/" + str(utilities.number_extraction_from_string(
                second_revision_info['revision_id']))
        )

    with allure.step("Deleting the article"):
        sumo_pages.kb_article_deletion_flow.delete_kb_article()
