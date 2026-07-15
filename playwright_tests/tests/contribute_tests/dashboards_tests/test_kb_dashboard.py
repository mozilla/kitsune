import random

import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.common_elements_messages import CommonElementsMessages
from playwright_tests.messages.contribute_messages.con_tools.kb_dashboard_messages import (
    KBDashboardPageMessages,
)
from playwright_tests.messages.contribute_messages.con_tools.moderate_forum_messages import (
    ModerateForumContentPageMessages,
)
from playwright_tests.messages.homepage_messages import HomepageMessages
from playwright_tests.pages.sumo_pages import SumoPages


# C891357
@pytest.mark.kbDashboard
def test_unreviewed_articles_visibility_in_kb_dashboard(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["forum-contributors"])
    test_user_two = create_user_factory(groups=["forum-contributors"])
    test_user_three = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a simple user account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Create a new simple article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

    with allure.step("Navigating to the kb dashboards and clicking on the 'Complete "
                     "overview' option"):
        sumo_pages.top_navbar.click_on_dashboards_option()
        sumo_pages.kb_dashboard_page.click_on_the_complete_overview_link()

    with allure.step("Verifying that we are redirected to the correct page"):
        expect(page).to_have_url(utilities.general_test_data['dashboard_links']['kb_overview'])

    with check, allure.step("Verifying that the correct live status is displayed"):
        expect(sumo_pages.kb_dashboard_page.article_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.get_kb_not_live_status(
            revision_note=article_details['article_review_description']))

    with allure.step("Signing out and verifying that the article is not displayed since it "
                     "is not live yet"):
        utilities.delete_cookies()
        expect(sumo_pages.kb_dashboard_page.article_title(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Navigating to the homepage and performing the sign in step since the "
                     "kb overview takes quite a bit to refresh/load"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating to the kb overview verifying that the article is not "
                     "displayed since it is not live yet"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_title(
            article_details['article_title'])).to_be_hidden()

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        utilities.start_existing_session(cookies=test_user_three)

    with allure.step("Navigating to the kb overview page and clicking on the article title"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        sumo_pages.kb_dashboard_page.click_on_article_title(article_details['article_title'])

    with allure.step("Verifying that the user is redirected to the correct kb page"):
        expect(page).to_have_url(article_details['article_url'])

    with allure.step("Approving the article revision"):
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=article_details['first_revision_id'])

    with check, allure.step("Navigating back to the kb overview page and verifying that the "
                            "correct live status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.KB_LIVE_STATUS)

    with allure.step("Signing out and verifying that the article is visible"):
        utilities.delete_cookies()
        expect(sumo_pages.kb_dashboard_page.article_title(
            article_details['article_title'])).to_be_visible()

    with allure.step("Signing in with a non-admin user"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating to the kb overview and verifying that the article is "
                     "visible"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_title(
            article_details['article_title'])).to_be_visible()


# C2266376
@pytest.mark.kbDashboard
def test_kb_dashboard_articles_status(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new simple article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    with allure.step("Creating a new revision for the document"):
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with check, allure.step("Navigating to the kb overview dashboard and verifying that the "
                            "correct status is displayed"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['kb_overview'])

        expect(sumo_pages.kb_dashboard_page.article_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.get_kb_not_live_status(
            revision_note=second_revision['changes_description']))

    with allure.step("Navigating back to the article history and deleting the revision"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.kb_article_show_history_page.click_on_delete_revision_button(
            second_revision['revision_id']
        )
        sumo_pages.kb_article_show_history_page.click_on_confirmation_delete_button()

    with check, allure.step("Navigating back to the kb dashboard and verifying that the live "
                            "status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.KB_LIVE_STATUS)


# C2496647
@pytest.mark.kbDashboard
def test_kb_dashboard_revision_deferred_status(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new simple article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    article_show_history_url = utilities.get_page_url()

    with allure.step("Creating a new revision for the document"):
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()

    with check, allure.step("Navigating to the kb overview page and verifying that the "
                            "correct kb status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.get_kb_not_live_status(
            second_revision['changes_description']))

    with allure.step("Navigating back to the article history page and deferring the revision"):
        utilities.navigate_to_link(article_show_history_url)
        sumo_pages.kb_article_show_history_page.click_on_review_revision(
            second_revision['revision_id']
        )
        sumo_pages.kb_article_review_revision_page.click_on_defer_revision_button()
        sumo_pages.kb_article_review_revision_page.click_on_defer_confirm_button()

    with check, allure.step("Navigating back to the kb overview page and verifying that the "
                            "correct status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.KB_LIVE_STATUS)


# C2496646
@pytest.mark.kbDashboard
def test_kb_dashboard_needs_update_when_reviewing_a_revision(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewers account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new simple article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    with allure.step("Creating a new article revision for the document"):
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=second_revision['revision_id'], revision_needs_change=True
        )

    with check, allure.step("Navigating to the kb dashboard overview page and verifying that "
                            "the correct article status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.needs_update_status(article_details['article_title'])
               ).to_have_text(utilities.kb_revision_test_data['needs_change_message'])

# C2266377, C2243456, C2496646
@pytest.mark.kbDashboard
def test_kb_dashboard_needs_update_edit_metadata(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Create a new simple article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    with allure.step("Clicking on the 'Edit Article Metadata' option and enabling the 'Needs "
                     "change with comment' option"):
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(
            needs_change=True, needs_change_comment=True
        )

    with check, allure.step("Navigating to the kb dashboard and verifying that the correct "
                            "needs change status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.needs_update_status(article_details['article_title'])
               ).to_have_text(utilities.kb_revision_test_data['needs_change_message'])

    with allure.step("Navigating back to the article's 'Edit Article Metadata' page and "
                     "removing the comment from the needs change textarea"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(needs_change=True)

    with allure.step("Navigating to the complete dashboard list and verifying that the "
                     "correct needs change status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.needs_update_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)

    with allure.step("Navigating back to the article's 'Edit Article Metadata' page and "
                     "removing the needs change updates"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata()

    with check, allure.step("Navigating to the kb overview page and verifying that the "
                            "correct needs change status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.needs_update_status(article_details['article_title'])
               ).to_be_empty()


# C2266378, C2489548
@pytest.mark.smokeTest
@pytest.mark.kbDashboard
def test_ready_for_l10n_kb_dashboard_revision_approval(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Create a new simple article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article()

    revision_id = article_details['first_revision_id']

    with allure.step("Approving the first revision and marking it as ready for l10n"):
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=revision_id, ready_for_l10n=True)

    with check, allure.step("Navigating to the kb dashboard overview page and verifying that "
                            "the correct l10n status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)


# C2266378
@pytest.mark.smokeTest
@pytest.mark.kbDashboard
def test_ready_for_l10n_kb_dashboard_revision_l10n_status(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new kb article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    with check, allure.step("Navigating to the kb dashboard overview page and verifying that "
                            "the correct l10n status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Navigating back to the article page and marking the revision as ready "
                     "for l10n"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.kb_article_show_history_page.click_on_ready_for_l10n_option(
            article_details['first_revision_id']
        )
        sumo_pages.kb_article_show_history_page.click_on_submit_l10n_readiness_button(
            article_details['first_revision_id'])

    with allure.step("Navigating to the kb dashboard overview page and verifying that the "
                     "correct l10n status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)


# C2875533
@pytest.mark.smokeTest
@pytest.mark.kbDashboard
def test_ready_for_l10n_kb_dashboard_status_update(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new kb article and approving the first revision without marking "
                     "it as ready for l10n"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=False)

    with check, allure.step("Verifying that the correct kb dashboard l10n status is displayed "
                            "(No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with check, allure.step("Approving the KB article without marking it as ready for l10n and "
                            "verifying that the correct l10N status is displayed inside the KB "
                            "dashboard (No)"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=article_details["first_revision_id"])
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Creating a new revision and approve it as minor significance"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='minor')

    with check, allure.step("Verifying that the correct l10N status is inside the KB dashboard "
                            "(No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Creating a new revision and approving it as normal significance and ready "
                     "for localization"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='normal', ready_for_l10n=True
        )

    with check, allure.step("Verifying that the correct l10n status is inside the kb dashboard "
                            "(Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)

    with allure.step("Creating a new revision and approving it as normal significance and not "
                     "ready for localization"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='normal'
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Creating a new minor revision and approving it"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='minor'
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Creating a new major revision and not marking it as ready for localization"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='major'
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Creating a new minor revision and approving it"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='minor'
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Creating a new major revision and marking it as ready for localization"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='major', ready_for_l10n=True
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)


# C2875537
@pytest.mark.smokeTest
@pytest.mark.kbDashboard
def test_ready_for_l10n_status_update_via_history_page(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new kb article and approving the first revision without marking "
                     "it as ready for l10n"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    with allure.step("Creating a new revision and approving it as Normal significance and not"
                     "ready for localization"):
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='normal'
        )

    with check, allure.step("Verifying that the correct ready for localization status is "
                            "displayed inside the KB dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Marking the newly submitted revision as ready for localization via the"
                     " /history page"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.kb_article_show_history_page.click_on_ready_for_l10n_option(
            second_revision["revision_id"])
        sumo_pages.kb_article_show_history_page.click_on_submit_l10n_readiness_button(
            second_revision["revision_id"])

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            "inside the KB dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)

    with allure.step("Creating a new minor revision"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='minor'
        )

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)

    with allure.step("Creating a new major significance revision"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        third_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='major'
        )

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Marking the newly submitted revision as ready for localization via the"
                     " /history page"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.kb_article_show_history_page.click_on_ready_for_l10n_option(
            third_revision["revision_id"])
        sumo_pages.kb_article_show_history_page.click_on_submit_l10n_readiness_button(
            third_revision["revision_id"])

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)


# C2875536
@pytest.mark.kbDashboard
def test_deferring_revision_does_not_impact_l10n_kb_dashboard_status(page: Page,
                                                                     create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new kb article and approving the first revision without marking "
                     "it as ready for l10n"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    with allure.step("Creating a new kb article revision and deferring it instead of approving"):
        second_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()
        sumo_pages.submit_kb_article_flow.defer_revision(second_revision['revision_id'])

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)

    with allure.step("Creating a new revision of normal significance and approving it by marking"
                     "it as ready for localization"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='major', ready_for_l10n=True
        )

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)

    with allure.step("Creating a new revision and deferring it instead of approving"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        fourth_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()
        sumo_pages.submit_kb_article_flow.defer_revision(fourth_revision['revision_id'])

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)


# C2266378
@pytest.mark.kbDashboard
def test_article_translation_not_allowed_kb_dashboard(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new simple article & unchecking the allow translations"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            allow_translations=False, approve_first_revision=True
        )

    with allure.step("Navigating to the kb dashboard overview page and verifying that the "
                     "correct l10n status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.ready_for_l10n_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS)


# C2266379, C2266380
@pytest.mark.kbDashboard
def test_article_stale_kb_dashboard(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)

    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Create a new simple article & adding an old expiry date"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            expiry_date=utilities.kb_article_test_data['old_expiry_date'],
            approve_first_revision=True
        )

    article_url = utilities.get_page_url()

    with check, allure.step("Navigating to the kb dashboard overview page and verifying that "
                            "the correct stale status and date is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.stale_status(article_details['article_title'])
               ).to_have_text(KBDashboardPageMessages.GENERAL_POSITIVE_STATUS)
        expect(sumo_pages.kb_dashboard_page.expiry_date(article_details['article_title'])
               ).to_have_text(utilities.convert_string_to_datetime(
            utilities.kb_article_test_data['old_expiry_date']))

    with allure.step("Navigating back to the article and creating a new revision with a "
                     "non-stale expiry date"):
        utilities.navigate_to_link(article_url)
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            expiry_date=utilities.kb_article_test_data['expiry_date'], approve_revision=True
        )

    with check, allure.step("Navigating to the kb dashboard and verifying that the correct "
                            "stale status and date is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.stale_status(article_details['article_title'])
               ).to_be_empty()
        expect(sumo_pages.kb_dashboard_page.expiry_date(article_details['article_title'])
               ).to_have_text(utilities.convert_string_to_datetime(
            utilities.kb_article_test_data['expiry_date']))


@pytest.mark.kbDashboard
def test_article_title_update(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    test_user = create_user_factory(groups=["Knowledge Base Reviewers"])

    with allure.step("Signing in with a Knowledge Base Reviewer account"):
        utilities.start_existing_session(cookies=test_user)

    with allure.step("Creating a new kb article"):
        article_details = sumo_pages.submit_kb_article_flow.submit_simple_kb_article(
            approve_first_revision=True)

    with allure.step("Navigating to the kb dashboard overview page and verifying that the "
                     "correct title is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_title(
            article_details['article_title'])).to_be_visible()

    with allure.step("Navigating to the article's 'Edit Metadata page' page and changing the "
                     "title"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        new_article_title = "Updated " + article_details['article_title']
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(title=new_article_title)

    with allure.step("Navigating back to the kb dashboard page and verifying that the "
                     "correct title is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(sumo_pages.kb_dashboard_page.article_title(new_article_title)).to_be_visible()


# C891350, C891351, C954936
@pytest.mark.kbDashboard
def test_kb_dashboard_can_be_filtered_by_each_product(page: Page):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_overview_link = utilities.general_test_data['dashboard_links']['kb_overview']

    with allure.step("Signing in with a staff account"):
        utilities.start_existing_session(
            session_file_name=utilities.username_extraction_from_email(utilities.staff_user))

    with allure.step("Navigating to the kb overview dashboard and fetching the list of products "
                     "available in the filter dropdown"):
        utilities.navigate_to_link(kb_overview_link)
        product_options = sumo_pages.kb_dashboard_page.get_product_filter_options()
        assert product_options, "No products were found inside the kb dashboard filter dropdown"

    for product in product_options:
        with allure.step(f"Filtering the kb dashboard by the '{product['label']}' product"):
            utilities.navigate_to_link(kb_overview_link)
            sumo_pages.kb_dashboard_page.filter_by_product(product['value'])
            page.wait_for_url(
                lambda url: f"product={product['value']}" in url, timeout=10000)

        articles_count = sumo_pages.kb_dashboard_page.get_number_of_listed_articles()
        if articles_count == 0:
            print(f"No articles are listed for the '{product['label']}' product. Skipping.")
            continue

        with allure.step(f"Clicking on a random listed article for the '{product['label']}' "
                         f"product"):
            random_index = random.randint(0, articles_count - 1)
            article_title = sumo_pages.kb_dashboard_page.get_listed_article_title(random_index)
            sumo_pages.kb_dashboard_page.click_on_listed_article(random_index)

        with check, allure.step(f"Verifying that the '{article_title}' article belongs to the "
                                f"'{product['label']}' product"):
            article_products = sumo_pages.kb_article_page.get_article_products_metadata()
            assert product['label'] in article_products, (
                f"The '{article_title}' article was listed under the '{product['label']}' product "
                f"filter but its metadata only lists the following products: {article_products}")

    with allure.step("Fetching the list of types available in the kb dashboard filter dropdown"):
        utilities.navigate_to_link(kb_overview_link)
        type_options = sumo_pages.kb_dashboard_page.get_type_filter_options()
        assert type_options, "No types were found inside the kb dashboard type filter dropdown"

    for kb_type in type_options:
        with allure.step(f"Filtering the kb dashboard by the '{kb_type['label']}' type"):
            utilities.navigate_to_link(kb_overview_link)
            sumo_pages.kb_dashboard_page.select_type_filter(kb_type['value'])
            page.wait_for_url(
                lambda url, value=kb_type['value']: f"category={value}" in url, timeout=10000)

        articles_count = sumo_pages.kb_dashboard_page.get_number_of_listed_articles()
        if articles_count == 0:
            print(f"No articles are listed for the '{kb_type['label']}' type. Skipping.")
            continue

        with allure.step(f"Opening the edit metadata page of a random listed article for the "
                         f"'{kb_type['label']}' type"):
            random_index = random.randint(0, articles_count - 1)
            article_title = sumo_pages.kb_dashboard_page.get_listed_article_title(random_index)
            sumo_pages.kb_dashboard_page.click_on_listed_article(random_index)
            utilities.navigate_to_link(
                sumo_pages.kb_article_page.get_url().rstrip("/") + "/edit/metadata")
            if sumo_pages.kb_edit_article_page.is_edit_anyway_option_visible():
                sumo_pages.kb_edit_article_page.click_on_edit_anyway_option()

        with check, allure.step(f"Verifying that the '{article_title}' article is of the "
                                f"'{kb_type['label']}' type"):
            selected_category = (
                sumo_pages.kb_article_edit_article_metadata_page.get_selected_category_value())
            assert selected_category == kb_type['value'], (
                f"The '{article_title}' article was listed under the '{kb_type['label']}' type "
                f"filter but its metadata category value is '{selected_category}' instead of the "
                f"expected '{kb_type['value']}'")


# C2597852
@pytest.mark.kbDashboard
def test_kb_dashboard_contributor_tools_sidebar(page: Page, create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    common = sumo_pages.common_web_elements
    kb_dashboard_url = HomepageMessages.STAGE_HOMEPAGE_URL_EN_US + "contributors"

    sidebar_options = [
        (ModerateForumContentPageMessages.SIDEBAR_OPTION_NAME, "/flagged", False),
        ("Knowledge base dashboards", "/contributors", False),
        ("Guides", "/contributor", False),
        ("Templates", "/kb/category/60", False),
        ("Media gallery", "/gallery/images", False),
        ("Recent revisions", "/kb/revisions", False),
        ("Community hub", "/community", False),
        ("Locales", "/kb/locales", True),
        ("Locale metrics", "/kb/dashboard/metrics/en-US", True),
        ("Aggregated metrics", "/kb/dashboard/metrics/aggregated", True),
    ]

    with allure.step("Creating a simple user and a forum moderator account"):
        simple_user = create_user_factory()
        forum_moderator = create_user_factory(groups=["Forum Moderators"])

    with allure.step("Signing in with the simple user account and navigating to the KB "
                     "dashboard"):
        utilities.start_existing_session(cookies=simple_user)
        utilities.navigate_to_link(kb_dashboard_url)

    with check, allure.step("Verifying that the 'Contributor tools' sidebar and heading are "
                            "displayed"):
        expect(common.contributor_tools_side_navbar).to_be_visible()
        expect(common.contributor_tools_side_navbar_heading).to_have_text(
            CommonElementsMessages.CONTRIBUTOR_TOOLS_SIDEBAR_HEADING)

    with check, allure.step("Verifying that the 'Moderate forum content' option is not displayed "
                            "for a user without the moderation permission"):
        expect(common.contributor_tools_side_navbar_option(
            ModerateForumContentPageMessages.SIDEBAR_OPTION_NAME)).to_be_hidden()

    with allure.step("Signing in with the forum moderator account and navigating to the KB "
                     "dashboard"):
        utilities.start_existing_session(cookies=forum_moderator)
        utilities.navigate_to_link(kb_dashboard_url)

    with check, allure.step("Verifying that the 'Moderate forum content' option is displayed for "
                            "a user with the moderation permission"):
        expect(common.contributor_tools_side_navbar_option(
            ModerateForumContentPageMessages.SIDEBAR_OPTION_NAME)).to_be_visible()

    for option_name, url_fragment, behind_show_more in sidebar_options:
        with allure.step(f"Clicking on the '{option_name}' contributor tools sidebar option"):
            utilities.navigate_to_link(kb_dashboard_url)
            if behind_show_more:
                common.click_on_contributor_tools_side_navbar_show_more_button()
            common.click_on_a_contributor_tools_side_navbar_option(option_name)
            utilities.wait_for_page_to_load()

        with check, allure.step(f"Verifying that the '{option_name}' option redirects to the "
                                f"correct page"):
            assert url_fragment in utilities.get_page_url(), (
                f"The '{option_name}' sidebar option redirected to "
                f"'{utilities.get_page_url()}' which does not contain '{url_fragment}'")


# C2266227
@pytest.mark.kbDashboard
def test_kb_dashboard_subscribe_button_not_available_for_logged_out_users(page: Page,
                                                                          create_user_factory):
    utilities = Utilities(page)
    sumo_pages = SumoPages(page)
    kb_dashboard_url = HomepageMessages.STAGE_HOMEPAGE_URL_EN_US + "contributors"

    with allure.step("Signing in with a simple user account and navigating to the KB dashboard"):
        test_user = create_user_factory()
        utilities.start_existing_session(cookies=test_user)
        utilities.navigate_to_link(kb_dashboard_url)

    with allure.step("Verifying that the 'Subscribe' button is available for logged in users"):
        expect(sumo_pages.kb_dashboard_page.subscribe_button).to_be_visible()

    with allure.step("Signing out and navigating back to the KB dashboard"):
        utilities.delete_cookies()
        utilities.navigate_to_link(kb_dashboard_url)

    with allure.step("Verifying that the 'Subscribe' button is not available for logged out "
                     "users"):
        expect(sumo_pages.kb_dashboard_page.subscribe_button).to_be_hidden()
