import allure
import pytest
from pytest_check import check
from playwright.sync_api import expect, Page
from playwright_tests.core.utilities import Utilities, retry_on_502
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
def test_community_card_and_helpful_tip_are_displayed_for_freemium_product(page: Page,
                                                                           create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step("Signing in with a simple user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to each freemium aaq form"):
        for freemium_product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][freemium_product]
            )

            with check, allure.step(f"Verifying that the helpful tip card is displayed for the "
                                    f"{freemium_product} product"):
                expect(sumo_pages.aaq_form_page.helpful_tip_section).to_be_visible()

            with allure.step("Clicking on the 'Learn More' button from the community help "
                             "card and verifying that we are on the contribute messages page"):
                sumo_pages.common_web_elements.click_on_volunteer_learn_more_link()
                expect(page).to_have_url(ContributePageMessages.STAGE_CONTRIBUTE_PAGE_URL)


# C2188694, C2188695
@pytest.mark.aaqPage
def test_community_card_and_helpful_tip_not_displayed_for_premium_products(page: Page,
                                                                           create_user_factory):

    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step("Signing in with a simple user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to each premium aaq form"):
        for premium_product in utilities.general_test_data["premium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][premium_product]
            )

            with check, allure.step(f"Verifying that the helpful tip options is not displayed for"
                                    f" the {premium_product}"):
                expect(sumo_pages.aaq_form_page.helpful_tip_section).to_be_hidden()

            with allure.step("Verifying that the 'Learn More' button from the community help "
                             "banner is not displayed"):
                expect(sumo_pages.common_web_elements.learn_more_button).to_be_hidden()


# C1511570
@pytest.mark.aaqPage
@pytest.mark.parametrize("user_type", ['','Simple User', 'Forum Moderator'])
def test_scam_banner_premium_products_not_displayed(page: Page, user_type, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["Forum Moderators"])
    user_map = {'Simple User': test_user, 'Forum Moderator': test_user_two}

    with allure.step("Signing in to SUMO"):
        utilities.start_existing_session(cookies=user_map.get(user_type))

    with allure.step("Navigating to each premium product solutions page"):
        for premium_product in utilities.general_test_data["premium_products"]:
            utilities.navigate_to_link(
                utilities.general_test_data["product_solutions"][premium_product]
            )

            with check, allure.step(f"Verifying that the sam banner is not displayed for "
                                    f"{premium_product} card"):
                expect(sumo_pages.product_solutions_page.support_scams_banner).to_be_hidden()

            if user_type != '':
                with allure.step("Clicking on the Ask Now button and verifying that the scam "
                                 "banner is not displayed"):
                    sumo_pages.common_web_elements.click_on_aaq_button()
                    utilities.wait_for_url_to_be(
                        utilities.aaq_question_test_data["products_aaq_url"][premium_product]
                    )
                    expect(sumo_pages.product_solutions_page.support_scams_banner).to_be_hidden()


# C2190040
@pytest.mark.aaqPage
@pytest.mark.parametrize("user_type", ['', 'Simple User', 'Forum Moderator'])
def test_scam_banner_for_freemium_products_is_displayed(page: Page, user_type,
                                                        create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()
    test_user_two = create_user_factory(groups=["Forum Moderators"])
    user_map = {'Simple User': test_user, 'Forum Moderator': test_user_two}

    with allure.step("Sign in to SUMO"):
        utilities.start_existing_session(cookies=user_map.get(user_type))

    with allure.step("Navigating to each freemium product solutions page"):
        for freemium_product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.general_test_data["product_solutions"][freemium_product]
            )

            with check, allure.step("Verifying that the 'Learn More' button contains the "
                                    "correct link"):
                assert sumo_pages.product_solutions_page.get_scam_alert_banner_link(
                ) == QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK

            if user_type != '':
                with check, allure.step("Clicking on the Ask Now button and verifying that "
                                        "the 'Learn More' button contains the correct link"):
                    sumo_pages.common_web_elements.click_on_aaq_button()
                    utilities.wait_for_url_to_be(
                        utilities.aaq_question_test_data["products_aaq_url"][freemium_product]
                    )
                    assert sumo_pages.product_solutions_page.get_scam_alert_banner_link(
                    ) == QuestionPageMessages.AVOID_SCAM_SUPPORT_LEARN_MORE_LINK


# T5696596
@pytest.mark.aaqPage
def test_corresponding_aaq_product_name_and_image_are_displayed(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step("Signing in with a simple user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to each product aaq form"):
        for product in utilities.aaq_question_test_data["products_aaq_url"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            # This needs to change when we add the Mozilla Account icon/product.
            if product != "Mozilla Account":
                with check, allure.step("Verifying that the product image is displayed"):
                    expect(sumo_pages.aaq_form_page.aaq_page_logo).to_be_visible()
            else:
                with check, allure.step("Verifying that the product image is hidden for Mozilla "
                                        "Account product"):
                    expect(sumo_pages.aaq_form_page.aaq_page_logo).to_be_visible()

            with check, allure.step("Verifying that the correct product header is displayed"):
                assert sumo_pages.aaq_form_page.get_aaq_form_page_heading() == product


# T5696594, T5696595
@pytest.mark.aaqPage
def test_progress_milestone_redirect(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step("Signing in with a simple user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to each product AAQ form"):
        for product in utilities.aaq_question_test_data["products_aaq_url"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            with check, allure.step("Verifying that the correct in progress milestone is "
                                    "displayed"):
                assert sumo_pages.aaq_form_page.get_in_progress_item_label(
                ) == AAQFormMessages.IN_PROGRESS_MILESTONE

            with check, allure.step(f"Clicking on the {AAQFormMessages.COMPLETED_MILESTONE_TWO} "
                                    f"milestone and verifying that we are on the correct product "
                                    f"solutions page"):
                sumo_pages.aaq_form_page.click_on_a_particular_completed_milestone(
                    AAQFormMessages.COMPLETED_MILESTONE_TWO)
                expect(page).to_have_url(utilities.general_test_data["product_solutions"][product])

            with allure.step(f"Navigating back to the aaq form and clicking on the "
                             f"{AAQFormMessages.COMPLETED_MILESTONE_ONE} milestone"):
                utilities.navigate_to_link(
                    utilities.aaq_question_test_data["products_aaq_url"][product])
                sumo_pages.aaq_form_page.click_on_a_particular_completed_milestone(
                    AAQFormMessages.COMPLETED_MILESTONE_ONE)
                expect(page).to_have_url(ContactSupportMessages.PAGE_URL_CHANGE_PRODUCT_REDIRECT)


# T5696600
@pytest.mark.aaqPage
def test_aaq_form_cancel_button_freemium_products(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory()

    with allure.step("Signing in with a simple user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to each product AAQ form"):
        for product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            with allure.step("Adding data inside the AAQ form fields and clicking on the "
                             "cancel button"):
                sumo_pages.aaq_flow.add__valid_data_to_all_aaq_fields_without_submitting(
                    subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
                    topic_value=sumo_pages.aaq_form_page.get_aaq_form_topic_options()[0],
                    body_text=utilities.aaq_question_test_data["valid_firefox_question"]
                    ["question_body"]
                )
                sumo_pages.aaq_form_page.click_aaq_form_cancel_button()

            with allure.step("Verifying that we are redirected back to the correct product "
                             "solutions page"):
                expect(page).to_have_url(utilities.general_test_data["product_solutions"][product])

            with check, allure.step("Navigating back to the My Profile page and verifying "
                                    "that the correct number of posted questions is displayed"):
                sumo_pages.top_navbar.click_on_view_profile_option()
                expect(sumo_pages.my_profile_page.questions_link).to_be_hidden()


# T5696597, T5696601, T5696602
@pytest.mark.aaqPage
def test_post_aaq_questions_for_all_freemium_products_topics(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Signing in with a Forum Moderator account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to each product AAQ form"):
        for product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            for topic in sumo_pages.aaq_form_page.get_aaq_form_topic_options():
                with allure.step(f"Submitting question for {product} product"):
                    question_info = sumo_pages.aaq_flow.submit_an_aaq_question(
                        subject=f"Issue related to the {topic} topic",
                        topic_name=topic,
                        body=f"I have a problem related to {topic}. But I don't know how to "
                             f"explain it properly. I need some guidance in debugging this so "
                             f"that I can provide more information.",
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
                    expect(sumo_pages.my_questions_page.question_by_name(
                        question_info['aaq_subject'])).to_be_visible()

                with allure.step(f"Navigating back to the {product} product aa form"):
                    utilities.navigate_to_link(
                        utilities.aaq_question_test_data["products_aaq_url"][product])


# T5696633
@pytest.mark.aaqPage
def test_share_firefox_data_functionality(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Signing in with a Forum Moderator account"):
        utilities.start_existing_session(cookies=test_user)

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
            body_text=utilities.aaq_question_test_data["valid_firefox_question"]["question_body"]
        )

    with allure.step("Adding text inside the troubleshooting information field and "
                     "submitting the AAQ question"):
        sumo_pages.aaq_form_page.add_text_to_troubleshooting_information_textarea(
            utilities.aaq_question_test_data["troubleshooting_information"]
        )
        with utilities.page.expect_navigation():
            retry_on_502(
                sumo_pages.aaq_form_page.click_aaq_form_submit_button(
                expected_locator=sumo_pages.question_page.questions_header)
            )

    with allure.step("Verifying that the troubleshooting information is displayed"):
        sumo_pages.question_page.click_on_question_details_button()
        sumo_pages.question_page.click_on_more_system_details_option()
        expect(sumo_pages.question_page.more_information_with_text(
            utilities.aaq_question_test_data["troubleshooting_information"])).to_be_visible()

    with allure.step("Closing the additional details panel and verifying that the panel is no "
                     "longer displayed"):
        sumo_pages.question_page.click_on_the_additional_system_panel_close()
        expect(sumo_pages.question_page.more_system_details_modal).to_be_hidden()


@pytest.mark.aaqPage
def test_additional_system_details_user_agent_information(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Signing in with a Forum Moderator user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Navigating to each product aaq form"):
        for product in utilities.general_test_data["freemium_products"]:
            utilities.navigate_to_link(
                utilities.aaq_question_test_data["products_aaq_url"][product])

            with allure.step(f"Submitting a question for the {product} product"):
                sumo_pages.aaq_flow.submit_an_aaq_question(
                    subject=utilities.aaq_question_test_data["valid_firefox_question"]["subject"],
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


@pytest.mark.aaqPage
def test_system_details_information(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    troubleshooting_info = [
        utilities.aaq_question_test_data["troubleshoot_product_and_os_versions"][0],
        "Firefox " + utilities.aaq_question_test_data["troubleshoot_product_and_os_versions"][1]
    ]
    test_user = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Signing in with a Forum Moderator user account"):
        utilities.start_existing_session(cookies=test_user)

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
                        utilities.aaq_question_test_data["troubleshoot_product_and_os_versions"][1]
                    )
                    sumo_pages.aaq_form_page.add_text_to_os_field(
                        utilities.aaq_question_test_data["troubleshoot_product_and_os_versions"][0]
                    )

                with check, allure.step("Submitting the AAQ question and verifying that the "
                                        "correct provided troubleshooting information is "
                                        "displayed"):
                    with utilities.page.expect_navigation():
                        retry_on_502(
                            sumo_pages.aaq_form_page.click_aaq_form_submit_button(
                            expected_locator=sumo_pages.question_page.questions_header
                            )
                        )

                    sumo_pages.question_page.click_on_question_details_button()
                    assert sumo_pages.question_page.get_system_details_information(
                    ) == troubleshooting_info


# T5696704
@pytest.mark.aaqPage
def test_premium_products_aaq(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    aaq_form_messages = AAQFormMessages()

    with allure.step("Signing in with a Forum Moderator account"):
        utilities.start_existing_session(
            session_file_name=utilities.username_extraction_from_email(utilities.staff_user))

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
                    is_premium=True,
                    expected_locator= sumo_pages.aaq_form_page.premium_ticket_message,
                    form_url=premium_form_link
                )
            else:
                sumo_pages.aaq_flow.submit_an_aaq_question(
                    subject=utilities.aaq_question_test_data['premium_aaq_question']['subject'],
                    body=utilities.aaq_question_test_data['premium_aaq_question']['body'],
                    is_premium=True,
                    expected_locator=sumo_pages.aaq_form_page.premium_ticket_message,
                    form_url=premium_form_link
                )
                if utilities.get_page_url() == premium_form_link:
                    with utilities.page.expect_navigation():
                        retry_on_502(
                            sumo_pages.aaq_form_page.click_aaq_form_submit_button(with_force=True,
                            expected_locator=sumo_pages.question_page.questions_header)
                        )

        with allure.step("Verifying that the correct success message is displayed"):
            assert sumo_pages.aaq_form_page.get_premium_card_submission_message(
            ) == aaq_form_messages.get_premium_ticket_submission_success_message(
                utilities.staff_user)


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
            # In case a 502 error occurs we might end up in the auth page after the automatic
            # refresh/retry so we need to skip the signin_signup button click since the
            # element is not available.
            sumo_pages.aaq_flow.submit_an_aaq_question(
                subject=utilities.aaq_question_test_data['premium_aaq_question']['subject'],
                body=utilities.aaq_question_test_data['premium_aaq_question']['body'],
                is_premium=True,
                email=utilities.staff_user,
                is_loginless=True,
                expected_locator= sumo_pages.aaq_form_page.premium_ticket_message
            )
            if i <= 3:
                with allure.step("Verifying that the correct success message is displayed"):
                    assert sumo_pages.aaq_form_page.get_premium_card_submission_message(
                    ) == aaq_form_messages.get_premium_ticket_submission_success_message(
                        utilities.staff_user
                    )
            else:
                with allure.step("Verifying that submission error message is displayed"):
                    assert sumo_pages.aaq_form_page.get_premium_card_submission_message(
                    ) == aaq_form_messages.LOGINLESS_RATELIMIT_REACHED_MESSAGE
            i += 1
