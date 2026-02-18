import allure
import pytest
from playwright.sync_api import Page, expect
from pytest_check import check
from playwright_tests.core.utilities import Utilities
from playwright_tests.messages.contribute_messages.con_tools.kb_dashboard_messages import (
    KBDashboardPageMessages,
)
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
        assert sumo_pages.kb_dashboard_page.get_a_particular_article_status(
            article_details['article_title']
        ).strip() == KBDashboardPageMessages.get_kb_not_live_status(
            revision_note=article_details['article_review_description']
        )

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
        expect(
            sumo_pages.kb_dashboard_page.article_title(
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
        assert sumo_pages.kb_dashboard_page.get_a_particular_article_status(
            article_details['article_title']).strip() == KBDashboardPageMessages.KB_LIVE_STATUS

    with allure.step("Signing out and verifying that the article is visible"):
        utilities.delete_cookies()
        expect(
            sumo_pages.kb_dashboard_page.article_title(
                article_details['article_title'])).to_be_visible()

    with allure.step("Signing in with a non-admin user"):
        sumo_pages.top_navbar.click_on_sumo_nav_logo()
        utilities.start_existing_session(cookies=test_user_two)

    with allure.step("Navigating to the kb overview and verifying that the article is "
                     "visible"):
        utilities.navigate_to_link(
            utilities.general_test_data['dashboard_links']['kb_overview'])
        expect(
            sumo_pages.kb_dashboard_page.article_title(
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
        assert sumo_pages.kb_dashboard_page.get_a_particular_article_status(
            article_details['article_title']
        ).strip() == KBDashboardPageMessages.get_kb_not_live_status(
            revision_note=second_revision['changes_description']
        )

    with allure.step("Navigating back to the article history and deleting the revision"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.kb_article_show_history_page.click_on_delete_revision_button(
            second_revision['revision_id']
        )
        sumo_pages.kb_article_show_history_page.click_on_confirmation_delete_button()

    with check, allure.step("Navigating back to the kb dashboard and verifying that the live "
                            "status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_a_particular_article_status(
            article_details['article_title']).strip() == KBDashboardPageMessages.KB_LIVE_STATUS


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
        assert sumo_pages.kb_dashboard_page.get_a_particular_article_status(
            article_details['article_title']
        ) == KBDashboardPageMessages.get_kb_not_live_status(
            second_revision['changes_description'])

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
        assert sumo_pages.kb_dashboard_page.get_a_particular_article_status(
            article_details['article_title']) == KBDashboardPageMessages.KB_LIVE_STATUS


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
        assert sumo_pages.kb_dashboard_page.get_needs_update_status(
            article_details['article_title']
        ).strip() == utilities.kb_revision_test_data['needs_change_message']


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
        assert sumo_pages.kb_dashboard_page.get_needs_update_status(
            article_details['article_title']
        ).strip() == utilities.kb_revision_test_data['needs_change_message']

    with allure.step("Navigating back to the article's 'Edit Article Metadata' page and "
                     "removing the comment from the needs change textarea"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata(needs_change=True)

    with allure.step("Navigating to the complete dashboard list and verifying that the "
                     "correct needs change status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_needs_update_status(
            article_details['article_title']
        ).strip() == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS

    with allure.step("Navigating back to the article's 'Edit Article Metadata' page and "
                     "removing the needs change updates"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.edit_article_metadata_flow.edit_article_metadata()

    with check, allure.step("Navigating to the kb overview page and verifying that the "
                            "correct needs change status is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.is_needs_change_empty(article_details['article_title'])


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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS


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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS


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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

    with check, allure.step("Approving the KB article without marking it as ready for l10n and "
                            "verifying that the correct l10N status is displayed inside the KB "
                            "dashboard (No)"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.approve_kb_revision(
            revision_id=article_details["first_revision_id"])
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

    with allure.step("Creating a new revision and approve it as minor significance"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='minor')

    with check, allure.step("Verifying that the correct l10N status is inside the KB dashboard "
                            "(No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

    with allure.step("Creating a new revision and approving it as normal significance and ready "
                     "for localization"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='normal', ready_for_l10n=True
        )

    with check, allure.step("Verifying that the correct l10n status is inside the kb dashboard "
                            "(Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS

    with allure.step("Creating a new revision and approving it as normal significance and not "
                     "ready for localization"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='normal'
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

    with allure.step("Creating a new minor revision and approving it"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='minor'
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

    with allure.step("Creating a new major revision and not marking it as ready for localization"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='major'
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

    with allure.step("Creating a new minor revision and approving it"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='minor'
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

    with allure.step("Creating a new major revision and marking it as ready for localization"):
        utilities.navigate_to_link(article_details["article_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='major', ready_for_l10n=True
        )

    with check, allure.step("Verifying that the correct l10n status is displayed inside the kb "
                            "dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS


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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS

    with allure.step("Creating a new minor revision"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='minor'
        )

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS

    with allure.step("Creating a new major significance revision"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        third_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='major'
        )

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (No)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS


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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS

    with allure.step("Creating a new revision of normal significance and approving it by marking"
                     "it as ready for localization"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            approve_revision=True, significance_type='major', ready_for_l10n=True
        )

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS

    with allure.step("Creating a new revision and deferring it instead of approving"):
        utilities.navigate_to_link(article_details["article_show_history_url"])
        fourth_revision = sumo_pages.submit_kb_article_flow.submit_new_kb_revision()
        sumo_pages.submit_kb_article_flow.defer_revision(fourth_revision['revision_id'])

    with check, allure.step("Verifying that the correct ready for localization status is displayed"
                            " inside the KB dashboard (Yes)"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS


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
        assert sumo_pages.kb_dashboard_page.get_ready_for_l10n_status(
            article_details['article_title']) == KBDashboardPageMessages.GENERAL_NEGATIVE_STATUS


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
        assert sumo_pages.kb_dashboard_page.get_stale_status(
            article_details['article_title']
        ) == KBDashboardPageMessages.GENERAL_POSITIVE_STATUS
        assert sumo_pages.kb_dashboard_page.get_existing_expiry_date(
            article_details['article_title']
        ) == utilities.convert_string_to_datetime(
            utilities.kb_article_test_data['old_expiry_date']
        )

    with allure.step("Navigating back to the article and creating a new revision with a "
                     "non-stale expiry date"):
        utilities.navigate_to_link(article_url)
        sumo_pages.submit_kb_article_flow.submit_new_kb_revision(
            expiry_date=utilities.kb_article_test_data['expiry_date'], approve_revision=True
        )

    with check, allure.step("Navigating to the kb dashboard and verifying that the correct "
                            "stale status and date is displayed"):
        utilities.navigate_to_link(utilities.general_test_data['dashboard_links']['kb_overview'])
        assert sumo_pages.kb_dashboard_page.is_stale_status_empty(article_details['article_title'])
        assert sumo_pages.kb_dashboard_page.get_existing_expiry_date(
            article_details['article_title']
        ) == utilities.convert_string_to_datetime(utilities.kb_article_test_data['expiry_date'])


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
        expect(
            sumo_pages.kb_dashboard_page.article_title(
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
