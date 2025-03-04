import allure
import pytest
from pytest_check import check

from playwright.sync_api import expect, Page
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.aaq_form_page_messages import (
    AAQFormMessages)
from playwright_tests.messages.ask_a_question_messages.AAQ_messages.question_page_messages import \
    QuestionPageMessages
from playwright_tests.messages.ask_a_question_messages.contact_support_messages import (
    ContactSupportMessages)
from playwright_tests.messages.contribute_messages.con_pages.con_page_messages import (
    ContributePageMessages)
from playwright_tests.pages.sumo_pages import SumoPages


# T5696741, T5696742
@pytest.mark.aaqPage
def test_community_card_and_helpful_tip_are_displayed_for_freemium_product(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating to each freemium aaq form"):
        for freemium_product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][freemium_product]
            )

            with allure.step(f"Verifying that the helpful tip card is displayed for the "
                             f"{freemium_product} product"):
                expect(sumo_pages.aaq_form_page.get_helpful_tip_locator()).to_be_visible()

            with allure.step("Clicking on the 'Learn More' button from the community help "
                             "card and verifying that we are on the contribute messages page"):
                sumo_pages.aaq_form_page.click_on_learn_more_button()
                expect(page).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)


# C2188694, C2188695
@pytest.mark.aaqPage
def test_community_card_and_helpful_tip_not_displayed_for_premium_products(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating to each premium aaq form"):
        for premium_product in utilities.general_test_data["premium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][premium_product]
            )

            with allure.step(f"Verifying that the helpful tip options is displayed for the "
                             f"{premium_product}"):
                expect(sumo_pages.aaq_form_page.get_helpful_tip_locator()).to_be_hidden()

            with allure.step("Verifying that the 'Learn More' button from the community help "
                             "banner is not displayed"):
                expect(sumo_pages.aaq_form_page.get_learn_more_button_locator()).to_be_hidden()


# C1511570
@pytest.mark.aaqPage
@pytest.mark.parametrize("username", ['', 'TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR'])
def test_scam_banner_premium_products_not_displayed(page: Page, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    if username != '':
        with allure.step(f"Singing in with {username} user"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts[username]
            ))

    with allure.step("Navigating to each premium product solutions page"):
        for premium_product in utilities.general_test_data["premium_products"]:
            utilities.navigate_to_link(
                utilities.general_test_data["product_solutions"][premium_product]
            )

            with allure.step(f"Verifying that the sam banner is not displayed for "
                             f"{premium_product} card"):
                expect(sumo_pages.product_solutions_page.get_scam_banner_locator()).to_be_hidden()

            if username != '':
                with allure.step("Clicking on the Ask Now button and verifying that the scam "
                                 "banner is not displayed"):
                    sumo_pages.product_solutions_page.click_ask_now_button()
                    utilities.wait_for_url_to_be(
                        utilities.aaq_question_test_data["products_aaq_url"][premium_product]
                    )
                    expect(sumo_pages.product_solutions_page.get_scam_banner_locator()
                           ).to_be_hidden()


# C2190040
@pytest.mark.aaqPage
@pytest.mark.parametrize("username", ['', 'TEST_ACCOUNT_12', 'TEST_ACCOUNT_MODERATOR'])
def test_scam_banner_for_freemium_products_is_displayed(page: Page, username):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    if username != '':
        with allure.step(f"Signing in with {username} user"):
            utilities.start_existing_session(utilities.username_extraction_from_email(
                utilities.user_secrets_accounts[username]
            ))

    with allure.step("Navigating to each freemium product solutions page"):
        for freemium_product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.general_test_data["product_solutions"][freemium_product]
            )

            with check, allure.step("Verifying that the 'Learn More' button contains the "
                                    "correct link"):
                assert sumo_pages.product_solutions_page.get_scam_alert_banner_link(
                ) == QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK

            if username != '':
                with check, allure.step("Clicking on the Ask Now button and verifying that "
                                        "the 'Learn More' button contains the correct link"):
                    sumo_pages.product_solutions_page.click_ask_now_button()
                    utilities.wait_for_url_to_be(
                        utilities.aaq_question_test_data["products_aaq_url"][freemium_product]
                    )
                    assert sumo_pages.product_solutions_page.get_scam_alert_banner_link(
                    ) == QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK


# T5696596
@pytest.mark.aaqPage
def test_corresponding_aaq_product_name_and_image_are_displayed(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating to each product aaq form"):
        for product in utilities.aaq_question_test_data["products_aaq_url"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            # This needs to change when we add the Mozilla Account icon/product.
            if product != "Mozilla Account":
                with allure.step("Verifying that the product image is displayed"):
                    expect(sumo_pages.aaq_form_page.get_product_image_locator()).to_be_visible()
            else:
                with allure.step("Verifying that the product image is hidden for Mozilla "
                                 "Account product"):
                    expect(sumo_pages.aaq_form_page.get_product_image_locator()).to_be_visible()

            with check, allure.step("Verifying that the correct product header is displayed"):
                assert sumo_pages.aaq_form_page.get_aaq_form_page_heading() == product


# T5696594, T5696595
@pytest.mark.aaqPage
def test_progress_milestone_redirect(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts['TEST_ACCOUNT_12']
        ))

    with allure.step("Navigating to each product AAQ form"):
        for product in utilities.aaq_question_test_data["products_aaq_url"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            with check, allure.step("Verifying that the correct in progress milestone is "
                                    "displayed"):
                assert sumo_pages.aaq_form_page.get_in_progress_item_label(
                ) == AAQFormMessages.IN_PROGRESS_MILESTONE

            with allure.step(f"Clicking on the {AAQFormMessages.COMPLETED_MILESTONE_TWO} "
                             f"milestone and verifying that we are on the correct product "
                             f"solutions page"):
                sumo_pages.aaq_form_page.click_on_a_particular_completed_milestone(
                    AAQFormMessages.COMPLETED_MILESTONE_TWO)
                expect(page).to_have_url(
                    utilities.general_test_data["product_solutions"][product])

            with allure.step(f"Navigating back to the aaq form and clicking on the "
                             f"{AAQFormMessages.COMPLETED_MILESTONE_ONE} milestone"):
                utilities.navigate_to_link(
                    utilities.aaq_question_test_data["products_aaq_url"][product])
                sumo_pages.aaq_form_page.click_on_a_particular_completed_milestone(
                    AAQFormMessages.COMPLETED_MILESTONE_ONE)
                expect(page).to_have_url(ContactSupportMessages.PAGE_URL_CHANGE_PRODUCT_REDIRECT)


# T5696600
@pytest.mark.aaqPage
def test_aaq_form_cancel_button_freemium_products(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with a non-admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MESSAGE_1"]
        ))

    with allure.step("Accessing the 'My profile' page via the top-navbar menu and extracting "
                     "the original number of posted questions"):
        sumo_pages.top_navbar.click_on_view_profile_option()
        original_number_of_questions = utilities.number_extraction_from_string(
            sumo_pages.my_profile_page.get_my_profile_questions_text()
        )

    with allure.step("Navigating to each product AAQ form"):
        for product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            with allure.step("Adding data inside the AAQ form fields and clicking on the "
                             "cancel button"):
                sumo_pages.aaq_flow.add__valid_data_to_all_aaq_fields_without_submitting(
                    subject=utilities.aaq_question_test_data["valid_firefox_question"]
                    ["subject"],
                    topic_value=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
                    body_text=utilities.aaq_question_test_data["valid_firefox_question"]
                    ["question_body"]
                )
                sumo_pages.aaq_form_page.click_aaq_form_cancel_button()

            with allure.step("Verifying that we are redirected back to the correct product "
                             "solutions page"):
                expect(page).to_have_url(
                    utilities.general_test_data["product_solutions"][product])

            with check, allure.step("Navigating back to the My Profile page and verifying "
                                    "that the correct number of posted questions is "
                                    "displayed"):
                sumo_pages.top_navbar.click_on_view_profile_option()
                new_number = utilities.number_extraction_from_string(
                    sumo_pages.my_profile_page.get_my_profile_questions_text()
                )
                assert new_number == original_number_of_questions


# T5696597, T5696601, T5696602
@pytest.mark.aaqPage
def test_post_aaq_questions_for_all_freemium_products_topics(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Navigating to each product AAQ form"):
        for product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            for topic in sumo_pages.aaq_form_page.get_aaq_form_topic_options():
                with allure.step(f"Submitting question for {product} product"):
                    question_info = sumo_pages.aaq_flow.submit_an_aaq_question(
                        subject=utilities.aaq_question_test_data["valid_firefox_question"]
                        ["subject"],
                        topic_name=topic,
                        body=utilities.aaq_question_test_data["valid_firefox_question"]
                        ["question_body"],
                        attach_image=False,
                        expected_locator=sumo_pages.question_page.questions_header
                    )

                with allure.step("Verifying that the correct implicit tags are added to the "
                                 "question"):
                    topic_s = utilities.aaq_question_test_data['aaq_topic_tags'][product][topic]
                    if isinstance(topic_s, list):
                        slugs = topic_s
                    else:
                        slugs = [topic_s]
                    if (utilities.aaq_question_test_data['aaq_topic_tags'][product]
                            ['default_slug'] != "none"):
                        slugs.append(
                            utilities.aaq_question_test_data['aaq_topic_tags'][product]
                            ['default_slug']
                        )
                    assert (
                        all(map(
                            lambda x: x in sumo_pages.question_page.get_question_tag_options(
                                is_moderator=True
                            ),
                            slugs))
                    )

                with allure.step("Clicking on the 'My Questions' banner option and Verifying "
                                 "that the posted question is displayed inside the 'My "
                                 "Questions page"):
                    sumo_pages.question_page.click_on_my_questions_banner_option()
                    expect(sumo_pages.my_questions_page.get_listed_question(
                        question_info['aaq_subject'])).to_be_visible()

                with allure.step("Clicking on the question and deleting it"):
                    sumo_pages.my_questions_page.click_on_a_question_by_name(
                        question_info['aaq_subject']
                    )
                    sumo_pages.aaq_flow.deleting_question_flow()

                with allure.step("Verifying that the question is no longer displayed inside "
                                 "My Questions page"):
                    sumo_pages.top_navbar.click_on_my_questions_profile_option()
                    expect(
                        sumo_pages.my_questions_page.get_listed_question(
                            question_info['aaq_subject'])).to_be_hidden()

                with allure.step(f"Navigating back to the {product} product aa form"):
                    utilities.navigate_to_link(
                        utilities.aaq_question_test_data["products_aaq_url"][product])


# T5696633
@pytest.mark.aaqPage
def test_share_firefox_data_functionality(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Navigating to the Firefox AAQ form page and clicking on the 'Share "
                     "Data' option"):
        utilities.navigate_to_link(
            utilities.aaq_question_test_data["products_aaq_url"]["Firefox"])
        sumo_pages.aaq_form_page.click_on_share_data_button()

    with check, allure.step("Verifying that the 'try these manual steps' contains the "
                            "correct link"):
        assert sumo_pages.aaq_form_page.get_try_these_manual_steps_link(
        ) == QuestionPageMessages.TRY_THESE_MANUAL_STEPS_LINK

    with allure.step("Adding data inside AAQ form fields without submitting the form"):
        sumo_pages.aaq_flow.add__valid_data_to_all_aaq_fields_without_submitting(
            subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
            topic_value=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
            body_text=utilities.aaq_question_test_data["valid_firefox_question"]
            ["question_body"]
        )

    with allure.step("Adding text inside the troubleshooting information field and "
                     "submitting the AAQ question"):
        sumo_pages.aaq_form_page.add_text_to_troubleshooting_information_textarea(
            utilities.aaq_question_test_data["troubleshooting_information"]
        )
        utilities.re_call_function_on_error(
            sumo_pages.aaq_form_page.click_aaq_form_submit_button,
            expected_locator=sumo_pages.question_page.questions_header
        )

    with allure.step("Verifying that the troubleshooting information is displayed"):
        sumo_pages.question_page.click_on_question_details_button()
        sumo_pages.question_page.click_on_more_system_details_option()
        expect(
            sumo_pages.question_page.get_more_information_with_text_locator(
                utilities.aaq_question_test_data["troubleshooting_information"]
            )
        ).to_be_visible()

    with allure.step("Closing the additional details panel and deleting the posted question"):
        sumo_pages.question_page.click_on_the_additional_system_panel_close()
        sumo_pages.aaq_flow.deleting_question_flow()


@pytest.mark.aaqPage
def test_additional_system_details_user_agent_information(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    with allure.step("Signing in with an admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Navigating to each product aaq form"):
        for product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            with allure.step(f"Submitting a question for the {product} product"):
                sumo_pages.aaq_flow.submit_an_aaq_question(
                    subject=utilities.aaq_question_test_data["valid_firefox_question"]
                    ["subject"],
                    topic_name=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
                    body=utilities.aaq_question_test_data["valid_firefox_question"]
                    ["question_body"],
                    attach_image=True,
                    expected_locator=sumo_pages.question_page.questions_header
                )

            with check, allure.step("Verifying that the correct user-agent information is "
                                    "displayed"):
                sumo_pages.question_page.click_on_question_details_button()
                sumo_pages.question_page.click_on_more_system_details_option()
                assert "User Agent: " + utilities.get_user_agent(
                ) == sumo_pages.question_page.get_user_agent_information()

            with allure.step("Closing the additional details panel and deleting the posted "
                             "questions"):
                sumo_pages.question_page.click_on_the_additional_system_panel_close()
                sumo_pages.aaq_flow.deleting_question_flow()


@pytest.mark.aaqPage
def test_system_details_information(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    troubleshooting_info = [
        utilities.aaq_question_test_data["troubleshoot_product_and_os_versions"][0],
        "Firefox " + utilities.aaq_question_test_data["troubleshoot_product_and_os_versions"][1]
    ]

    with allure.step("Signing in with an admin user account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Navigating to each product aaq form and and adding data without "
                     "submitting the form"):
        for product in utilities.general_test_data["freemium_products"]:
            if product == "Thunderbird" or product == "Thunderbird for Android":
                continue
            else:
                utilities.navigate_to_link(
                    utilities.aaq_question_test_data["products_aaq_url"][product])
                sumo_pages.aaq_flow.add__valid_data_to_all_aaq_fields_without_submitting(
                    subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
                    topic_value=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
                    body_text=utilities.aaq_question_test_data["valid_firefox_question"][
                        "question_body"]
                )

                with allure.step("Clicking on the 'Show details' option and adding data to "
                                 "product version and OS fields"):
                    sumo_pages.aaq_form_page.click_on_show_details_option()
                    sumo_pages.aaq_form_page.add_text_to_product_version_field(
                        utilities.aaq_question_test_data[
                            "troubleshoot_product_and_os_versions"][1]
                    )
                    sumo_pages.aaq_form_page.add_text_to_os_field(
                        utilities.aaq_question_test_data[
                            "troubleshoot_product_and_os_versions"][0]
                    )

                with check, allure.step("Submitting the AAQ question and verifying that the "
                                        "correct provided troubleshooting information is "
                                        "displayed"):
                    utilities.re_call_function_on_error(
                        sumo_pages.aaq_form_page.click_aaq_form_submit_button,
                        expected_locator=sumo_pages.question_page.questions_header
                    )

                    sumo_pages.question_page.click_on_question_details_button()
                    assert sumo_pages.question_page.get_system_details_information(
                    ) == troubleshooting_info

                with allure.step("Deleting the posted question"):
                    sumo_pages.aaq_flow.deleting_question_flow()


# T5696704
@pytest.mark.aaqPage
def test_premium_products_aaq(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    aaq_form_messages = AAQFormMessages()
    with allure.step("Signing in with an admin account"):
        utilities.start_existing_session(utilities.username_extraction_from_email(
            utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
        ))

    with allure.step("Navigating to each premium product contact form and sending a ticket"):
        for premium_product in utilities.general_test_data['premium_products']:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data['products_aaq_url'][premium_product]
            )
            utilities.wait_for_dom_to_load()
            premium_form_link = utilities.get_page_url()
            if premium_product == 'Mozilla VPN':
                sumo_pages.aaq_flow.submit_an_aaq_question(
                    subject=utilities.aaq_question_test_data['premium_aaq_question']['subject'],
                    body=utilities.aaq_question_test_data['premium_aaq_question']['body'],
                    is_premium=True
                )
            else:
                sumo_pages.aaq_flow.submit_an_aaq_question(
                    subject=utilities.aaq_question_test_data['premium_aaq_question']['subject'],
                    body=utilities.aaq_question_test_data['premium_aaq_question']['body'],
                    is_premium=True
                )
                if utilities.get_page_url() == premium_form_link:
                    utilities.re_call_function_on_error(
                        sumo_pages.aaq_form_page.click_aaq_form_submit_button,
                        with_force=True,
                        expected_locator=sumo_pages.question_page.questions_header
                    )

        with allure.step("Verifying that the correct success message is displayed"):
            assert sumo_pages.aaq_form_page.get_premium_card_submission_message(
            ) == aaq_form_messages.get_premium_ticket_submission_success_message(
                utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
            )


# C2635907
@pytest.mark.aaqPage
def test_loginless_mozilla_account_aaq(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    aaq_form_messages = AAQFormMessages()
    with allure.step("Sending 4 loginless tickets and verifying that the user is successfully "
                     "blocked after 3 submissions"):
        i = 1
        while i <= 4:
            sumo_pages.top_navbar.click_on_signin_signup_button()
            sumo_pages.auth_page.click_on_cant_sign_in_to_my_mozilla_account_link()
            sumo_pages.aaq_flow.submit_an_aaq_question(
                subject=utilities.aaq_question_test_data['premium_aaq_question']['subject'],
                body=utilities.aaq_question_test_data['premium_aaq_question']['body'],
                is_premium=True,
                email=utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"],
                is_loginless=True
            )
            if i <= 3:
                with allure.step("Verifying that the correct success message is displayed"):
                    assert sumo_pages.aaq_form_page.get_premium_card_submission_message(
                    ) == aaq_form_messages.get_premium_ticket_submission_success_message(
                        utilities.user_secrets_accounts["TEST_ACCOUNT_MODERATOR"]
                    )
            else:
                with allure.step("Verifying that submission error message is displayed"):
                    assert sumo_pages.aaq_form_page.get_premium_card_submission_message(
                    ) == aaq_form_messages.LOGINLESS_RATELIMIT_REACHED_MESSAGE
            i += 1
