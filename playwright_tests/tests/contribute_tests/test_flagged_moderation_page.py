import re
import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.auth_pages_messages.fxa_page_messages import FxAPageMessages
from playwright_tests.messages.common_elements_messages import CommonElementsMessages
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import (
    QuestionPageMessages,
)
from playwright_tests.messages.contribute_messages.con_tools.moderate_forum_messages import (
    ModerateForumContentPageMessages,
)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.messages.my_profile_pages_messages.my_profile_page_messages import (
    MyProfileMessages,
)
from playwright_tests.pages.sumo_pages import SumoPages
from playwright_tests.tests.ask_a_question_tests.aaq_tests.test_posted_questions import (
    post_firefox_product_question_flow,
)


# C890840
@pytest.mark.flaggedModerationPage
@pytest.mark.parametrize("user",[None, "Simple User", "Forum Contributor", "Forum Moderator",
                                 "Admin"])
def test_flagged_moderation_page_access(page: Page, user, create_user_factory):
    utilities = Utilities(page)

    with allure.step("Creating the test user accounts"):
        simple_user = create_user_factory()
        forum_contributor = create_user_factory(
            groups=["forum-contributors", "kb-contributors", "l10n-contributors"])
        forum_moderator = create_user_factory(groups=["Forum Moderators"])

    user_map = {
        "Simple User": simple_user,
        "Forum Contributor": forum_contributor,
        "Forum Moderator": forum_moderator,
    }

    with allure.step(f"Signing in with the {user if user else 'signed-out'} account"):
        if user == "Admin":
            utilities.start_existing_session(
                session_file_name=utilities.username_extraction_from_email(utilities.staff_user)
            )
        elif user is None:
            utilities.delete_cookies()
        else:
            utilities.start_existing_session(cookies=user_map.get(user))

    with allure.step("Navigating to the flagged content moderation page"):
        response = utilities.navigate_to_link(ModerateForumContentPageMessages.PAGE_URL)

    if user in ["Forum Moderator", "Admin"]:
        with check, allure.step(f"Verifying that the {user} can access the moderation page"):
            assert response.status == 200
            expect(page).to_have_url(ModerateForumContentPageMessages.PAGE_URL)
    elif user is None:
        with check, allure.step(
            "Verifying that the signed-out user is redirected to the auth page"
        ):
            expect(page).to_have_url(re.compile(f".*{FxAPageMessages.AUTH_PAGE_URL}*"))
    else:
        with check, allure.step(
            f"Verifying that the {user} receives an Access Denied (403) page"
        ):
            assert response.status == 403

# C890840
@pytest.mark.flaggedModerationPage
@pytest.mark.parametrize("user", [None, "Simple User", "Forum Contributor", "Forum Moderator",
                                  "Admin"])
def test_moderate_forum_content_sidebar_option(page: Page, user, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    with allure.step("Creating the test user accounts"):
        simple_user = create_user_factory()
        forum_contributor = create_user_factory(
            groups=["forum-contributors", "kb-contributors", "l10n-contributors"])
        forum_moderator = create_user_factory(groups=["Forum Moderators"])

    user_map = {
        "Simple User": simple_user,
        "Forum Contributor": forum_contributor,
        "Forum Moderator": forum_moderator,
    }

    with allure.step(f"Signing in with the {user if user else 'signed-out'} account"):
        if user == "Admin":
            utilities.start_existing_session(
                session_file_name=utilities.username_extraction_from_email(utilities.staff_user)
            )
        elif user is None:
            utilities.delete_cookies()
        else:
            utilities.start_existing_session(cookies=user_map.get(user))

    with allure.step("Navigating to the media gallery page which displays the 'Contributor "
                     "tools' sidebar"):
        utilities.navigate_to_link(HomepageMessages.STAGE_HOMEPAGE_URL_EN_US + "gallery")

    moderate_option = sumo_pages.common_web_elements.contributor_tools_side_navbar_option(
        ModerateForumContentPageMessages.SIDEBAR_OPTION_NAME)

    if user in ["Forum Moderator", "Admin"]:
        with check, allure.step(
            f"Verifying that the {user} can see the 'Moderate forum content' sidebar option"
        ):
            expect(moderate_option).to_be_visible()

        with allure.step("Clicking on the 'Moderate forum content' sidebar option"):
            sumo_pages.common_web_elements.click_on_a_contributor_tools_side_navbar_option(
                ModerateForumContentPageMessages.SIDEBAR_OPTION_NAME)

        with check, allure.step(
            f"Verifying that the {user} is redirected to the flagged content moderation page"
        ):
            expect(page).to_have_url(ModerateForumContentPageMessages.PAGE_URL)
    else:
        with check, allure.step(
            f"Verifying that the {user if user else 'signed-out'} user cannot see the "
            "'Moderate forum content' sidebar option"
        ):
            expect(moderate_option).to_be_hidden()


# C945377
@pytest.mark.flaggedModerationPage
def test_deactivated_users_are_listed_in_the_deactivation_log(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Creating two test user accounts to be deactivated"):
        normally_deactivated_user = create_user_factory()
        spam_deactivated_user = create_user_factory()

    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(session_file_name=staff_user)

    with check, allure.step("Deactivating the first user via the 'Deactivate this user' button"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            normally_deactivated_user["username"]))
        sumo_pages.my_profile_page.click_on_deactivate_this_user_button()
        expect(sumo_pages.my_profile_page.this_user_was_deactivated_message).to_have_text(
            MyProfileMessages.USER_DEACTIVATED_MESSAGE)

    with check, allure.step("Deactivating the second user via the 'Deactivate this user and mark "
                            "all content as spam' button"):
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            spam_deactivated_user["username"]))
        sumo_pages.my_profile_page.click_deactivate_this_user_and_mark_all_content_as_spam()
        expect(sumo_pages.my_profile_page.this_user_was_deactivated_message).to_have_text(
            MyProfileMessages.USER_DEACTIVATED_MESSAGE)

    with allure.step("Navigating to the flagged content moderation page and clicking on the "
                     "'View all deactivated users' button"):
        utilities.navigate_to_link(ModerateForumContentPageMessages.PAGE_URL)
        sumo_pages.moderate_forum_content_page.click_view_all_deactivated_users_button()

    with check, allure.step("Verifying that the deactivation log page is displayed"):
        expect(page).to_have_url(ModerateForumContentPageMessages.DEACTIVATED_USERS_PAGE_URL)

    with check, allure.step("Verifying that both the normally deactivated and the "
                            "spam-deactivated users are listed in the deactivation log"):
        expect(sumo_pages.moderate_forum_content_page.deactivation_log_deactivated_user(
            normally_deactivated_user["username"])).to_be_visible()
        expect(sumo_pages.moderate_forum_content_page.deactivation_log_deactivated_user(
            spam_deactivated_user["username"])).to_be_visible()

    with allure.step("Reactivating the first user via the Django admin user page"):
        sumo_pages.admin_users_flows.navigate_to_a_particular_user_profile_in_admin(
            normally_deactivated_user["username"])
        sumo_pages.admin_users_page.active_checkbox.check()
        sumo_pages.admin_users_page.click_on_save_changes_button()

    with check, allure.step("Verifying that the reactivated user is still listed in the "
                            "deactivation log alongside the spam-deactivated user"):
        utilities.navigate_to_link(ModerateForumContentPageMessages.DEACTIVATED_USERS_PAGE_URL)
        expect(sumo_pages.moderate_forum_content_page.deactivation_log_deactivated_user(
            normally_deactivated_user["username"])).to_be_visible()
        expect(sumo_pages.moderate_forum_content_page.deactivation_log_deactivated_user(
            spam_deactivated_user["username"])).to_be_visible()


# C2663906
@pytest.mark.flaggedModerationPage
def test_flagged_page_displays_contributor_tools_sidebar(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    with allure.step("Signing in with a Forum Moderator account"):
        forum_moderator = create_user_factory(groups=["Forum Moderators"])
        utilities.start_existing_session(cookies=forum_moderator)

    with allure.step("Navigating to the flagged content moderation page"):
        utilities.navigate_to_link(ModerateForumContentPageMessages.PAGE_URL)

    with check, allure.step("Verifying that the 'Contributor tools' sidebar is displayed"):
        expect(sumo_pages.common_web_elements.contributor_tools_side_navbar).to_be_visible()
        expect(
            sumo_pages.common_web_elements.contributor_tools_side_navbar_heading
        ).to_have_text(CommonElementsMessages.CONTRIBUTOR_TOOLS_SIDEBAR_HEADING)

    with check, allure.step("Verifying that the 'Moderate forum content' option is the "
                            "highlighted sidebar option"):
        expect(
            sumo_pages.common_web_elements.contributor_tools_side_navbar_selected_option
        ).to_have_text(ModerateForumContentPageMessages.SIDEBAR_OPTION_NAME)


# C945378
@pytest.mark.flaggedModerationPage
@pytest.mark.parametrize("flagged_content", ["question", "profile"])
def test_flagged_content_can_be_viewed_via_take_action(page: Page, flagged_content,
                                                       create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    report_text = "Automation test abuse report"

    with allure.step("Creating the content owner, reporter and moderator accounts"):
        content_owner = create_user_factory()
        reporter = create_user_factory()
        forum_moderator = create_user_factory(groups=["Forum Moderators"])

    if flagged_content == "question":
        filter_type, filter_reason = "question", "spam"
        with allure.step("Posting a Firefox product question with the content owner account"):
            posted_question = post_firefox_product_question_flow(page, content_owner)
            flagged_identifier = posted_question["question_details"]["aaq_subject"]

        with allure.step("Reporting the question as abusive with the reporter account"):
            utilities.start_existing_session(cookies=reporter)
            sumo_pages.aaq_flow.report_question_abuse(text=report_text)
    else:
        filter_type, filter_reason = "profile", "abuse"
        flagged_identifier = content_owner["username"]
        with allure.step("Reporting the content owner's profile as abusive with the reporter "
                         "account"):
            utilities.start_existing_session(cookies=reporter)
            utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
                flagged_identifier))
            sumo_pages.user_profile_flow.report_user_profile(
                report_reason="Abusive content", report_details=report_text)

    with allure.step("Signing in with the Forum Moderator and navigating to the freshly flagged "
                     "ticket"):
        utilities.start_existing_session(cookies=forum_moderator)
        _go_to_flagged_ticket(utilities, sumo_pages, filter_reason, filter_type)

    with allure.step("Clicking on the 'View' button of the flagged content's 'Take Action' "
                     "section"):
        sumo_pages.moderate_forum_content_page.click_take_action_view_option(flagged_identifier)

    with check, allure.step("Verifying that the flagged content is brought into view"):
        if flagged_content == "question":
            expect(sumo_pages.question_page.questions_header).to_have_text(flagged_identifier)
        else:
            expect(sumo_pages.my_profile_page.display_name_header).to_have_text(flagged_identifier)


# C945379
@pytest.mark.flaggedModerationPage
@pytest.mark.parametrize("flagged_content", ["question", "reply"])
def test_flagged_content_can_be_edited_via_take_action(page: Page, flagged_content,
                                                       create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    edited_content = "Automation edited content " + utilities.generate_random_number(1, 1000)

    with allure.step("Creating the question author and reporter accounts"):
        question_author = create_user_factory()
        reporter = create_user_factory()

    with allure.step("Posting a Firefox product question with the author account"):
        posted_question = post_firefox_product_question_flow(page, question_author)
        question_id = posted_question["question_details"]["question_id"]

    reply_id = ""
    if flagged_content == "question":
        filter_type = "question"
        flagged_identifier = posted_question["question_details"]["aaq_subject"]
    else:
        filter_type = "answer"
        with allure.step("Posting a reply to the question with the author account"):
            flagged_identifier = (f"Automation reply {question_author['username']} "
                                  + utilities.generate_random_number(1, 1000))
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=question_author["username"], reply=flagged_identifier)

    with allure.step("Reporting the content as abusive with the reporter account"):
        utilities.start_existing_session(cookies=reporter)
        if flagged_content == "question":
            sumo_pages.aaq_flow.report_question_abuse(text="Automation abuse report")
        else:
            sumo_pages.aaq_flow.report_question_abuse(
                answer_id=reply_id, text="Automation abuse report")

    with allure.step("Signing in with an admin account and navigating to the freshly flagged "
                     "ticket"):
        utilities.start_existing_session(session_file_name=staff_user)
        _go_to_flagged_ticket(utilities, sumo_pages, "spam", filter_type)

    with check, allure.step("Clicking the 'Edit' button and verifying that the post edit form is "
                            "displayed"):
        sumo_pages.moderate_forum_content_page.click_take_action_edit_option(flagged_identifier)
        if flagged_content == "question":
            expect(page).to_have_url(re.compile(r".*/questions/\d+/edit$"))
            expect(sumo_pages.aaq_form_page.save_edit_question_button).to_be_visible()
        else:
            expect(page).to_have_url(re.compile(r".*/questions/\d+/edit/\d+$"))
            expect(sumo_pages.aaq_form_page.form_update_answer_button).to_be_visible()

    with allure.step("Editing the content and submitting the changes"):
        if flagged_content == "question":
            sumo_pages.aaq_flow.editing_question_flow(body=edited_content)
        else:
            sumo_pages.aaq_flow.editing_reply_flow(answer_id=reply_id, reply_body=edited_content)

    with check, allure.step("Verifying that the moderator is redirected to the post and that the "
                            "edit was applied"):
        expect(sumo_pages.question_page.questions_header).to_be_visible()
        if flagged_content == "question":
            expect(sumo_pages.question_page.question(question_id)).to_contain_text(edited_content)
        else:
            expect(sumo_pages.question_page.reply(reply_id)).to_contain_text(edited_content)

    with check, allure.step("Verifying that the 'Modified by' message is displayed for the "
                            "flagged post"):
        container_id = question_id if flagged_content == "question" else reply_id
        expect(sumo_pages.question_page.modified_by_text(container_id)).to_be_visible()


# C945380
@pytest.mark.flaggedModerationPage
@pytest.mark.parametrize("flagged_content", ["question", "reply"])
def test_flagged_content_can_be_deleted_via_take_action(page: Page, flagged_content,
                                                        create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Creating the question author and reporter accounts"):
        question_author = create_user_factory()
        reporter = create_user_factory()

    with allure.step("Posting a Firefox product question with the author account"):
        posted_question = post_firefox_product_question_flow(page, question_author)
        question_id = posted_question["question_details"]["question_id"]
        question_number = question_id.split("-")[-1]

    with allure.step("Posting two replies to the question so that it has multiple replies"):
        sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=question_author["username"],
            reply=(f"First automation reply {question_author['username']} "
                   + utilities.generate_random_number(1, 1000)))
        second_reply_content = (f"Second automation reply {question_author['username']} "
                                + utilities.generate_random_number(1, 1000))
        second_reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=question_author["username"], reply=second_reply_content)
        second_reply_number = second_reply_id.split("-")[-1]

    with allure.step("Reporting the targeted content as abusive with the reporter account"):
        utilities.start_existing_session(cookies=reporter)
        if flagged_content == "question":
            filter_type = "question"
            flagged_identifier = posted_question["question_details"]["aaq_subject"]
            sumo_pages.aaq_flow.report_question_abuse(text="Automation abuse report")
        else:
            filter_type = "answer"
            flagged_identifier = second_reply_content
            sumo_pages.aaq_flow.report_question_abuse(
                answer_id=second_reply_id, text="Automation abuse report")

    with allure.step("Signing in with an admin account and navigating to the freshly flagged "
                     "ticket"):
        utilities.start_existing_session(session_file_name=staff_user)
        _go_to_flagged_ticket(utilities, sumo_pages, "spam", filter_type)

    with check, allure.step("Clicking the 'Delete' button and verifying that the delete "
                            "confirmation page of the correct flagged item is displayed"):
        sumo_pages.moderate_forum_content_page.click_take_action_delete_option(flagged_identifier)
        if flagged_content == "question":
            expect(page).to_have_url(re.compile(rf".*/questions/{question_number}/delete$"))
            expect(sumo_pages.question_page.delete_confirmation_heading).to_have_text(
                QuestionPageMessages.DELETE_QUESTION_CONFIRMATION_HEADING)
        else:
            expect(page).to_have_url(re.compile(
                rf".*/questions/{question_number}/delete/{second_reply_number}$"))
            expect(sumo_pages.question_page.delete_confirmation_heading).to_have_text(
                QuestionPageMessages.DELETE_ANSWER_CONFIRMATION_HEADING)
        expect(sumo_pages.question_page.delete_confirmation_section).to_contain_text(
            flagged_identifier)

    with allure.step("Confirming the deletion"):
        sumo_pages.question_page.click_delete_this_question_button()

    with check, allure.step("Filtering the flagged queue by reason and verifying that the flag "
                            "was automatically removed"):
        _go_to_flagged_ticket(utilities, sumo_pages, "spam")
        expect(sumo_pages.moderate_forum_content_page.flagged_question(
            flagged_identifier)).to_be_hidden()


def _go_to_last_page_of_filtered_queue(utilities, sumo_pages):
    utilities.navigate_to_link(utilities.get_page_url())
    if sumo_pages.moderate_forum_content_page.is_paginator_visible():
        sumo_pages.moderate_forum_content_page.click_on_last_pagination_element()


def _go_to_flagged_ticket(utilities, sumo_pages, reason_value, content_type_label=None):
    mfc = sumo_pages.moderate_forum_content_page
    utilities.navigate_to_link(ModerateForumContentPageMessages.PAGE_URL)
    if content_type_label:
        mfc.filter_flagged_content_by_type(content_type_label)
    mfc.filter_flagged_content_by_reason(reason_value)
    _go_to_last_page_of_filtered_queue(utilities, sumo_pages)


# C2749371
@pytest.mark.flaggedModerationPage
def test_flagged_page_filter_by_reason(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    reasons = [
        ("Spam or other unrelated content", "spam"),
        ("Inappropriate language/dialog", "language"),
        ("Abusive content", "abuse"),
        ("Other (please specify)", "other"),
    ]

    with allure.step("Creating the reporter account"):
        reporter = create_user_factory()

    with allure.step("Flagging one profile for each reason with the reporter account"):
        utilities.start_existing_session(cookies=reporter)
        flagged_usernames = {}
        for label, value in reasons:
            target = create_user_factory()
            utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
                target["username"]))
            sumo_pages.user_profile_flow.report_user_profile(
                report_reason=label, report_details="Automation filter report")
            flagged_usernames[value] = target["username"]

    with allure.step("Signing in with an admin account and navigating to the flagged page"):
        utilities.start_existing_session(session_file_name=staff_user)
        utilities.navigate_to_link(ModerateForumContentPageMessages.PAGE_URL)

    for index, (label, value) in enumerate(reasons):
        other_value = reasons[(index + 1) % len(reasons)][1]
        with check, allure.step(f"Filtering by the '{label}' reason and verifying the results"):
            sumo_pages.moderate_forum_content_page.filter_flagged_content_by_reason(value)
            expect(page).to_have_url(re.compile(rf".*[?&]reason={value}"))
            _go_to_last_page_of_filtered_queue(utilities, sumo_pages)
            expect(sumo_pages.moderate_forum_content_page.profile_flagged_ticket(
                flagged_usernames[value])).to_be_visible()
            expect(sumo_pages.moderate_forum_content_page.profile_flagged_ticket(
                flagged_usernames[other_value])).to_be_hidden()

    with check, allure.step("Selecting 'All reasons' and verifying that a flag is shown "
                            "regardless of its reason"):
        sumo_pages.moderate_forum_content_page.filter_flagged_content_by_reason("")
        expect(page).not_to_have_url(re.compile(r".*[?&]reason="))
        _go_to_last_page_of_filtered_queue(utilities, sumo_pages)
        expect(sumo_pages.moderate_forum_content_page.profile_flagged_ticket(
            flagged_usernames["other"])).to_be_visible()


# C2749371
@pytest.mark.flaggedModerationPage
def test_flagged_page_filter_by_type(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    mfc = sumo_pages.moderate_forum_content_page
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)

    with allure.step("Creating the question author, reporter and to-be-flagged profile accounts"):
        question_author = create_user_factory()
        reporter = create_user_factory()
        flagged_profile = create_user_factory()

    with allure.step("Posting a Firefox product question and a reply with the author account"):
        posted_question = post_firefox_product_question_flow(page, question_author)
        question_subject = posted_question["question_details"]["aaq_subject"]
        reply_content = "Automation reply " + utilities.generate_random_number(1, 1000)
        reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
            repliant_username=question_author["username"], reply=reply_content)

    with allure.step("Flagging the question, the reply and a profile with the reporter account"):
        utilities.start_existing_session(cookies=reporter)
        sumo_pages.aaq_flow.report_question_abuse(text="Automation filter report")
        sumo_pages.aaq_flow.report_question_abuse(
            answer_id=reply_id, text="Automation filter report")
        utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
            flagged_profile["username"]))
        sumo_pages.user_profile_flow.report_user_profile(
            report_reason="Abusive content", report_details="Automation filter report")

    with allure.step("Signing in with an admin account and navigating to the flagged page"):
        utilities.start_existing_session(session_file_name=staff_user)
        utilities.navigate_to_link(ModerateForumContentPageMessages.PAGE_URL)

    type_cases = [
        ("question", mfc.flagged_question(question_subject),
         mfc.profile_flagged_ticket(flagged_profile["username"])),
        ("answer", mfc.flagged_question(reply_content),
         mfc.flagged_question(question_subject)),
        ("profile", mfc.profile_flagged_ticket(flagged_profile["username"]),
         mfc.flagged_question(question_subject)),
    ]

    for type_label, matching_item, non_matching_item in type_cases:
        with check, allure.step(f"Filtering by the '{type_label}' type and verifying the results"):
            mfc.filter_flagged_content_by_type(type_label)
            expect(page).to_have_url(re.compile(r".*[?&]content_type=\d+"))
            _go_to_last_page_of_filtered_queue(utilities, sumo_pages)
            expect(matching_item).to_be_visible()
            expect(non_matching_item).to_be_hidden()

    with check, allure.step("Selecting 'All types' and verifying that a flag is shown regardless "
                            "of its type"):
        mfc.filter_flagged_content_by_type("All types")
        expect(page).not_to_have_url(re.compile(r".*[?&]content_type="))
        _go_to_last_page_of_filtered_queue(utilities, sumo_pages)
        expect(mfc.profile_flagged_ticket(flagged_profile["username"])).to_be_visible()


# C945383
@pytest.mark.flaggedModerationPage
def test_flagged_ticket_usernames_link_to_the_correct_profiles(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    mfc = sumo_pages.moderate_forum_content_page

    with allure.step("Creating the question author, reporter and moderator accounts"):
        question_author = create_user_factory()
        reporter = create_user_factory()
        forum_moderator = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Posting a Firefox product question with the author account"):
        posted_question = post_firefox_product_question_flow(page, question_author)
        question_subject = posted_question["question_details"]["aaq_subject"]

    with allure.step("Reporting the question as abusive with the reporter account"):
        utilities.start_existing_session(cookies=reporter)
        sumo_pages.aaq_flow.report_question_abuse(text="Automation abuse report")

    with allure.step("Signing in with the Forum Moderator and navigating to the freshly flagged "
                     "ticket"):
        utilities.start_existing_session(cookies=forum_moderator)
        _go_to_flagged_ticket(utilities, sumo_pages, "spam", "question")

    with check, allure.step("Verifying that the 'Created:' and 'Flagged:' usernames are correct"):
        expect(mfc.created_by_link_text(question_subject)).to_have_text(
            question_author["username"])
        expect(mfc.flagged_by_link_text(question_subject)).to_have_text(reporter["username"])

    with check, allure.step("Verifying that the 'Created:' username links to the author profile"):
        mfc.click_created_by_link(question_subject)
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(
            question_author["username"]))

    with allure.step("Navigating back to the freshly flagged ticket"):
        _go_to_flagged_ticket(utilities, sumo_pages, "spam", "question")

    with check, allure.step("Verifying that the 'Flagged:' username links to the reporter "
                            "profile"):
        mfc.click_flagged_by_link(question_subject)
        expect(page).to_have_url(MyProfileMessages.get_my_profile_stage_url(reporter["username"]))


REPORT_REASONS = [
    pytest.param(("Spam or other unrelated content", "spam"), id="spam"),
    pytest.param(("Inappropriate language/dialog", "language"), id="language"),
    pytest.param(("Abusive content", "abuse"), id="abuse"),
    pytest.param(("Other (please specify)", "other"), id="other"),
]


# C945382
@pytest.mark.flaggedModerationPage
@pytest.mark.parametrize("flagged_content", ["question", "reply", "profile"])
@pytest.mark.parametrize("report_reason", REPORT_REASONS)
def test_rejecting_a_flag_preserves_content_and_removes_ticket(page: Page, flagged_content,
                                                               report_reason, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    mfc = sumo_pages.moderate_forum_content_page
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    reason_label, reason_value = report_reason
    content_type_label = "answer" if flagged_content == "reply" else flagged_content
    report_text = "Automation reject report"

    with allure.step("Creating the content owner and reporter accounts"):
        content_owner = create_user_factory()
        reporter = create_user_factory()

    question_page_url = ""
    reply_id = ""
    if flagged_content == "question":
        with allure.step("Posting a Firefox product question with the content owner account"):
            posted_question = post_firefox_product_question_flow(page, content_owner)
            question_page_url = posted_question["question_details"]["question_page_url"]
            flagged_identifier = posted_question["question_details"]["aaq_subject"]

        with allure.step(f"Reporting the question with the '{reason_label}' reason as the "
                         "reporter account"):
            utilities.start_existing_session(cookies=reporter)
            sumo_pages.aaq_flow.report_question_abuse(text=report_text, report_reason=reason_value)
    elif flagged_content == "reply":
        with allure.step("Posting a Firefox product question and a reply with the content owner "
                         "account"):
            posted_question = post_firefox_product_question_flow(page, content_owner)
            question_page_url = posted_question["question_details"]["question_page_url"]
            # The owner's username keeps the reply text unique across parallel workers so the
            # flagged-queue text locator can never match another test's reply.
            flagged_identifier = (f"Automation reply {content_owner['username']} "
                                  + utilities.generate_random_number(1, 1000))
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=content_owner["username"], reply=flagged_identifier)

        with allure.step(f"Reporting the reply with the '{reason_label}' reason as the reporter "
                         "account"):
            utilities.start_existing_session(cookies=reporter)
            sumo_pages.aaq_flow.report_question_abuse(
                answer_id=reply_id, text=report_text, report_reason=reason_value)
    else:
        flagged_identifier = content_owner["username"]
        with allure.step(f"Reporting the content owner's profile with the '{reason_label}' reason "
                         "as the reporter account"):
            utilities.start_existing_session(cookies=reporter)
            utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
                flagged_identifier))
            sumo_pages.user_profile_flow.report_user_profile(
                report_reason=reason_label, report_details=report_text)

    with allure.step("Signing in with an admin account and navigating to the freshly flagged "
                     "ticket"):
        utilities.start_existing_session(session_file_name=staff_user)
        _go_to_flagged_ticket(utilities, sumo_pages, reason_value, content_type_label)

    with allure.step("Selecting the second ('Rejected') option from the update-status dropdown "
                     "and clicking the 'Update' button"):
        if flagged_content == "profile":
            mfc.select_update_profile_status_option(
                flagged_identifier, ModerateForumContentPageMessages.UPDATE_STATUS_SECOND_VALUE)
            mfc.click_on_the_update_profile_button(flagged_identifier)
        else:
            mfc.select_update_status_option(
                flagged_identifier, ModerateForumContentPageMessages.UPDATE_STATUS_SECOND_VALUE)
            mfc.click_on_the_update_button(flagged_identifier)

    with check, allure.step("Filtering the flagged queue by reason and verifying that the ticket "
                            "was removed"):
        _go_to_flagged_ticket(utilities, sumo_pages, reason_value)
        if flagged_content == "profile":
            expect(mfc.profile_flagged_ticket(flagged_identifier)).to_be_hidden()
        else:
            expect(mfc.flagged_question(flagged_identifier)).to_be_hidden()

    with check, allure.step("Verifying that the content owner was not deactivated"):
        utilities.navigate_to_link(ModerateForumContentPageMessages.DEACTIVATED_USERS_PAGE_URL)
        expect(mfc.deactivation_log_deactivated_user(
            content_owner["username"])).to_be_hidden()

    with check, allure.step("Verifying that the flagged content was not removed"):
        if flagged_content == "question":
            utilities.navigate_to_link(question_page_url)
            expect(sumo_pages.question_page.questions_header).to_have_text(flagged_identifier)
        elif flagged_content == "reply":
            utilities.navigate_to_link(question_page_url)
            expect(sumo_pages.question_page.reply(reply_id)).to_contain_text(flagged_identifier)
        else:
            utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
                flagged_identifier))
            expect(sumo_pages.my_profile_page.display_name_header).to_have_text(flagged_identifier)


# C945381
@pytest.mark.flaggedModerationPage
@pytest.mark.parametrize("flagged_content", ["question", "reply", "profile"])
@pytest.mark.parametrize("report_reason", REPORT_REASONS)
def test_accepting_a_flag_preserves_content_and_removes_ticket(page: Page, flagged_content,
                                                               report_reason, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    mfc = sumo_pages.moderate_forum_content_page
    staff_user = utilities.username_extraction_from_email(utilities.staff_user)
    reason_label, reason_value = report_reason
    content_type_label = "answer" if flagged_content == "reply" else flagged_content
    report_text = "Automation accept report"

    with allure.step("Creating the content owner and reporter accounts"):
        content_owner = create_user_factory()
        reporter = create_user_factory()

    question_page_url = ""
    reply_id = ""
    if flagged_content == "question":
        with allure.step("Posting a Firefox product question with the content owner account"):
            posted_question = post_firefox_product_question_flow(page, content_owner)
            question_page_url = posted_question["question_details"]["question_page_url"]
            flagged_identifier = posted_question["question_details"]["aaq_subject"]

        with allure.step(f"Reporting the question with the '{reason_label}' reason as the "
                         "reporter account"):
            utilities.start_existing_session(cookies=reporter)
            sumo_pages.aaq_flow.report_question_abuse(text=report_text, report_reason=reason_value)
    elif flagged_content == "reply":
        with allure.step("Posting a Firefox product question and a reply with the content owner "
                         "account"):
            posted_question = post_firefox_product_question_flow(page, content_owner)
            question_page_url = posted_question["question_details"]["question_page_url"]
            flagged_identifier = (f"Automation reply {content_owner['username']} "
                                  + utilities.generate_random_number(1, 1000))
            reply_id = sumo_pages.aaq_flow.post_question_reply_flow(
                repliant_username=content_owner["username"], reply=flagged_identifier)

        with allure.step(f"Reporting the reply with the '{reason_label}' reason as the reporter "
                         "account"):
            utilities.start_existing_session(cookies=reporter)
            sumo_pages.aaq_flow.report_question_abuse(
                answer_id=reply_id, text=report_text, report_reason=reason_value)
    else:
        flagged_identifier = content_owner["username"]
        with allure.step(f"Reporting the content owner's profile with the '{reason_label}' reason "
                         "as the reporter account"):
            utilities.start_existing_session(cookies=reporter)
            utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
                flagged_identifier))
            sumo_pages.user_profile_flow.report_user_profile(
                report_reason=reason_label, report_details=report_text)

    with allure.step("Signing in with an admin account and navigating to the freshly flagged "
                     "ticket"):
        utilities.start_existing_session(session_file_name=staff_user)
        _go_to_flagged_ticket(utilities, sumo_pages, reason_value, content_type_label)

    with allure.step("Selecting the first ('Accepted and Fixed') option from the update-status "
                     "dropdown and clicking the 'Update' button"):
        if flagged_content == "profile":
            mfc.select_update_profile_status_option(
                flagged_identifier, ModerateForumContentPageMessages.UPDATE_STATUS_FIRST_VALUE)
            mfc.click_on_the_update_profile_button(flagged_identifier)
        else:
            mfc.select_update_status_option(
                flagged_identifier, ModerateForumContentPageMessages.UPDATE_STATUS_FIRST_VALUE)
            mfc.click_on_the_update_button(flagged_identifier)

    with check, allure.step("Filtering the flagged queue by reason and verifying that the ticket "
                            "was removed"):
        _go_to_flagged_ticket(utilities, sumo_pages, reason_value)
        if flagged_content == "profile":
            expect(mfc.profile_flagged_ticket(flagged_identifier)).to_be_hidden()
        else:
            expect(mfc.flagged_question(flagged_identifier)).to_be_hidden()

    with check, allure.step("Verifying that the content owner was not deactivated"):
        utilities.navigate_to_link(ModerateForumContentPageMessages.DEACTIVATED_USERS_PAGE_URL)
        expect(mfc.deactivation_log_deactivated_user(
            content_owner["username"])).to_be_hidden()

    with check, allure.step("Verifying that the flagged content was not removed"):
        if flagged_content == "question":
            utilities.navigate_to_link(question_page_url)
            expect(sumo_pages.question_page.questions_header).to_have_text(flagged_identifier)
        elif flagged_content == "reply":
            utilities.navigate_to_link(question_page_url)
            expect(sumo_pages.question_page.reply(reply_id)).to_contain_text(flagged_identifier)
        else:
            utilities.navigate_to_link(MyProfileMessages.get_my_profile_stage_url(
                flagged_identifier))
            expect(sumo_pages.my_profile_page.display_name_header).to_have_text(flagged_identifier)


